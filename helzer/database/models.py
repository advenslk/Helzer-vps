from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class VPS(Base):
    __tablename__ = "vps"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(64))
    container_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    host_port: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending")
    cpu_cores: Mapped[int] = mapped_column(Integer)
    ram_mb: Mapped[int] = mapped_column(Integer)
    disk_gb: Mapped[int] = mapped_column(Integer)
    image: Mapped[str] = mapped_column(String(128), default="ubuntu:24.04")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
