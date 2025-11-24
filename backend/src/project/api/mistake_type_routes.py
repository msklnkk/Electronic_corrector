from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import MistakeTypeNotFound, MistakeTypeAlreadyExists
from project.schemas.mistake_type import MistakeTypeCreate, MistakeTypeSchema

from project.api.depends import database, mistake_type_repo, get_current_user, check_for_admin_access
from project.schemas.user import UserSchema

mistake_type_routes = APIRouter()

@mistake_type_routes.get(
    "/all_mistake_types",
    response_model=list[MistakeTypeSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_all_mistake_types() -> list[MistakeTypeSchema]:
    async with database.session() as session:
        all_mistake_types = await mistake_type_repo.get_all_mistake_types(session=session)
    return all_mistake_types

@mistake_type_routes.get(
    "/mistake_type/{mistake_type_id}",
    response_model=MistakeTypeSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_mistake_type_by_id(mistake_type_id: int) -> MistakeTypeSchema:
    async with database.session() as session:
        mistake_type = await mistake_type_repo.get_mistake_type_by_id(session=session, mistake_type_id=mistake_type_id)
    return mistake_type

@mistake_type_routes.post(
    "/add_mistake_type",
    response_model=MistakeTypeSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_mistake_type(
    mistake_type_dto: MistakeTypeCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> MistakeTypeSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            new_mistake_type = await mistake_type_repo.create_mistake_type(session=session, mistake_type=mistake_type_dto)
    except MistakeTypeAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_mistake_type

@mistake_type_routes.put(
    "/update_mistake_type/{mistake_type_id}",
    response_model=MistakeTypeSchema,
    status_code=status.HTTP_200_OK,
)
async def update_mistake_type(
    mistake_type_id: int,
    mistake_type_dto: MistakeTypeCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> MistakeTypeSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            updated_mistake_type = await mistake_type_repo.update_mistake_type(
                session=session,
                mistake_type_id=mistake_type_id,
                mistake_type=mistake_type_dto,
            )
    except MistakeTypeNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except MistakeTypeAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return updated_mistake_type

@mistake_type_routes.delete(
    "/delete_mistake_type/{mistake_type_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_mistake_type(
    mistake_type_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            await mistake_type_repo.delete_mistake_type(session=session, mistake_type_id=mistake_type_id)
    except MistakeTypeNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)