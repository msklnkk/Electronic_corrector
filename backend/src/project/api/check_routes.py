from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import CheckNotFound, CheckAlreadyExists
from project.schemas.check import CheckCreate, CheckSchema

from project.api.depends import database, check_repo, get_current_user, check_for_admin_access
from project.schemas.user import UserSchema

check_routes = APIRouter()

@check_routes.get(
    "/all_checks",
    response_model=list[CheckSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_all_checks() -> list[CheckSchema]:
    async with database.session() as session:
        all_checks = await check_repo.get_all_checks(session=session)
    return all_checks

@check_routes.get(
    "/check/{check_id}",
    response_model=CheckSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_check_by_id(check_id: int) -> CheckSchema:
    async with database.session() as session:
        check = await check_repo.get_check_by_id(session=session, check_id=check_id)
    return check

@check_routes.get(
    "/checks/document/{document_id}",
    response_model=list[CheckSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_checks_by_document_id(document_id: int) -> list[CheckSchema]:
    async with database.session() as session:
        checks = await check_repo.get_checks_by_document_id(session=session, document_id=document_id)
        return [CheckSchema.model_validate(obj=check) for check in checks]

@check_routes.get(
    "/checks/standard/{standart_id}",
    response_model=list[CheckSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_checks_by_standart_id(standart_id: int) -> list[CheckSchema]:
    async with database.session() as session:
        checks = await check_repo.get_checks_by_standart_id(session=session, standart_id=standart_id)
        return [CheckSchema.model_validate(obj=check) for check in checks]

@check_routes.post(
    "/add_check",
    response_model=CheckSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_check(
    check_dto: CheckCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> CheckSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            new_check = await check_repo.create_check(session=session, check=check_dto)
    except CheckAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_check

@check_routes.put(
    "/update_check/{check_id}",
    response_model=CheckSchema,
    status_code=status.HTTP_200_OK,
)
async def update_check(
    check_id: int,
    check_dto: CheckCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> CheckSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            updated_check = await check_repo.update_check(
                session=session,
                check_id=check_id,
                check=check_dto,
            )
    except CheckNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except CheckAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return updated_check

@check_routes.delete(
    "/delete_check/{check_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_check(
    check_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            await check_repo.delete_check(session=session, check_id=check_id)
    except CheckNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)