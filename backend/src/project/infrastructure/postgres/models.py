from decimal import Decimal

from sqlalchemy import String, ForeignKey, Integer, DateTime, \
    Boolean, Text, Date, Numeric
from datetime import datetime, date

from sqlalchemy.orm import Mapped, mapped_column, relationship
from project.infrastructure.postgres.database import Base


class Users(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "Пользователи"}

    user_id: Mapped[int] = mapped_column(primary_key=True, comment="Идентификатор")
    first_name: Mapped[str] = mapped_column(String, nullable=False, comment="Имя")
    surname_name: Mapped[str] = mapped_column(String, nullable=False, comment="Фамилия")
    patronomic_name: Mapped[str] = mapped_column(String, nullable=False, comment="Отчество")

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, comment="Почта")
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, comment="Логин")
    password: Mapped[str] = mapped_column(String, nullable=False, comment="Пароль")

    role: Mapped[str] = mapped_column(String, nullable=False, comment="Роль")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    tg_username: Mapped[str] = mapped_column(unique=True, nullable=True, comment="Telegram:")
    is_tg_subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    theme: Mapped[str] = mapped_column(String(10), nullable=False, default="light")
    is_push_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    documents: Mapped[list['Document']] = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[list['Review']] = relationship("Review", back_populates="user", cascade="all, delete-orphan")


class Documents(Base):
    __tablename__ = "documents"
    __table_args__ = {"comment": "Документы"}

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    filename: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    filepath: Mapped[str] = mapped_column(String, nullable=False)

    upload_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="Дата и время загрузки")

    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    is_example: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    size: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.status_id"), nullable=False)
    report_pdf_path: Mapped[str] = mapped_column(String(500), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, comment="Соответствие стандарту (0-100)")
    analysis_time: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    mistakes: Mapped[list["Mistake"]] = relationship(
        "Mistake", back_populates="document",
        cascade="all, delete-orphan", lazy="selectin"
    )
    status: Mapped["Status"] = relationship("Status", back_populates="documents")
    user: Mapped["User"] = relationship("User", back_populates="documents")
    mistakes: Mapped[list["Mistake"]] = relationship("Mistake", back_populates="document", cascade="all, delete-orphan", lazy="selectin")
    checks: Mapped[list["Check"]] = relationship("Check", back_populates="document", cascade="all, delete-orphan")


class Standart(Base):
    __tablename__ = "standart"

    standart_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    checks: Mapped[list["Check"]] = relationship("Check", back_populates="standard", cascade="all, delete-orphan")

class Check(Base):
    __tablename__ = "check"

    check_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.document_id"), nullable=False)
    standart_id: Mapped[int] = mapped_column(ForeignKey("standart.standart_id"), nullable=False)

    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    result: Mapped[str] = mapped_column(String, nullable=True) # success / warnings / failed

    report_path: Mapped[str] = mapped_column(String, nullable=True)

    document: Mapped["Documents"] = relationship("Documents", back_populates="checks")
    standard: Mapped["Standart"] = relationship("Standart", back_populates="checks")
    reports: Mapped[list["Reports"]] = relationship("Reports", back_populates="check", cascade="all, delete-orphan")


class Reports(Base):
    __tablename__ = "reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("check.check_id"), nullable=False)

    report_json: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    check: Mapped["Check"] = relationship("Check", back_populates="reports")

class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = {"comment": "Отзывы"}

    review_id: Mapped[int] = mapped_column(primary_key=True, comment="Индентификатор")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Связь с User")

    rating: Mapped[int] = mapped_column(Integer, nullable=False, comment="Оценка от 1 до 5 звезд")
    review_text: Mapped[str] = mapped_column(Text, nullable=True, comment="Текст отзыва")
    created_at: Mapped[date] = mapped_column(Date, nullable=False, comment="Время отправки отзыва")

    user: Mapped["Users"] = relationship("User", back_populates="reviews")


class Status(Base):
    __tablename__ = "statuses"
    __table_args__ = {"comment": "Статусы"}

    status_id: Mapped[int] = mapped_column(primary_key=True, comment="Индентификатор")
    status_name: Mapped[str] = mapped_column(String(60), nullable=False)
    documents: Mapped[list["Documents"]] = relationship("Document", back_populates="status", lazy="selectin")


class MistakeType(Base):
    __tablename__ = "mistake_types"
    __table_args__ = {"comment": "Типы ошибок"}

    mistake_type_id: Mapped[int] = mapped_column(primary_key=True, comment="Индентификатор")
    mistake_type_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    mistakes: Mapped[list["Mistake"]] = relationship(
        "Mistake", back_populates="mistake_type",
        cascade="all, delete-orphan", lazy="selectin"
    )


class Mistake(Base):
    __tablename__ = "mistakes"
    __table_args__ = {"comment": "Ошибки"}

    mistake_id: Mapped[int] = mapped_column(primary_key=True, comment="Индентификатор")
    mistake_type_id: Mapped[int] = mapped_column(
        ForeignKey("mistake_types.mistake_type_id"),
        nullable=True,
        comment="Связь с Mistake_Type"
    )

    description: Mapped[str] = mapped_column(Text, nullable=False, comment="Описание ошибки")
    critical_status: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.document_id"),
        nullable=False,
        comment="Связь с Document"
    )

    document: Mapped["Documents"] = relationship("Document", back_populates="mistakes", lazy="selectin")
    mistake_type: Mapped["MistakeType"] = relationship("MistakeType", back_populates="mistakes")