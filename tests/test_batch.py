
import json

import pytest
from datetime import date, datetime
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
    QualityTest,
    Approval,
    AuditLog
)

from app.routers.batch import router as batch_router

import app.services.batch_service as batch_service_module


@pytest.fixture
def test_environment(tmp_path):

    test_database = tmp_path / "test_batch.db"

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
    test_app.include_router(batch_router)
    test_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(test_app)

    # Create required reference records
    with TestingSessionLocal() as db:

        user = User(
            username="batch_test_user",
            email="batch_test@example.com",
            password_hash="test_hash",
            role="production",
            is_active=True
        )

        product = Product(
            product_code="PROD-BATCH-001",
            product_name="Test Frozen Product",
            description="Batch testing product",
            unit="kg",
            is_active=True
        )

        line = ProductionLine(
            line_code="LINE-BATCH-001",
            line_name="Batch Testing Line",
            description="Batch testing line",
            is_active=True
        )

        db.add_all([user, product, line])
        db.commit()

        db.refresh(user)
        db.refresh(product)
        db.refresh(line)

        reference_ids = {
            "user_id": user.id,
            "product_id": product.id,
            "production_line_id": line.id
        }

    yield client, TestingSessionLocal, reference_ids

    client.close()
    test_app.dependency_overrides.clear()
    test_engine.dispose()


def batch_payload(reference_ids, batch_number="BATCH-TEST-001"):

    return {
        "batch_number": batch_number,
        "product_id": reference_ids["product_id"],
        "production_line_id": reference_ids["production_line_id"],
        "created_by": reference_ids["user_id"],
        "production_date": date.today().isoformat(),
        "input_quantity": 100.0,
        "output_quantity": 95.0,
        "status": "draft"
    }


def create_test_batch(db, reference_ids, batch_number):

    batch = Batch(
        batch_number=batch_number,
        product_id=reference_ids["product_id"],
        production_line_id=reference_ids["production_line_id"],
        created_by=reference_ids["user_id"],
        production_date=date.today(),
        input_quantity=100.0,
        output_quantity=95.0,
        status="draft"
    )

    db.add(batch)
    db.commit()
    db.refresh(batch)

    return batch


def test_batch_crud_and_audit(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = batch_payload(reference_ids)

    # CREATE
    response = client.post("/batches/", json=data)

    assert response.status_code == 200

    batch_id = response.json()["id"]

    assert response.json()["batch_number"] == "BATCH-TEST-001"

    # Verify CREATE audit
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Batch",
            AuditLog.entity_id == batch_id,
            AuditLog.action == "CREATE"
        ).first()

        assert audit is not None

        new_value = json.loads(audit.new_value)

        assert new_value["batch_number"] == "BATCH-TEST-001"

    # GET ALL
    response = client.get("/batches/")

    assert response.status_code == 200

    assert any(
        item["id"] == batch_id
        for item in response.json()
    )

    # GET BY ID
    response = client.get(f"/batches/{batch_id}")

    assert response.status_code == 200

    # UPDATE
    response = client.put(
        f"/batches/{batch_id}",
        json={"status": "completed"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    # Verify UPDATE audit
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Batch",
            AuditLog.entity_id == batch_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is not None

        old_value = json.loads(audit.old_value)
        new_value = json.loads(audit.new_value)

        assert old_value["status"] == "draft"
        assert new_value["status"] == "completed"

    # DELETE
    response = client.delete(f"/batches/{batch_id}")

    assert response.status_code == 200

    with SessionLocal() as db:

        assert db.query(Batch).filter(
            Batch.id == batch_id
        ).first() is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Batch",
            AuditLog.entity_id == batch_id,
            AuditLog.action == "DELETE"
        ).first()

        assert audit is not None
        assert audit.new_value is None


def test_duplicate_batch_numbers_are_allowed(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = batch_payload(reference_ids, "BATCH-DUP-001")

    first = client.post("/batches/", json=data)
    second = client.post("/batches/", json=data)

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["id"] != second.json()["id"]


def test_invalid_product_reference(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = batch_payload(reference_ids)
    data["product_id"] = 999999

    response = client.post("/batches/", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Product does not exist"


def test_invalid_production_line_reference(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = batch_payload(reference_ids)
    data["production_line_id"] = 999999

    response = client.post("/batches/", json=data)

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Production line does not exist"
    )


def test_invalid_user_reference(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = batch_payload(reference_ids)
    data["created_by"] = 999999

    response = client.post("/batches/", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "User does not exist"


def test_negative_quantity_validation(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = batch_payload(reference_ids)
    data["input_quantity"] = -10

    response = client.post("/batches/", json=data)

    assert response.status_code == 422 or response.status_code == 400


def test_cannot_delete_batch_with_production_record(test_environment):

    client, SessionLocal, reference_ids = test_environment

    with SessionLocal() as db:

        batch = create_test_batch(
            db, reference_ids, "BATCH-PROD-001"
        )

        batch_id = batch.id

        production = Production(
            batch_id=batch_id,
            production_date=date.today(),
            input_quantity=100,
            output_quantity=95,
            wastage_quantity=5,
            shift="morning"
        )

        db.add(production)
        db.commit()

    response = client.delete(f"/batches/{batch_id}")

    assert response.status_code == 400

    assert "production records" in response.json()["detail"]

    with SessionLocal() as db:

        assert db.query(Batch).filter(
            Batch.id == batch_id
        ).first() is not None


def test_cannot_delete_batch_with_quality_test(test_environment):

    client, SessionLocal, reference_ids = test_environment

    with SessionLocal() as db:

        batch = create_test_batch(
            db, reference_ids, "BATCH-QUALITY-001"
        )

        batch_id = batch.id

        quality_test = QualityTest(
            batch_id=batch_id,
            moisture_reading=2.5,
            result="pass",
            tested_at=datetime.utcnow()
        )

        db.add(quality_test)
        db.commit()

    response = client.delete(f"/batches/{batch_id}")

    assert response.status_code == 400

    assert "quality test records" in response.json()["detail"]


def test_cannot_delete_batch_with_approval(test_environment):

    client, SessionLocal, reference_ids = test_environment

    with SessionLocal() as db:

        batch = create_test_batch(
            db, reference_ids, "BATCH-APPROVAL-001"
        )

        batch_id = batch.id

        approval = Approval(
            batch_id=batch_id,
            reviewed_by=reference_ids["user_id"],
            decision="pending"
        )

        db.add(approval)
        db.commit()

    response = client.delete(f"/batches/{batch_id}")

    assert response.status_code == 400

    assert "approval records" in response.json()["detail"]


def test_batch_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal, reference_ids = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        batch_service_module,
        "record_audit",
        fail_audit
    )

    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    data = batch_payload(reference_ids, "BATCH-ROLLBACK-001")

    response = test_client.post("/batches/", json=data)

    assert response.status_code == 500

    with SessionLocal() as db:

        batch = db.query(Batch).filter(
            Batch.batch_number == "BATCH-ROLLBACK-001"
        ).first()

        assert batch is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Batch",
            AuditLog.action == "CREATE"
        ).first()

        assert audit is None

    test_client.close()


def test_batch_no_change_update(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = batch_payload(reference_ids, "BATCH-NOCHANGE-001")

    create_response = client.post("/batches/", json=data)

    assert create_response.status_code == 200

    batch_id = create_response.json()["id"]

    response = client.put(
        f"/batches/{batch_id}",
        json={"status": "draft"}
    )

    assert response.status_code == 200

    with SessionLocal() as db:

        update_audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Batch",
            AuditLog.entity_id == batch_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert update_audit is None


def test_get_nonexistent_batch(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.get("/batches/999999")

    assert response.status_code == 404
