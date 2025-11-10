from sqlalchemy import String, ForeignKey, Integer, DateTime, \
    Boolean, Text, false
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from project.infrastructure.postgres.database import Base


class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=false())


class Documents(Base):
    __tablename__ = "documents"

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    is_example: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Standart(Base):
    __tablename__ = "standart"

    standart_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Check(Base):
    __tablename__ = "check"

    check_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.document_id"), nullable=False)
    standart_id: Mapped[int] = mapped_column(ForeignKey("standart.standart_id"), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    result: Mapped[str] = mapped_column(String, nullable=True) # success / warnings / failed
    report_path: Mapped[str] = mapped_column(String, nullable=True)


class Reports(Base):
    __tablename__ = "reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("check.check_id"), nullable=False)
    report_json: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)