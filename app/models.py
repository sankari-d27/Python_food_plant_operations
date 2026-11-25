
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# 1. USER MODEL
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150))
    role = Column(String(50), default="operator")
    is_active = Column(Boolean, default=True)


# 2. PRODUCT MODEL
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(150), nullable=False)
    product_code = Column(String(50), unique=True)
    description = Column(Text)
    unit = Column(String(30))
    is_active = Column(Boolean, default=True)


# 3. SUPPLIER MODEL
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(150), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(150))
    phone = Column(String(30))
    address = Column(Text)


# 4. PRODUCTION LINE MODEL
class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(Integer, primary_key=True, index=True)
    line_name = Column(String(100), nullable=False)
    line_code = Column(String(50), unique=True)
    capacity = Column(Float)
    status = Column(String(50), default="Active")


# 5. BATCH MODEL
class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String(100), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    production_line_id = Column(
        Integer,
        ForeignKey("production_lines.id")
    )
    quantity = Column(Float)
    status = Column(String(50), default="Planned")
    production_date = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    production_line = relationship("ProductionLine")


# 6. RAW MATERIAL MODEL
class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True, index=True)
    material_name = Column(String(150), nullable=False)
    material_code = Column(String(50), unique=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    quantity = Column(Float, default=0)
    unit = Column(String(30))
    reorder_level = Column(Float, default=0)

    supplier = relationship("Supplier")


# 7. MACHINE MODEL
class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(150), nullable=False)
    machine_code = Column(String(50), unique=True)
    production_line_id = Column(
        Integer,
        ForeignKey("production_lines.id")
    )
    status = Column(String(50), default="Operational")
    maintenance_due = Column(DateTime)

    production_line = relationship("ProductionLine")


# 8. PRODUCTION MODEL
class Production(Base):
    __tablename__ = "productions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))
    produced_quantity = Column(Float, default=0)
    rejected_quantity = Column(Float, default=0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    operator_id = Column(Integer, ForeignKey("users.id"))

    batch = relationship("Batch")
    machine = relationship("Machine")
    operator = relationship("User")


# 9. QUALITY TEST MODEL
class QualityTest(Base):
    __tablename__ = "quality_tests"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"))
    test_name = Column(String(150), nullable=False)
    test_result = Column(String(100))
    remarks = Column(Text)
    tested_by = Column(Integer, ForeignKey("users.id"))
    tested_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("Batch")
    tester = relationship("User")


# 10. APPROVAL MODEL
class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approval_status = Column(String(50), default="Pending")
    remarks = Column(Text)
    approved_at = Column(DateTime)

    batch = relationship("Batch")
    approver = relationship("User")


# 11. AUDIT LOG MODEL
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(150), nullable=False)
    module = Column(String(100))
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
