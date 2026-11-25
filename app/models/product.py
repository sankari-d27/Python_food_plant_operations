from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    product_code = Column(String(50), unique=True, nullable=False)

    product_name = Column(String(100), nullable=False)

    description = Column(String(255))

    unit = Column(String(30))

    is_active = Column(Boolean, default=True)