from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
import shutil
import os
from pathlib import Path
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from project.api.depends import (
    database,
    get_current_user,
    document_repo,
    check_for_admin_access,
    # require_tg_subscription,  # ← ОТКЛЮЧАЕМ ПРОВЕРКУ ПОДПИСКИ
)
from project.schemas.documents import (
    DocumentCreate,
    DocumentSchema,
    DocumentUpdate,
    FileUploadResponse,
    FileInfo
)
from project.core.exceptions import DocumentNotFound
from project.core.config import settings

# УБИРАЕМ require_tg_subscription из зависимостей роутера
# Было: dependencies=[Depends(require_tg_subscription)]
document_routes = APIRouter()  # ← теперь без проверки подписки


@document_routes.get(
    "/all_documents",
    response_model=list[DocumentSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)]
)
async def get_all_documents() -> list[DocumentSchema]:
    async with database.session() as session:
        documents = await document_repo.get_all_documents(session)
    return documents


@document_routes.get(
    "/documents_by_user/{user_id}",
    response_model=list[DocumentSchema],
    status_code=status.HTTP_200_OK,
)
async def get_documents_by_user(
        user_id: int,
        current_user=Depends(get_current_user),
) -> list[DocumentSchema]:
    if not current_user.is_admin and current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    async with database.session() as session:
        documents = await document_repo.get_documents_by_user(session, user_id)
    return documents


@document_routes.get(
    "/status/{status_id}",
    response_model=list[DocumentSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)]
)
async def get_documents_by_status(
        status_id: int,
) -> list[DocumentSchema]:
    async with database.session() as session:
        documents = await document_repo.get_documents_by_status(session, status_id)
    return documents


@document_routes.get(
    "/mistakes/{document_id}",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
)
async def get_document_mistakes(
        document_id: int,
        current_user=Depends(get_current_user),
) -> list[dict]:
    async with database.session() as session:
        document = await document_repo.get_document_by_id(session, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

        if not current_user.is_admin and document.user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
        mistakes = await document_repo.get_document_mistakes(session, document_id)
    return mistakes


@document_routes.get(
    "/full-info/{document_id}",
    response_model=DocumentSchema,
    status_code=status.HTTP_200_OK,
)
async def get_document_full_info(
        document_id: int,
        current_user=Depends(get_current_user),
) -> DocumentSchema:
    async with database.session() as session:
        document = await document_repo.get_document_by_id(session, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

        if not current_user.is_admin and document.user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
        full_info = await document_repo.get_document_full_info(session, document_id)
    return full_info


@document_routes.post(
    "/add_document",
    response_model=DocumentSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_document(
        document_dto: DocumentCreate,
        current_user=Depends(get_current_user),
) -> DocumentSchema:
    document_dto.user_id = current_user.user_id

    async with database.session() as session:
        new_document = await document_repo.create_document(session, document_dto)
    return new_document


@document_routes.put(
    "/update_document/{document_id}",
    response_model=DocumentSchema,
    status_code=status.HTTP_200_OK,
)
async def update_document(
        document_id: int,
        document_dto: DocumentUpdate,
        current_user=Depends(get_current_user),
) -> DocumentSchema:
    async with database.session() as session:
        document = await document_repo.get_document_by_id(session, document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

        if not current_user.is_admin and document.user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORБIDDEN, detail="Нет доступа")

        try:
            updated_document = await document_repo.update_document(session, document_id, document_dto)
        except DocumentNotFound as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    return updated_document


@document_routes.delete(
    "/delete_document/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
        document_id: int,
        current_user=Depends(get_current_user),
) -> None:
    async with database.session() as session:
        document = await document_repo.get_document_by_id(session, document_id)
        if document is None:
            raise HTTPException(404, "Документ не найден")

        if not current_user.is_admin and document.user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

        try:
            await document_repo.delete_document(session, document_id)
        except DocumentNotFound as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)


@document_routes.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document_file(
        file: UploadFile = File(...),
        doc_type: str = Form("document"),
        is_example: bool = Form(False),
        current_user=Depends(get_current_user)
) -> FileUploadResponse:
    """
    Загрузка документа через проводник
    """
    try:
        print(f"=== НАЧАЛО ЗАГРУЗКИ ===")
        print(f"Файл: {file.filename}")
        print(f"Пользователь: {current_user.user_id}")

        # Проверяем тип файла
        file_extension = Path(file.filename).suffix.lower()
        allowed_types = [".pdf", ".doc", ".docx", ".txt"]

        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый тип файла. Разрешены: {', '.join(allowed_types)}"
            )

        # Создаем директорию если нет
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        # Генерируем уникальное имя файла
        import uuid
        import time
        unique_filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = upload_dir / unique_filename

        # Сохраняем файл
        content = await file.read()
        file_size = len(content)

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        print(f"Файл сохранен: {file_path}")

        # Создаем запись в БД
        document_data = DocumentCreate(
            user_id=current_user.user_id,
            filename=unique_filename,
            filepath=str(file_path),
            upload_datetime=datetime.utcnow(),
            doc_type=doc_type,
            is_example=is_example,
            size=Decimal(file_size),
            status_id=1,
            report_pdf_path="",
            score=Decimal('0.0'),
            analysis_time=Decimal('0.0')
        )

        async with database.session() as session:
            new_document = await document_repo.create_document(session, document_data)

        print(f"Документ создан в БД: {new_document.document_id}")

        return FileUploadResponse(
            filename=file.filename,
            saved_filename=unique_filename,
            file_path=str(file_path),
            file_size=file_size,
            content_type=file.content_type,
            document_id=new_document.document_id,
            message="Документ успешно загружен"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при загрузке: {str(e)}")
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )
    finally:
        await file.close()

@document_routes.post("/{document_id}/check-gost")
async def check_document_gost(
    document_id: int,
    current_user=Depends(get_current_user),
):
    """Запустить проверку ГОСТ для документа"""
    async with database.session() as session:
        # Получаем документ асинхронно через репозиторий
        document = await document_repo.get_document_by_id(session, document_id)
        
        if not document:
            raise HTTPException(404, "Документ не найден")
        
        # Проверяем права доступа
        if not current_user.is_admin and document.user_id != current_user.user_id:
            raise HTTPException(403, "Нет доступа к документу")
        
        # Создаем сервис и запускаем проверку
        # Предполагается, что GostCheckService принимает сессию в конструкторе
        service = GostCheckService(session)
        check_id = await service.start_gost_check(document_id)
        
        return {"message": "Проверка ГОСТ запущена", "check_id": check_id}