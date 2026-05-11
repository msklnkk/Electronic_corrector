# backend/src/project/api/document_routes.py

import io
import time
import uuid

from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Request,
)

from project.api.depends import (
    database,
    get_current_user,
    document_repo,
    check_for_admin_access,
)

from project.schemas.documents import (
    DocumentCreate,
    DocumentSchema,
    DocumentUpdate,
    FileUploadResponse,
)

from project.core.exceptions import DocumentNotFound

from project.infrastructure.kafka.publishers import (
    publish_status,
)

from project.storage.minio_client import (
    client,
    BUCKET_NAME,
)

document_routes = APIRouter()


@document_routes.get(
    "/documents",
    response_model=list[DocumentSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)]
)
async def get_all_documents() -> list[DocumentSchema]:

    async with database.session() as session:
        documents = await document_repo.get_all_documents(
            session
        )

    return documents


@document_routes.get(
    "/documents/user/{id}",
    response_model=list[DocumentSchema],
    status_code=status.HTTP_200_OK,
)
async def get_documents_by_user(
    id: int,
    current_user=Depends(get_current_user),
) -> list[DocumentSchema]:

    if (
        not current_user.is_admin
        and current_user.user_id != id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа"
        )

    async with database.session() as session:

        documents = await (
            document_repo.get_documents_by_user(
                session,
                id
            )
        )

    return documents


@document_routes.get(
    "/documents/full-info/{id}",
    response_model=DocumentSchema,
    status_code=status.HTTP_200_OK,
)
async def get_document_full_info(
    id: int,
    current_user=Depends(get_current_user),
) -> DocumentSchema:

    async with database.session() as session:

        document = await (
            document_repo.get_document_by_id(
                session,
                id
            )
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )

        if (
            not current_user.is_admin
            and document.user_id != current_user.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа"
            )

        full_info = await (
            document_repo.get_document_full_info(
                session,
                id
            )
        )

    return full_info


@document_routes.post(
    "/documents",
    response_model=DocumentSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_document(
    document_dto: DocumentCreate,
    current_user=Depends(get_current_user),
) -> DocumentSchema:

    document_dto.user_id = current_user.user_id

    async with database.session() as session:

        new_document = await (
            document_repo.create_document(
                session,
                document_dto
            )
        )

    return new_document


@document_routes.put(
    "/documents/{id}",
    response_model=DocumentSchema,
    status_code=status.HTTP_200_OK,
)
async def update_document(
    id: int,
    document_dto: DocumentUpdate,
    current_user=Depends(get_current_user),
) -> DocumentSchema:

    async with database.session() as session:

        document = await (
            document_repo.get_document_by_id(
                session,
                id
            )
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )

        if (
            not current_user.is_admin
            and document.user_id != current_user.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа"
            )

        try:
            updated_document = await (
                document_repo.update_document(
                    session,
                    id,
                    document_dto
                )
            )

        except DocumentNotFound as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error.message
            )

    return updated_document


@document_routes.delete(
    "/documents/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    id: int,
    current_user=Depends(get_current_user),
) -> None:

    async with database.session() as session:

        document = await (
            document_repo.get_document_by_id(
                session,
                id
            )
        )

        if document is None:
            raise HTTPException(
                404,
                "Документ не найден"
            )

        if (
            not current_user.is_admin
            and document.user_id != current_user.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа"
            )

        try:
            await document_repo.delete_document(
                session,
                id
            )

        except DocumentNotFound as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error.message
            )


@document_routes.post(
    "/documents/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document_file(
    request: Request,
    file: UploadFile = File(...),
    doc_type: str = Form("document"),
    is_example: bool = Form(False),
    current_user=Depends(get_current_user)
) -> FileUploadResponse:

    try:
        kafka_producer = getattr(
            request.app.state,
            "kafka_producer",
            None
        )

        print("=== НАЧАЛО ЗАГРУЗКИ ===")
        print(f"Файл: {file.filename}")
        print(f"Пользователь: {current_user.user_id}")

        file_extension = (
            Path(file.filename)
            .suffix
            .lower()
        )

        allowed_types = [
            ".pdf",
            ".doc",
            ".docx",
            ".txt"
        ]

        if file_extension not in allowed_types:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Недопустимый тип файла"
                )
            )

        unique_filename = (
            f"{int(time.time())}_"
            f"{uuid.uuid4().hex[:8]}_"
            f"{file.filename}"
        )

        content = await file.read()

        file_size = len(content)

        client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=unique_filename,
            data=io.BytesIO(content),
            length=file_size,
            content_type=(
                file.content_type
                or "application/octet-stream"
            ),
        )

        file_path = (
            f"{BUCKET_NAME}/"
            f"{unique_filename}"
        )

        print(
            f"Файл сохранен в MinIO: "
            f"{file_path}"
        )

        document_data = DocumentCreate(
            user_id=current_user.user_id,
            filename=unique_filename,
            filepath=file_path,
            upload_datetime=(
                datetime.now(timezone.utc)
                .replace(tzinfo=None)
            ),
            doc_type=doc_type,
            is_example=is_example,
            size=Decimal(file_size),
            status_id=1,
            report_pdf_path="",
            score=Decimal("0.0"),
            analysis_time=Decimal("0.0")
        )

        async with database.session() as session:

            new_document = await (
                document_repo.create_document(
                    session,
                    document_data
                )
            )

        print(
            f"Документ создан в БД: "
            f"{new_document.document_id}"
        )

        await publish_status(
            kafka_producer=kafka_producer,
            document_id=(
                new_document.document_id
            ),
            status="uploaded",
            message=(
                "Документ успешно загружен"
            ),
        )

        return FileUploadResponse(
            filename=file.filename,
            saved_filename=unique_filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type,
            document_id=(
                new_document.document_id
            ),
            message=(
                "Документ успешно загружен"
            )
        )

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"Ошибка при загрузке: {str(e)}"
        )

        if "unique_filename" in locals():

            try:
                client.remove_object(
                    BUCKET_NAME,
                    unique_filename
                )

            except Exception:
                pass

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                f"Ошибка при загрузке файла: "
                f"{str(e)}"
            )
        )

    finally:
        await file.close()