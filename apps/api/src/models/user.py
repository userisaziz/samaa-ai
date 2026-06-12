import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    BRAND_ADMIN = "BRAND_ADMIN"
    STORE_MANAGER = "STORE_MANAGER"
    SALESPERSON = "SALESPERSON"
    OPERATOR = "OPERATOR"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("brands.id"), nullable=True
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("stores.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    brand: Mapped["Brand | None"] = relationship("Brand", back_populates="users")
    store: Mapped["Store | None"] = relationship("Store", back_populates="users")
    role_corrections: Mapped[list["SpeakerRoleCorrection"]] = relationship(
        "SpeakerRoleCorrection", back_populates="user", cascade="all, delete-orphan"
    )
