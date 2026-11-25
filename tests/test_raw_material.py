
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import (
    User,
    Product,
    Supplier,
    ProductionLine,
    Batch,
    RawMaterial,
    Machine,
    Production,
    QualityTest,
    Approval,
    AuditLog
)

from app.routers.raw_material import router as raw_material_router

import app.services.raw_material_service as raw_material_service_module


@pytest.fixture
def test_environment(tmp_path):

    # Separate temporary SQLite database
    test_database = tmp_path / "test_food_plant.db"

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
    test_app.include_router(raw_material_router)
    test_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(test_app)

    # Create a supplier for raw material tests
    with TestingSessionLocal() as db:

        supplier = Supplier(
            supplier_name="Raw Material Test Supplier",
            contact_person="Test Person",
            email="rawmaterial@example.com",
            phone="9876543210",
            address="Chennai, Tamil Nadu",
            is_active=True
        )

        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        supplier_id = supplier.id

    yield client, TestingSessionLocal, supplier_id

    client.close()
    test_app.dependency_overrides.clear()
    test_engine.dispose()


def test_raw_material_crud_and_audit(test_environment):

    client, SessionLocal, supplier_id = test_environment

    material_data = {
        "material_code": "RM-TEST-001",
        "material_name": "Frozen Chicken",
        "supplier_id": supplier_id,
        "available_quantity": 500.0,
        "unit": "KG",
        "is_active": True
    }

    # CREATE
    response = client.post(
        "/raw-materials/",
        json=material_data
    )

    assert response.status_code == 200

    material = response.json()
    material_id = material["id"]

    assert material["material_code"] == "RM-TEST-001"
    assert material["material_name"] == "Frozen Chicken"

    # Verify CREATE audit
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "RawMaterial",
            AuditLog.entity_id == material_id,
            AuditLog.action == "CREATE"
        ).first()

        assert audit is not None
        assert audit.old_value is None

        new_value = json.loads(audit.new_value)

       
def test_duplicate_material_code_validation(test_environment):

    client, SessionLocal, supplier_id = test_environment

    material_data = {
        "material_code": "RM-DUP-001",
        "material_name": "Duplicate Test Material",
        "supplier_id": supplier_id,
        "available_quantity": 100.0,
        "unit": "KG",
        "is_active": True
    }

    first_response = client.post(
        "/raw-materials/",
        json=material_data
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/raw-materials/",
        json=material_data
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Material code already exists"
    )


def test_invalid_supplier_validation(test_environment):

    client, SessionLocal, supplier_id = test_environment

    material_data = {
        "material_code": "RM-INVALID-001",
        "material_name": "Invalid Supplier Material",
        "supplier_id": 999999,
        "available_quantity": 100.0,
        "unit": "KG",
        "is_active": True
    }

    response = client.post(
        "/raw-materials/",
        json=material_data
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Supplier not found"



def test_negative_quantity_validation(test_environment):

    client, SessionLocal, supplier_id = test_environment

    material_data = {
        "material_code": "RM-NEG-001",
        "material_name": "Negative Quantity Material",
        "supplier_id": supplier_id,
        "available_quantity": -50.0,
        "unit": "KG",
        "is_active": True
    }

    response = client.post(
        "/raw-materials/",
        json=material_data
    )

    # Pydantic rejects negative quantity before service execution
    assert response.status_code == 422

    # Verify the validation error identifies available_quantity
    errors = response.json()["detail"]

    assert any(
        error["loc"][-1] == "available_quantity"
        for error in errors
    )


def test_raw_material_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal, supplier_id = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        raw_material_service_module,
        "record_audit",
        fail_audit
    )

    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/raw-materials/",
        json={
            "material_code": "RM-ROLLBACK-001",
            "material_name": "Rollback Test Material",
            "supplier_id": supplier_id,
            "available_quantity": 200.0,
            "unit": "KG",
            "is_active": True
        }
    )

    assert response.status_code == 500

    with SessionLocal() as db:

        material = db.query(RawMaterial).filter(
            RawMaterial.material_code == "RM-ROLLBACK-001"
        ).first()

        assert material is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "RawMaterial",
            AuditLog.action == "CREATE"
        ).first()

        assert audit is None

    test_client.close()


def test_raw_material_no_change_update(test_environment):

    client, SessionLocal, supplier_id = test_environment

    material_data = {
        "material_code": "RM-NOCHANGE-001",
        "material_name": "No Change Material",
        "supplier_id": supplier_id,
        "available_quantity": 300.0,
        "unit": "KG",
        "is_active": True
    }

    create_response = client.post(
        "/raw-materials/",
        json=material_data
    )

    assert create_response.status_code == 200

    material_id = create_response.json()["id"]

    response = client.put(
        f"/raw-materials/{material_id}",
        json=material_data
    )

    assert response.status_code == 200

    with SessionLocal() as db:

        update_audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "RawMaterial",
            AuditLog.entity_id == material_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert update_audit is None
