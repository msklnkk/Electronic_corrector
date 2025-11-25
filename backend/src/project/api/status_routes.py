from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import StatusNotFound, StatusAlreadyExists
from project.schemas.status import StatusCreate, StatusSchema

from project.api.depends import database, status_repo, get_current_user, check_for_admin_access
from project.schemas.user import UserSchema

status_routes = APIRouter()

@status_routes.get(
    "/all_statuses",
    response_model=list[StatusSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_all_statuses() -> list[StatusSchema]:
    async with database.session() as session:
        all_statuses = await status_repo.get_all_statuses(session=session)
    return all_statuses

@status_routes.get(
    "/status/{status_id}",
    response_model=StatusSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_status_by_id(status_id: int) -> StatusSchema:
    async with database.session() as session:
        status = await status_repo.get_status_by_id(session=session, status_id=status_id)
    return status

@status_routes.post(
    "/add_status",
    response_model=StatusSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_status(
    status_dto: StatusCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> StatusSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            new_status = await status_repo.create_status(session=session, status=status_dto)
    except StatusAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_status

@status_routes.put(
    "/update_status/{status_id}",
    response_model=StatusSchema,
    status_code=status.HTTP_200_OK,
)
async def update_status(
    status_id: int,
    status_dto: StatusCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> StatusSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            updated_status = await status_repo.update_status(
                session=session,
                status_id=status_id,
                status=status_dto,
            )
    except StatusNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except StatusAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return updated_status

@status_routes.delete(
    "/delete_status/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_status(
    status_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            await status_repo.delete_status(session=session, status_id=status_id)
    except StatusNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)