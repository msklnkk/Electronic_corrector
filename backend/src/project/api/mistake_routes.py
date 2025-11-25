from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import MistakeNotFound, MistakeAlreadyExists, DocumentNotFound
from project.schemas.mistake import MistakeCreate, MistakeSchema

from project.api.depends import database, mistake_repo, get_current_user, check_for_admin_access
from project.api.depends import document_repo
from project.schemas.user import UserSchema

mistake_routes = APIRouter()


@mistake_routes.get(
    "/all_mistakes",
    response_model=list[MistakeSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_all_mistakes() -> list[MistakeSchema]:
    async with database.session() as session:
        all_mistakes = await mistake_repo.get_all_mistakes(session=session)
    return all_mistakes

@mistake_routes.get(
    "/mistake/{mistake_id}",
    response_model=MistakeSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_mistake_by_id(
    mistake_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> MistakeSchema:
    try:
        async with database.session() as session:
            mistake = await mistake_repo.get_mistake_by_id(session=session, mistake_id=mistake_id)
    except MistakeNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    try:
        async with database.session() as session:
            document = await document_repo.get_document_by_id(session=session, document_id=mistake.document_id)
    except DocumentNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    if not current_user.is_admin and document.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")


    return mistake

@mistake_routes.get(
    "/mistakes/document/{document_id}",
    response_model=list[MistakeSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_mistakes_by_document_id(
    document_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> list[MistakeSchema]:
    try:
        async with database.session() as session:
            document = await document_repo.get_document_by_id(session=session, document_id=document_id)
    except DocumentNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    if not current_user.is_admin and document.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    async with database.session() as session:
        mistakes = await mistake_repo.get_mistakes_by_document_id(session=session, document_id=document_id)
        return mistakes

@mistake_routes.get(
    "/mistakes/type/{mistake_type_id}",
    response_model=list[MistakeSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_mistakes_by_mistake_type_id(
    mistake_type_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> list[MistakeSchema]:
    async with database.session() as session:
        mistakes = await mistake_repo.get_mistakes_by_mistake_type_id(session=session, mistake_type_id=mistake_type_id)

    # Админ получает всё
    if current_user.is_admin:
        return mistakes

    # Для пользователя — фильтруем по владельцу документа
    filtered: list[MistakeSchema] = []
    async with database.session() as session:
        for m in mistakes:
            try:
                doc = await document_repo.get_document_by_id(session=session, document_id=m.document_id)
            except DocumentNotFound:
                # если документ не найден — пропускаем такую запись
                continue
            if doc.user_id == current_user.user_id:
                filtered.append(m)

    return filtered

@mistake_routes.post(
    "/add_mistake",
    response_model=MistakeSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_for_admin_access)],
)
async def add_mistake(
    mistake_dto: MistakeCreate,
) -> MistakeSchema:
    try:
        async with database.session() as session:
            new_mistake = await mistake_repo.create_mistake(session=session, mistake=mistake_dto)
    except MistakeAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_mistake

@mistake_routes.put(
    "/update_mistake/{mistake_id}",
    response_model=MistakeSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def update_mistake(
    mistake_id: int,
    mistake_dto: MistakeCreate,
) -> MistakeSchema:
    try:
        async with database.session() as session:
            updated_mistake = await mistake_repo.update_mistake(
                session=session,
                mistake_id=mistake_id,
                mistake=mistake_dto,
            )
    except MistakeNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except MistakeAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return updated_mistake

@mistake_routes.delete(
    "/delete_mistake/{mistake_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_for_admin_access)],
)
async def delete_mistake(
    mistake_id: int,
) -> None:
    try:
        async with database.session() as session:
            await mistake_repo.delete_mistake(session=session, mistake_id=mistake_id)
    except MistakeNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)