import json
from datetime import date, time
from decimal import Decimal
from sqlalchemy import MetaData, ForeignKey, BigInteger, Boolean, Integer, Date, Time, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from typing import Literal, List



class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s", #индексы
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s", #проверки?
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "Пользователи"}

    id: Mapped[int] = mapped_column(primary_key=True, comment="Идентификатор")
    first_name: Mapped[str] = mapped_column(nullable=False, comment="Имя")
    surname_name: Mapped[str] = mapped_column(nullable=True, comment="Фамилия")
    patronomic_name: Mapped[str] = mapped_column(nullable=True, comment="Отчество")
    user_name: Mapped[str] = mapped_column(unique=True, nullable=False, comment="Логин")
    password: Mapped[str] = mapped_column(nullable=False, comment="Пароль")
    tg_username: Mapped[str] = mapped_column(unique=True, nullable=True, comment="Telegram:")
    is_tg_subscribed: Mapped[bool] = mapped_column(
       Boolean,
       default=False,
       nullable=False,
       comment="Проверка подписки на Telegram"
    )
    is_admin: Mapped[bool] = mapped_column(
       Boolean,
       default=False,
       nullable=False,
       comment="Проверка на админа"
   )
    theme: Mapped[Literal["dark", "light"]] = mapped_column(
    nullable=False,
    comment="Тема приложения dark/light"
   )
    notification_push: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Уведомления в браузере on/off"
    )
    documents: Mapped[list['Document']] = relationship("Document", back_populates="user")
    reviews: Mapped[list['Review']] = relationship("Review", back_populates="user")

class Review(Base):
    __tablename__= "reviews"
    __table_args__= {"comment": "Отзывы"}
    
    id:Mapped[int] = mapped_column(primary_key=True,comment="Индентификатор")
    user_id: Mapped[int] = mapped_column(
       Integer,
       ForeignKey("users.id",ondelete="CASCADE"),
       nullable=False,
       comment="Связь с User"
   )
    mark: Mapped[int] = mapped_column(nullable=False, comment="Оценка от 1 до 5 звезд")
    review_text: Mapped[str] = mapped_column(nullable=True,comment="Текст отзыва")
    created_at: Mapped[date] = mapped_column(
       Date,
       nullable=False,
       comment="Время отправки отзыва"
    )
    user: Mapped["User"] = relationship("User",back_populates="reviews")
    
class Status(Base):
    __tablename__= "statuses"
    __table_args__={"comment": "Статусы"}
    
    id: Mapped[int] = mapped_column(primary_key=True,comment="Индентификатор")
    status_name: Mapped[Literal["Загружен", "Анализируется","Проверен","Отправлен на доработку","Идеален"]] = mapped_column(
    nullable=False,
    comment="Наименование статуса"
    )
    documents: Mapped[List["Document"]] = relationship("Document",back_populates="status",lazy="selectin")
class Document(Base):
    __tablename__= "documents"
    __table_args__= {"comment": "Документы"}
    
    id: Mapped[int] = mapped_column(primary_key=True, comment="Идентификатор")
    file_name: Mapped[str] = mapped_column (unique=True, nullable="False",comment = "Наименование документа")
    upload_date: Mapped[date] = mapped_column(
       Date,
       nullable="False",
       comment="Дата загрузки"
    )
    upload_time: Mapped[date] = mapped_column(
        Time,
        nullable="False",
        comment="Время загрузки"
    )
    size: Mapped[Decimal] = mapped_column(
        Numeric (precision=5, decimal_return_scale = 2),
        nullable="False",
        comment="Размер файла"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable="False",
        comment="Связь с User"
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("statuses.id"),
        nullable = "False",
        comment= "Связь с Status"
    )
    report_pdf_path: Mapped[str] = mapped_column(nullable=False,comment="URL на отчет")
    score: Mapped[Decimal] = mapped_column(
        Numeric (precision=5, scale=2),
        nullable=False,
        comment="Соответсвие ГОСТу"
    )
    analysis_time: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
        comment="Время анализа"
    )
    mistakes: Mapped[List["Mistake"]] = relationship("Mistake",back_populates="document",cascade="all, delete-orphan",lazy="selectin")
    status: Mapped["Status"] = relationship("Status", back_populates="documents")  
    user: Mapped["User"] = relationship("User",back_populates="documents")
                                        
                                        
class MistakeType(Base):
   __tablename__ = "mistake_types"
   __table_args__={"comment":"Типы ошибок"}
   id: Mapped[int] = mapped_column(primary_key=True,comment="Индентификатор")
   mistake_type_name: Mapped[Literal[
       "Шрифт", 
       "Отступы",
       "Структура",
       "Подписи иллюстраций",
       "Таблицы",
       "Ссылки",
       "Нумерация",
       "Абзацы",
       "Заголовки",
       "Формулы",
       "Списки",
       "Колонтитулы",
       "Приложения",
       "Титульный лист",
       "Общий формат"]] = mapped_column(unique=True, nullable=False, comment="Наименование типа ошибки")
   mistakes: Mapped[List["Mistake"]] = relationship("Mistake",back_populates="mistake_type",cascade="all, delete-orphan",lazy="selectin")

class Mistake(Base):
   __tablename__ = "mistakes"
   __table_args__={"comment": "Ошибки"}
   id: Mapped[int]=mapped_column(primary_key=True,comment="Индентификатор")
   mistake_type_id:Mapped[int] = mapped_column(
        ForeignKey("mistake_types.id"),
        nullable=True,
        comment="Связь с Mistake_Type"
    )
   description: Mapped[str] = mapped_column(nullable=False,comment="Описание ошибки")
   critical_status: Mapped[Literal["Критично","Замечание"]] = mapped_column (nullable=False,comment="Статус важности")
   document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        comment="Связь с Document"
    )
   document: Mapped["Document"] = relationship("Document", back_populates="mistakes", lazy="selectin")
   mistake_type = relationship("MistakeType", back_populates="mistakes")
