
from fastapi import FastAPI

from app.database import Base, engine

# Import all database models
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

# Import existing routers
from app.routers.users import router as users_router
from app.routers.imports import router as imports_router
from app.routers.production import router as production_router
from app.routers.products import router as products_router
from app.routers.supplier import router as supplier_router
from app.routers.raw_material import router as raw_material_router
from app.routers.machine import router as machine_router
from app.routers.production_line import router as production_line_router
from app.routers.batch import router as batch_router
from app.routers.quality import router as quality_router
from app.routers.approval import router as approval_router
from app.routers.auth import router as auth_router


# Import Audit Trail router
from app.routers.audit import router as audit_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Initialize FastAPI
app = FastAPI(
    title="Food Plant Operations Management System",
    description="Management system for Chennai Frozen Foods Pvt. Ltd.",
    version="1.0.0"
)


# Register routers
app.include_router(users_router)
app.include_router(imports_router)
app.include_router(audit_router)
app.include_router(production_router)
app.include_router(products_router)
app.include_router(supplier_router)
app.include_router(raw_material_router)
app.include_router(machine_router)
app.include_router(production_line_router)
app.include_router(batch_router)
app.include_router(quality_router)
app.include_router(approval_router)
app.include_router(auth_router)

# Home endpoint
@app.get("/")
def home():

    return {
        "message": "Welcome to Food Plant Operations Management System",
        "status": "Running successfully",
        "company": "Chennai Frozen Foods Pvt. Ltd."
    }


# Health endpoint
@app.get("/health")
def health_check():
    return {"status": "Healthy"}


# Database status endpoint
@app.get("/database-status")
def database_status():
    return {
        "database": "SQLite",
        "status": "Connected",
        "tables": list(Base.metadata.tables.keys())
    }
