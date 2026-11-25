
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

from app.routers.production_line import router as production_line_router
import app.services.production_line_service as production_line_service_module


@pytest.fixture
def test_environment(tmp_path):

    test_database = tmp_path / "test_production_line.db"

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
    test_app.include_router(production_line_router)
    test_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(test_app)

    yield client, TestingSessionLocal

    client.close()
    test_app.dependency_overrides.clear()
    test_engine.dispose()


def test_production_line_crud_and_audit(test_environment):

    client, SessionLocal = test_environment

    line_data = {
        "line_code": "LINE-TEST-001",
        "line_name": "Automated Test Production Line",
        "description": "Production line testing",
        "is_active": True
    }

    # CREATE
    response = client.post(
        "/production-lines/",
        json=line_data
    )

    assert response.status_code == 200

    line = response.json()
    line_id = line["id"]

    assert line["line_code"] == "LINE-TEST-001"

    # Verify CREATE audit
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "ProductionLine",
            AuditLog.entity_id == line_id,
            AuditLog.action == "CREATE"
        ).first()

        assert audit is not None

        new_value = json.loads(audit.new_value)

        assert new_value["line_code"] == "LINE-TEST-001"

    # GET ALL
    response = client.get("/production-lines/")

    assert response.status_code == 200

    assert any(
        item["id"] == line_id
        for item in response.json()
    )

    # GET BY ID
    response = client.get(
        f"/production-lines/{line_id}"
    )

    assert response.status_code == 200

    # UPDATE
    update_data = {
        "line_code": "LINE-TEST-001",
        "line_name": "Updated Test Production Line",
        "description": "Updated production line",
        "is_active": True
    }

    response = client.put(
        f"/production-lines/{line_id}",
        json=update_data
    )

    assert response.status_code == 200

    assert response.json()["line_name"] == (
        "Updated Test Production Line"
    )

    # Verify UPDATE audit
    with SessionLocal() as db:

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "ProductionLine",
            AuditLog.entity_id == line_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is not None

        old_value = json.loads(audit.old_value)
        new_value = json.loads(audit.new_value)

        assert old_value["line_name"] == (
            "Automated Test Production Line"
        )

        assert new_value["line_name"] == (
            "Updated Test Production Line"
        )

    # DELETE
    response = client.delete(
        f"/production-lines/{line_id}"
    )

    assert response.status_code == 200

    # Verify DELETE audit
    with SessionLocal() as db:

        deleted_line = db.query(ProductionLine).filter(
            ProductionLine.id == line_id
        ).first()

        assert deleted_line is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "ProductionLine",
            AuditLog.entity_id == line_id,
            AuditLog.action == "DELETE"
        ).first()

        assert audit is not None
        assert audit.new_value is None


def test_duplicate_production_line_code_validation(test_environment):

    client, SessionLocal = test_environment

    line_data = {
        "line_code": "LINE-DUP-001",
        "line_name": "Duplicate Test Line",
        "description": "Duplicate testing",
        "is_active": True
    }

    first_response = client.post(
        "/production-lines/",
        json=line_data
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/production-lines/",
        json=line_data
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Production line code already exists"
    )


def test_production_line_required_field_validation(test_environment):

    client, SessionLocal = test_environment

    response = client.post(
        "/production-lines/",
        json={
            "line_code": "",
            "line_name": "",
            "description": "Invalid line",
            "is_active": True
        }
    )

    assert response.status_code == 422


def test_cannot_delete_production_line_with_assigned_machine(
    test_environment
):

    client, SessionLocal = test_environment

    with SessionLocal() as db:

        line = ProductionLine(
            line_code="LINE-MACHINE-001",
            line_name="Machine Assigned Line",
            description="Machine reference test",
            is_active=True
        )

        db.add(line)
        db.commit()
        db.refresh(line)

        line_id = line.id

        machine = Machine(
            machine_code="MCH-LINE-001",
            machine_name="Assigned Test Machine",
            production_line_id=line_id,
            machine_status="available",
            is_active=True
        )

        db.add(machine)
        db.commit()

    response = client.delete(
        f"/production-lines/{line_id}"
    )

    assert response.status_code == 400

    assert "machines are assigned" in (
        response.json()["detail"]
    )

    with SessionLocal() as db:

        assert db.query(ProductionLine).filter(
            ProductionLine.id == line_id
        ).first() is not None


def test_production_line_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        production_line_service_module,
        "record_audit",
        fail_audit
    )

    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/production-lines/",
        json={
            "line_code": "LINE-ROLLBACK-001",
            "line_name": "Rollback Test Line",
            "description": "Rollback testing",
            "is_active": True
        }
    )

    assert response.status_code == 500

    with SessionLocal() as db:

        line = db.query(ProductionLine).filter(
            ProductionLine.line_code == "LINE-ROLLBACK-001"
        ).first()

        assert line is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "ProductionLine",
            AuditLog.action == "CREATE"
        ).first()

        assert audit is None

    test_client.close()


def test_production_line_no_change_update(test_environment):

    client, SessionLocal = test_environment

    line_data = {
        "line_code": "LINE-NOCHANGE-001",
        "line_name": "No Change Test Line",
        "description": "No change testing",
        "is_active": True
    }

    create_response = client.post(
        "/production-lines/",
        json=line_data
    )

    assert create_response.status_code == 200

    line_id = create_response.json()["id"]

    response = client.put(
        f"/production-lines/{line_id}",
        json=line_data
    )

    assert response.status_code == 200

    with SessionLocal() as db:

        update_audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "ProductionLine",
            AuditLog.entity_id == line_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert update_audit is None
