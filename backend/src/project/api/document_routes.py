from fastapi import APIRouter, Depends, HTTPException, status

from project.api.depends import (
    database,
    get_current_user,
    document_repo, check_for_admin_access,
)
from project.schemas.documents import DocumentCreate, DocumentSchema, DocumentUpdate
from project.core.exceptions import DocumentNotFound

document_routes = APIRouter()


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
    response_model=list[dict],  # Предположим, ошибки возвращаются как список словарей
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

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
