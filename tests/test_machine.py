
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

from app.routers.machine import router as machine_router
import app.services.machine_service as machine_service_module


@pytest.fixture
def test_environment(tmp_path):

    test_database = tmp_path / "test_machine.db"

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
    test_app.include_router(machine_router)
    test_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(test_app)

    # Create a production line for machine testing
    with TestingSessionLocal() as db:

        production_line = ProductionLine(
            line_code="LINE-TEST-001",
            line_name="Automated Test Production Line",
            description="Machine testing line",
            is_active=True
        )

        db.add(production_line)
        db.commit()
        db.refresh(production_line)

        production_line_id = production_line.id

    yield client, TestingSessionLocal, production_line_id

    client.close()
    test_app.dependency_overrides.clear()
    test_engine.dispose()


def test_machine_crud_and_audit(test_environment):

    client, SessionLocal, production_line_id = test_environment

    machine_data = {
        "machine_code": "MCH-TEST-001",
        "machine_name": "Automated Test Machine",
        "production_line_id": production_line_id,
        "machine_status": "available",
        "is_active": True
    }

    # CREATE
    response = client.post(
        "/machines/",
        json=machine_data
    )

    assert response.status_code == 200

    machine = response.json()
    machine_id = machine["id"]

    assert machine["machine_code"] == "MCH-TEST-001"

    # Verify CREATE audit
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Machine",
            AuditLog.entity_id == machine_id,
            AuditLog.action == "CREATE"
        ).first()

        assert audit is not None

        new_value = json.loads(audit.new_value)

        assert new_value["machine_code"] == "MCH-TEST-001"

    # GET ALL
    response = client.get("/machines/")

    assert response.status_code == 200

    assert any(
        item["id"] == machine_id
        for item in response.json()
    )

    # GET BY ID
    response = client.get(
        f"/machines/{machine_id}"
    )

    assert response.status_code == 200

    # UPDATE
    update_data = {
        "machine_code": "MCH-TEST-001",
        "machine_name": "Updated Test Machine",
        "production_line_id": production_line_id,
        "machine_status": "maintenance",
        "is_active": True
    }

    response = client.put(
        f"/machines/{machine_id}",
        json=update_data
    )

    assert response.status_code == 200

    assert response.json()["machine_name"] == (
        "Updated Test Machine"
    )

    # Verify UPDATE audit
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Machine",
            AuditLog.entity_id == machine_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is not None

        old_value = json.loads(audit.old_value)
        new_value = json.loads(audit.new_value)

        assert old_value["machine_status"] == "available"
        assert new_value["machine_status"] == "maintenance"

    # DELETE
    response = client.delete(
        f"/machines/{machine_id}"
    )

    assert response.status_code == 200

    # Verify DELETE audit and record removal
    with SessionLocal() as db:

        deleted_machine = db.query(Machine).filter(
            Machine.id == machine_id
        ).first()

        assert deleted_machine is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Machine",
            AuditLog.entity_id == machine_id,
            AuditLog.action == "DELETE"
        ).first()

        assert audit is not None
        assert audit.new_value is None


def test_duplicate_machine_code_validation(test_environment):

    client, SessionLocal, production_line_id = test_environment

    machine_data = {
        "machine_code": "MCH-DUP-001",
        "machine_name": "Duplicate Test Machine",
        "production_line_id": production_line_id,
        "machine_status": "available",
        "is_active": True
    }

    first_response = client.post(
        "/machines/",
        json=machine_data
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/machines/",
        json=machine_data
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Machine code already exists"
    )


def test_invalid_production_line_validation(test_environment):

    client, SessionLocal, production_line_id = test_environment

    response = client.post(
        "/machines/",
        json={
            "machine_code": "MCH-INVALID-001",
            "machine_name": "Invalid Line Machine",
            "production_line_id": 999999,
            "machine_status": "available",
            "is_active": True
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Production line not found"
    )


def test_invalid_machine_status_validation(test_environment):

    client, SessionLocal, production_line_id = test_environment

    response = client.post(
        "/machines/",
        json={
            "machine_code": "MCH-STATUS-001",
            "machine_name": "Invalid Status Machine",
            "production_line_id": production_line_id,
            "machine_status": "unknown",
            "is_active": True
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid machine status"
    )


def test_machine_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal, production_line_id = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        machine_service_module,
        "record_audit",
        fail_audit
    )

    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/machines/",
        json={
            "machine_code": "MCH-ROLLBACK-001",
            "machine_name": "Rollback Test Machine",
            "production_line_id": production_line_id,
            "machine_status": "available",
            "is_active": True
        }
    )

    assert response.status_code == 500

    with SessionLocal() as db:

        machine = db.query(Machine).filter(
            Machine.machine_code == "MCH-ROLLBACK-001"
        ).first()

        assert machine is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Machine",
            AuditLog.action == "CREATE"
        ).first()

        assert audit is None

    test_client.close()


def test_machine_no_change_update(test_environment):

    client, SessionLocal, production_line_id = test_environment

    machine_data = {
        "machine_code": "MCH-NOCHANGE-001",
        "machine_name": "No Change Machine",
        "production_line_id": production_line_id,
        "machine_status": "available",
        "is_active": True
    }

    create_response = client.post(
        "/machines/",
        json=machine_data
    )

    assert create_response.status_code == 200

    machine_id = create_response.json()["id"]

    response = client.put(
        f"/machines/{machine_id}",
        json=machine_data
    )

    assert response.status_code == 200

    with SessionLocal() as db:

        update_audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Machine",
            AuditLog.entity_id == machine_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert update_audit is None
