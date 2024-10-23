from typing import List
import uuid
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pydantic import BaseModel, Field


class Base(DeclarativeBase): ...


class Orders(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str]
    payment_status: Mapped[str] = mapped_column(default="pending")


class OrdersSchema(BaseModel):
    order_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    email: str
    payment_status: str = "pending"
