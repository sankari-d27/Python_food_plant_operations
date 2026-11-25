
import json
from datetime import date, datetime

import pytest
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
    QualityTest,
    AuditLog
)
from app.routers.quality import router as quality_router

import app.services.quality_service as quality_service_module


@pytest.fixture
def test_environment(tmp_path):

    test_database = tmp_path / "test_quality.db"

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
    test_app.include_router(quality_router)
    test_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(test_app)

    with TestingSessionLocal() as db:

        user = User(
            username="quality_test_user",
            email="quality_test@example.com",
            password_hash="test_hash",
            role="quality",
            is_active=True
        )

        product = Product(
            product_code="PROD-QUALITY-001",
            product_name="Quality Testing Product",
            description="Quality testing product",
            unit="kg",
            is_active=True
        )

        line = ProductionLine(
            line_code="LINE-QUALITY-001",
            line_name="Quality Testing Line",
            description="Quality testing line",
            is_active=True
        )

        db.add_all([user, product, line])
        db.commit()

        db.refresh(user)
        db.refresh(product)
        db.refresh(line)

        batch = Batch(
            batch_number="BATCH-QUALITY-001",
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
            "batch_id": batch.id
        }

    yield client, TestingSessionLocal, reference_ids

    client.close()
    test_app.dependency_overrides.clear()
    test_engine.dispose()


def quality_payload(reference_ids):

    return {
        "batch_id": reference_ids["batch_id"],
        "moisture_reading": 2.5,
        "result": "pass",
        "tested_at": datetime.now().isoformat()
    }


def test_quality_crud_and_audit(test_environment):

    client, SessionLocal, refs = test_environment

    response = client.post(
        "/quality/",
        json=quality_payload(refs)
    )

    assert response.status_code == 200

    quality_id = response.json()["id"]

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "QualityTest",
            AuditLog.entity_id == quality_id,
            AuditLog.action == "CREATE"
        ).first()

        assert audit is not None
        assert json.loads(audit.new_value)["result"] == "pass"

    response = client.get("/quality/")
    assert response.status_code == 200

    response = client.get(f"/quality/{quality_id}")
    assert response.status_code == 200

    response = client.put(
        f"/quality/{quality_id}",
        json={"result": "fail", "moisture_reading": 3.0}
    )

    assert response.status_code == 200
    assert response.json()["result"] == "fail"

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "QualityTest",
            AuditLog.entity_id == quality_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is not None
        assert json.loads(audit.old_value)["result"] == "pass"
        assert json.loads(audit.new_value)["result"] == "fail"

    response = client.delete(f"/quality/{quality_id}")
    assert response.status_code == 200

    with SessionLocal() as db:
        assert db.query(QualityTest).filter(
            QualityTest.id == quality_id
        ).first() is None

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "QualityTest",
            AuditLog.entity_id == quality_id,
            AuditLog.action == "DELETE"
        ).first()

        assert audit is not None


def test_invalid_batch_reference(test_environment):

    client, _, refs = test_environment

    data = quality_payload(refs)
    data["batch_id"] = 999999

    response = client.post("/quality/", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Batch does not exist"


def test_invalid_quality_result(test_environment):

    client, _, refs = test_environment

    data = quality_payload(refs)
    data["result"] = "unknown"

    response = client.post("/quality/", json=data)

    assert response.status_code == 400


def test_negative_moisture_reading(test_environment):

    client, _, refs = test_environment

    data = quality_payload(refs)
    data["moisture_reading"] = -2.5

    response = client.post("/quality/", json=data)

    assert response.status_code == 422


def test_quality_no_change_update(test_environment):

    client, SessionLocal, refs = test_environment

    response = client.post("/quality/", json=quality_payload(refs))
    assert response.status_code == 200

    quality_id = response.json()["id"]

    response = client.put(
        f"/quality/{quality_id}",
        json={"result": "pass"}
    )

    assert response.status_code == 200

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "QualityTest",
            AuditLog.entity_id == quality_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is None


def test_quality_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal, refs = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        quality_service_module,
        "record_audit",
        fail_audit
    )

    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/quality/",
        json=quality_payload(refs)
    )

    assert response.status_code == 500

    with SessionLocal() as db:
        assert db.query(QualityTest).first() is None
        assert db.query(AuditLog).filter(
            AuditLog.entity_type == "QualityTest"
        ).first() is None

    test_client.close()


def test_get_nonexistent_quality(test_environment):

    client, _, _ = test_environment

    response = client.get("/quality/999999")

    assert response.status_code == 404


def test_delete_nonexistent_quality(test_environment):

    client, _, _ = test_environment

    response = client.delete("/quality/999999")

    assert response.status_code == 404


def test_quality_update_invalid_result(test_environment):

    client, _, refs = test_environment

    response = client.post("/quality/", json=quality_payload(refs))
    quality_id = response.json()["id"]

    response = client.put(
        f"/quality/{quality_id}",
        json={"result": "unknown"}
    )

    assert response.status_code == 400


def test_quality_update_negative_moisture(test_environment):

    client, _, refs = test_environment

    response = client.post("/quality/", json=quality_payload(refs))
    quality_id = response.json()["id"]

    response = client.put(
        f"/quality/{quality_id}",
        json={"moisture_reading": -1}
    )

    assert response.status_code == 422
