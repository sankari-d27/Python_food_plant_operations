
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
from app.routers.supplier import router as supplier_router
import app.services.supplier_service as supplier_service_module


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
    test_app.include_router(supplier_router)
    test_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(test_app)

    yield client, TestingSessionLocal

    client.close()
    test_app.dependency_overrides.clear()
    test_engine.dispose()


def test_supplier_crud_and_audit(test_environment):

    client, SessionLocal = test_environment

    supplier_data = {
        "supplier_name": "Automated Test Supplier",
        "contact_person": "Test Person",
        "email": "automated@example.com",
        "phone": "9876543210",
        "address": "Chennai, Tamil Nadu",
        "is_active": True
    }

    # CREATE
    response = client.post(
        "/suppliers/",
        json=supplier_data
    )

    assert response.status_code == 200

    supplier = response.json()
    supplier_id = supplier["id"]

    assert supplier["supplier_name"] == "Automated Test Supplier"

    # Verify CREATE audit
    with SessionLocal() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "Supplier",
                AuditLog.entity_id == supplier_id,
                AuditLog.action == "CREATE"
            )
            .first()
        )

        assert audit is not None
        assert audit.old_value is None

        new_value = json.loads(audit.new_value)
        assert new_value["supplier_name"] == "Automated Test Supplier"

    # GET ALL
    response = client.get("/suppliers/")

    assert response.status_code == 200
    assert any(
        item["id"] == supplier_id
        for item in response.json()
    )

    # GET BY ID
    response = client.get(f"/suppliers/{supplier_id}")

    assert response.status_code == 200
    assert response.json()["id"] == supplier_id

    # UPDATE
    update_data = {
        "supplier_name": "Updated Automated Supplier",
        "contact_person": "Updated Test Person",
        "email": "automated@example.com",
        "phone": "9876543210",
        "address": "Ambattur, Chennai",
        "is_active": True
    }

    response = client.put(
        f"/suppliers/{supplier_id}",
        json=update_data
    )

    assert response.status_code == 200
    assert response.json()["supplier_name"] == (
        "Updated Automated Supplier"
    )

    # Verify UPDATE audit
    with SessionLocal() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "Supplier",
                AuditLog.entity_id == supplier_id,
                AuditLog.action == "UPDATE"
            )
            .first()
        )

        assert audit is not None

        old_value = json.loads(audit.old_value)
        new_value = json.loads(audit.new_value)

        assert old_value["supplier_name"] == (
            "Automated Test Supplier"
        )

        assert new_value["supplier_name"] == (
            "Updated Automated Supplier"
        )

    # DELETE
    response = client.delete(
        f"/suppliers/{supplier_id}"
    )

    assert response.status_code == 200

    # Verify DELETE audit and record removal
    with SessionLocal() as db:

        deleted_supplier = db.query(Supplier).filter(
            Supplier.id == supplier_id
        ).first()

        assert deleted_supplier is None

        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "Supplier",
                AuditLog.entity_id == supplier_id,
                AuditLog.action == "DELETE"
            )
            .first()
        )

        assert audit is not None
        assert audit.new_value is None

        old_value = json.loads(audit.old_value)

        assert old_value["supplier_name"] == (
            "Updated Automated Supplier"
        )


def test_duplicate_supplier_validation(test_environment):

    client, SessionLocal = test_environment

    supplier_data = {
        "supplier_name": "Duplicate Test Supplier",
        "contact_person": "Test Person",
        "email": "duplicate@example.com",
        "phone": "9876543210",
        "address": "Chennai",
        "is_active": True
    }

    first_response = client.post(
        "/suppliers/",
        json=supplier_data
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/suppliers/",
        json=supplier_data
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Supplier name already exists"
    )


def test_supplier_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        supplier_service_module,
        "record_audit",
        fail_audit
    )

    # Prevent TestClient from re-raising the simulated server error
    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/suppliers/",
        json={
            "supplier_name": "Rollback Test Supplier",
            "contact_person": "Test Person",
            "email": "rollback@example.com",
            "phone": "9876543210",
            "address": "Chennai",
            "is_active": True
        }
    )

    assert response.status_code == 500

    # Verify supplier was rolled back
    with SessionLocal() as db:

        supplier = db.query(Supplier).filter(
            Supplier.supplier_name == "Rollback Test Supplier"
        ).first()

        assert supplier is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Supplier",
            AuditLog.action == "CREATE"
        ).first()

        assert audit is None

    test_client.close()
