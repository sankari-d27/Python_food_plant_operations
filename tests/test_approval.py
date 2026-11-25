
import json
from datetime import date

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.auth import get_current_user

from app.models import (
    User,
    Product,
    ProductionLine,
    Batch,
    Approval,
    AuditLog
)

from app.routers.approval import router as approval_router

import app.services.approval_service as approval_service_module


# --------------------------------------------------
# TEST DATABASE FIXTURE
# --------------------------------------------------

@pytest.fixture
def test_environment(tmp_path):

    test_database = tmp_path / "test_approval.db"

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
    test_app.include_router(approval_router)

    test_app.dependency_overrides[get_db] = override_get_db

    # TEST ADMIN AUTHENTICATION
    def override_get_current_user():
        with TestingSessionLocal() as db:
            admin = db.query(User).filter(
                User.username == "approval_admin"
            ).first()

            return admin

    test_app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )

    client = TestClient(test_app)

    # CREATE REFERENCE RECORDS
    with TestingSessionLocal() as db:

        user = User(
            username="approval_test_user",
            email="approval_test@example.com",
            password_hash="test_hash",
            role="quality",
            is_active=True
        )

        admin_user = User(
            username="approval_admin",
            email="approval_admin@example.com",
            password_hash="test_hash",
            role="admin",
            is_active=True
        )

        product = Product(
            product_code="PROD-APP-001",
            product_name="Approval Test Product",
            description="Approval testing product",
            unit="kg",
            is_active=True
        )

        line = ProductionLine(
            line_code="LINE-APP-001",
            line_name="Approval Testing Line",
            description="Approval testing line",
            is_active=True
        )

        db.add_all([
            user,
            admin_user,
            product,
            line
        ])

        db.commit()

        db.refresh(user)
        db.refresh(product)
        db.refresh(line)

        batch = Batch(
            batch_number="BATCH-APP-001",
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
# APPROVAL TEST DATA
# --------------------------------------------------

def approval_payload(reference_ids):

    return {
        "batch_id": reference_ids["batch_id"],
        "decision": "pending",
        "comments": "Awaiting quality review"
    }


# --------------------------------------------------
# TEST 1: COMPLETE CRUD AND AUDIT
# --------------------------------------------------

def test_approval_crud_and_audit(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = approval_payload(reference_ids)

    response = client.post("/approvals/", json=data)

    assert response.status_code == 200

    approval = response.json()
    approval_id = approval["id"]

    assert approval["batch_id"] == reference_ids["batch_id"]
    assert approval["decision"] == "pending"
    assert approval["reviewed_at"] is None

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Approval",
            AuditLog.entity_id == approval_id,
            AuditLog.action == "CREATE"
        ).first()

        assert audit is not None

        new_value = json.loads(audit.new_value)
        assert new_value["decision"] == "pending"

    response = client.get("/approvals/")

    assert response.status_code == 200

    assert any(
        item["id"] == approval_id
        for item in response.json()
    )

    response = client.get(f"/approvals/{approval_id}")

    assert response.status_code == 200
    assert response.json()["id"] == approval_id

    response = client.get(
        f"/approvals/batch/{reference_ids['batch_id']}"
    )

    assert response.status_code == 200

    assert any(
        item["id"] == approval_id
        for item in response.json()
    )

    response = client.put(
        f"/approvals/{approval_id}",
        json={"comments": "Quality review in progress"}
    )

    assert response.status_code == 200

    assert response.json()["comments"] == (
        "Quality review in progress"
    )

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Approval",
            AuditLog.entity_id == approval_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is not None

        old_value = json.loads(audit.old_value)
        new_value = json.loads(audit.new_value)

        assert old_value["comments"] == "Awaiting quality review"
        assert new_value["comments"] == "Quality review in progress"

    response = client.delete(f"/approvals/{approval_id}")

    assert response.status_code == 400

    with SessionLocal() as db:
        approval = db.query(Approval).filter(
            Approval.id == approval_id
        ).first()

        assert approval is not None


# --------------------------------------------------
# TEST 2: INVALID BATCH REFERENCE
# --------------------------------------------------

def test_invalid_batch_reference(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = approval_payload(reference_ids)
    data["batch_id"] = 999999

    response = client.post("/approvals/", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Batch does not exist"


# --------------------------------------------------
# TEST 3: INVALID REVIEWER
# --------------------------------------------------

def test_invalid_reviewer_reference(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = approval_payload(reference_ids)
    data["reviewed_by"] = 999999

    response = client.post("/approvals/", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Reviewer user does not exist"


# --------------------------------------------------
# TEST 4: INVALID DECISION
# --------------------------------------------------

def test_invalid_approval_decision(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = approval_payload(reference_ids)
    data["decision"] = "invalid"

    response = client.post("/approvals/", json=data)

    assert response.status_code == 422


# --------------------------------------------------
# TEST 5: COMMENTS LENGTH VALIDATION
# --------------------------------------------------

def test_approval_comments_length(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = approval_payload(reference_ids)
    data["comments"] = "A" * 501

    response = client.post("/approvals/", json=data)

    assert response.status_code == 422


# --------------------------------------------------
# TEST 6: APPROVE PENDING APPROVAL
# --------------------------------------------------

def test_approve_pending_approval(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.post(
        "/approvals/",
        json=approval_payload(reference_ids)
    )

    assert response.status_code == 200

    approval_id = response.json()["id"]

    response = client.put(
        f"/approvals/{approval_id}",
        json={
            "decision": "approved",
            "reviewed_by": reference_ids["user_id"],
            "comments": "Quality checks passed"
        }
    )

    assert response.status_code == 200

    approval = response.json()

    assert approval["decision"] == "approved"
    assert approval["reviewed_by"] == reference_ids["user_id"]
    assert approval["reviewed_at"] is not None

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Approval",
            AuditLog.entity_id == approval_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert audit is not None


# --------------------------------------------------
# TEST 7: REJECT PENDING APPROVAL
# --------------------------------------------------

def test_reject_pending_approval(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.post(
        "/approvals/",
        json=approval_payload(reference_ids)
    )

    assert response.status_code == 200

    approval_id = response.json()["id"]

    response = client.put(
        f"/approvals/{approval_id}",
        json={
            "decision": "rejected",
            "reviewed_by": reference_ids["user_id"],
            "comments": "Quality requirements not satisfied"
        }
    )

    assert response.status_code == 200

    approval = response.json()

    assert approval["decision"] == "rejected"
    assert approval["reviewed_by"] == reference_ids["user_id"]
    assert approval["reviewed_at"] is not None


# --------------------------------------------------
# TEST 8: FINALIZED APPROVAL CANNOT BE MODIFIED
# --------------------------------------------------

def test_finalized_approval_cannot_be_modified(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.post(
        "/approvals/",
        json=approval_payload(reference_ids)
    )

    assert response.status_code == 200

    approval_id = response.json()["id"]

    response = client.put(
        f"/approvals/{approval_id}",
        json={
            "decision": "approved",
            "reviewed_by": reference_ids["user_id"]
        }
    )

    assert response.status_code == 200

    response = client.put(
        f"/approvals/{approval_id}",
        json={"comments": "Changed after approval"}
    )

    assert response.status_code == 400

    assert "Finalized approvals cannot be modified" in (
        response.json()["detail"]
    )


# --------------------------------------------------
# TEST 9: FINALIZATION REQUIRES REVIEWER
# --------------------------------------------------

def test_finalization_requires_reviewer(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.post(
        "/approvals/",
        json=approval_payload(reference_ids)
    )

    assert response.status_code == 200

    approval_id = response.json()["id"]

    response = client.put(
        f"/approvals/{approval_id}",
        json={"decision": "approved"}
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Reviewer is required to finalize approval"
    )


# --------------------------------------------------
# TEST 10: NEW APPROVAL MUST START AS PENDING
# --------------------------------------------------

def test_new_approval_cannot_start_as_approved(test_environment):

    client, SessionLocal, reference_ids = test_environment

    data = approval_payload(reference_ids)
    data["decision"] = "approved"
    data["reviewed_by"] = reference_ids["user_id"]

    response = client.post("/approvals/", json=data)

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "New approvals must start with pending decision"
    )


# --------------------------------------------------
# TEST 11: NO-CHANGE UPDATE
# --------------------------------------------------

def test_approval_no_change_update(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.post(
        "/approvals/",
        json=approval_payload(reference_ids)
    )

    assert response.status_code == 200

    approval_id = response.json()["id"]

    response = client.put(
        f"/approvals/{approval_id}",
        json={"comments": "Awaiting quality review"}
    )

    assert response.status_code == 200

    with SessionLocal() as db:
        update_audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Approval",
            AuditLog.entity_id == approval_id,
            AuditLog.action == "UPDATE"
        ).first()

        assert update_audit is None


# --------------------------------------------------
# TEST 12: NONEXISTENT APPROVAL
# --------------------------------------------------

def test_get_nonexistent_approval(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.get("/approvals/999999")

    assert response.status_code == 404


# --------------------------------------------------
# TEST 13: DELETE NONEXISTENT APPROVAL
# --------------------------------------------------

def test_delete_nonexistent_approval(test_environment):

    client, SessionLocal, reference_ids = test_environment

    response = client.delete("/approvals/999999")

    assert response.status_code == 404


# --------------------------------------------------
# TEST 14: CREATE ROLLBACK WHEN AUDIT FAILS
# --------------------------------------------------

def test_approval_create_rollback_when_audit_fails(
    test_environment,
    monkeypatch
):

    client, SessionLocal, reference_ids = test_environment

    def fail_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        approval_service_module,
        "record_audit",
        fail_audit
    )

    test_client = TestClient(
        client.app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/approvals/",
        json=approval_payload(reference_ids)
    )

    assert response.status_code == 500

    with SessionLocal() as db:
        approvals = db.query(Approval).all()

        assert len(approvals) == 0

        audit = db.query(AuditLog).filter(
            AuditLog.entity_type == "Approval",
            AuditLog.action == "CREATE"
        ).first()

        assert audit is None

    test_client.close()
