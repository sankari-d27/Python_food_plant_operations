
import json

import pytest

from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db

from app.models import (
    User,
    Product,
    ProductionLine,
    Batch,
    Production,
    AuditLog
)

from app.routers.production import router as production_router

import app.services.production_service as production_service_module


# --------------------------------------------------
# TEST DATABASE FIXTURE
# --------------------------------------------------

@pytest.fixture
def test_environment(tmp_path):

    test_database = tmp_path / "test_production.db"

    test_engine = create_engine(
        f"sqlite:///{test_database}",
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(connection, record):

        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():

        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    test_app = FastAPI()
    test_app.include_router(production_router)

    test_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(test_app)

    # CREATE REQUIRED REFERENCE RECORDS
    with TestingSessionLocal() as db:

        user = User(
            username="production_test_user",
            email="production_test@example.com",
            password_hash="test_hash",
            role="production",
            is_active=True
        )

        product = Product(
            product_code="PROD-TEST-001",
            product_name="Production Test Product",
            description="Production testing product",
            unit="kg",
            is_active=True
        )

        line = ProductionLine(
            line_code="LINE-PROD-001",
            line_name="Production Testing Line",
            description="Production testing line",
            is_active=True
        )

        db.add_all([user, product, line])
        db.commit()

        db.refresh(user)
        db.refresh(product)
        db.refresh(line)

        batch = Batch(
            batch_number="BATCH-PROD-TEST-001",
            product_id=product.id,
            production_line_id=line.id,
            created_by=user.id,
            production_date=date.today(),
            input_quantity=100.0,
            output_quantity=95.0,
            status="draft"
        )

        db.add(batch)
        db.commit()
        db.refresh(batch)

        reference_ids = {
            "user_id": user.id,
            "product_id": product.id,
            "production_line_id": line.id,
            "batch_id": batch.id
        }

    yield client, TestingSessionLocal, reference_ids

    client.close()
    test_app.dependency_overrides.clear()
    test_engine.dispose()


# --------------------------------------------------
# PRODUCTION TEST DATA
# --------------------------------------------------

def production_payload(reference_ids):

    return {
        "batch_id": reference_ids["batch_id"],
        "production_date": date.today().isoformat(),
        "input_quantity": 100.0,
        "output_quantity": 90.0,
        "wastage_quantity": 5.0,
        "shift": "Morning"
    }


def create_test_production(db, batch_id):

    production = Production(
        batch_id=batch_id,
        production_date=date.today(),
        input_quantity=100.0,
        output_quantity=90.0,
        wastage_quantity=5.0,
        shift="Morning"
    )

    db.add(production)
    db.commit()
    db.refresh(production)

    return production


# --------------------------------------------------
# TEST 1: COMPLETE CRUD AND AUDIT
# --------------------------------------------------

def test_production_crud_and_audit(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)

    # CREATE
    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 200

    production = response.json()
    production_id = production["id"]

    assert production["batch_id"] == reference_ids["batch_id"]
    assert production["input_quantity"] == 100.0
    assert production["output_quantity"] == 90.0

    # VERIFY CREATE AUDIT
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Production",
            AuditLog.entity_id == production_id,
            AuditLog.action == "CREATE"
        ).first()

        assert audit is not None

        new_value = json.loads(audit.new_value)

        assert new_value["input_quantity"] == 100.0
        assert new_value["output_quantity"] == 90.0

    # GET ALL
    response = client.get("/production/")

    assert response.status_code == 200

    assert any(
        item["id"] == production_id
        for item in response.json()
    )

    # GET BY ID
    response = client.get(
        f"/production/{production_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == production_id

    # UPDATE
    response = client.put(
        f"/production/{production_id}",
        json={
            "output_quantity": 92.0,
            "wastage_quantity": 4.0
        }
    )

    assert response.status_code == 200
    assert response.json()["output_quantity"] == 92.0

    # VERIFY UPDATE AUDIT
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Production",
            AuditLog.entity_id == production_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is not None

        old_value = json.loads(audit.old_value)
        new_value = json.loads(audit.new_value)

        assert old_value["output_quantity"] == 90.0
        assert new_value["output_quantity"] == 92.0

    # DELETE
    response = client.delete(
        f"/production/{production_id}"
    )

    assert response.status_code == 200

    # VERIFY DELETE AND AUDIT
    with SessionLocal() as db:

        deleted_record = db.query(Production).filter(
            Production.id == production_id
        ).first()

        assert deleted_record is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Production",
            AuditLog.entity_id == production_id,
            AuditLog.action == "DELETE"
        ).first()

        assert audit is not None
        assert audit.new_value is None

        old_value = json.loads(audit.old_value)

        assert old_value["output_quantity"] == 92.0


# --------------------------------------------------
# TEST 2: INVALID BATCH REFERENCE
# --------------------------------------------------

def test_invalid_batch_reference(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)
    data["batch_id"] = 999999

    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Batch does not exist"
    )


# --------------------------------------------------
# TEST 3: NEGATIVE INPUT QUANTITY
# --------------------------------------------------

def test_negative_input_quantity(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)
    data["input_quantity"] = -10

    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 422


# --------------------------------------------------
# TEST 4: ZERO INPUT QUANTITY
# --------------------------------------------------

def test_zero_input_quantity(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)
    data["input_quantity"] = 0

    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Input quantity must be greater than zero"
    )


# --------------------------------------------------
# TEST 5: NEGATIVE OUTPUT QUANTITY
# --------------------------------------------------

def test_negative_output_quantity(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)
    data["output_quantity"] = -5

    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 422


# --------------------------------------------------
# TEST 6: NEGATIVE WASTAGE QUANTITY
# --------------------------------------------------

def test_negative_wastage_quantity(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)
    data["wastage_quantity"] = -5

    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 422


# --------------------------------------------------
# TEST 7: OUTPUT PLUS WASTAGE EXCEEDS INPUT
# --------------------------------------------------

def test_invalid_production_quantity_consistency(
    test_environment
):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)

    data["input_quantity"] = 100
    data["output_quantity"] = 90
    data["wastage_quantity"] = 15

    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Output quantity plus wastage quantity "
        "cannot exceed input quantity"
    )


# --------------------------------------------------
# TEST 8: INVALID SHIFT
# --------------------------------------------------

def test_invalid_shift(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = production_payload(reference_ids)
    data["shift"] = "InvalidShift"

    response = client.post(
        "/production/",
        json=data
    )

    assert response.status_code == 400

    assert "Invalid shift" in response.json()["detail"]


# --------------------------------------------------
# TEST 9: NONEXISTENT PRODUCTION RECORD
# --------------------------------------------------

def test_get_nonexistent_production(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.get(
        "/production/999999"
    )

    assert response.status_code == 404


# --------------------------------------------------
# TEST 10: NO-CHANGE UPDATE
# --------------------------------------------------

def test_production_no_change_update(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.post(
        "/production/",
        json=production_payload(reference_ids)
    )

    assert response.status_code == 200

    production_id = response.json()["id"]

    response = client.put(
        f"/production/{production_id}",
        json={
            "output_quantity": 90.0
        }
    )

    assert response.status_code == 200

    with SessionLocal() as db:

        update_audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Production",
            AuditLog.entity_id == production_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert update_audit is None


# --------------------------------------------------
# TEST 11: CREATE ROLLBACK WHEN AUDIT FAILS
# --------------------------------------------------

def test_production_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal, reference_ids = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        production_service_module,
        "record_audit",
        fail_audit
    )

    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/production/",
        json=production_payload(reference_ids)
    )

    assert response.status_code == 500

    with SessionLocal() as db:

        production_records = db.query(Production).filter(
            Production.batch_id == reference_ids["batch_id"]
        ).all()

        assert len(production_records) == 0

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Production",
            AuditLog.action == "CREATE"
        ).first()

        assert audit is None

    test_client.close()


# --------------------------------------------------
# TEST 12: UPDATE CONSISTENCY VALIDATION
# --------------------------------------------------

def test_invalid_production_update(test_environment):

    client, SessionLocal, reference_ids = test_environment

    with SessionLocal() as db:

        production = create_test_production(
            db,
            reference_ids["batch_id"]
        )

        production_id = production.id

    response = client.put(
        f"/production/{production_id}",
        json={
            "output_quantity": 98.0
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Output quantity plus wastage quantity "
        "cannot exceed input quantity"
    )

    with SessionLocal() as db:

        production = db.query(Production).filter(
            Production.id == production_id
        ).first()

        assert production.output_quantity == 90.0


# --------------------------------------------------
# TEST 13: INVALID PRODUCTION UPDATE ID
# --------------------------------------------------

def test_update_nonexistent_production(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.put(
        "/production/999999",
        json={
            "output_quantity": 80.0
        }
    )

    assert response.status_code == 404


# --------------------------------------------------
# TEST 14: DELETE NONEXISTENT PRODUCTION
# --------------------------------------------------

def test_delete_nonexistent_production(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.delete(
        "/production/999999"
    )

    assert response.status_code == 404
