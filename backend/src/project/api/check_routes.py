# backend/src/project/api/check_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone


from project.core.exceptions import CheckNotFound, CheckAlreadyExists
from project.schemas.check import CheckCreate, CheckSchema

from project.api.depends import database, check_repo, get_current_user, check_for_admin_access
from project.schemas.user import UserSchema

check_routes = APIRouter()


def utc_now_naive() -> datetime:
    """UTC время как naive datetime (для TIMESTAMP WITHOUT TIME ZONE)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@check_routes.get(
    "/checks",
    response_model=list[CheckSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_checks(current_user: UserSchema = Depends(get_current_user)) -> list[CheckSchema]:
    async with database.session() as session:
        try:
            if current_user.is_admin:
                all_checks = await check_repo.get_all_checks(session=session)
            else:
                all_checks = await check_repo.get_checks_by_user_id(session=session, user_id=current_user.user_id)
        except CheckNotFound as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
        return all_checks

@check_routes.get(
    "/checks/{id}",
    response_model=CheckSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_check_by_id(id: int) -> CheckSchema:
    async with database.session() as session:
        check = await check_repo.get_check_by_id(session=session, check_id=id)
    return check

@check_routes.get(
    "/checks/document/{id}",
    response_model=list[CheckSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_checks_by_document_id(id: int) -> list[CheckSchema]:
    async with database.session() as session:
        checks = await check_repo.get_checks_by_document_id(session=session, document_id=id)
        return [CheckSchema.model_validate(obj=check) for check in checks]

@check_routes.get(
    "/checks/standard/{id}",
    response_model=list[CheckSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_checks_by_standart_id(id: int) -> list[CheckSchema]:
    async with database.session() as session:
        checks = await check_repo.get_checks_by_standart_id(session=session, standart_id=id)
        return [CheckSchema.model_validate(obj=check) for check in checks]

@check_routes.post(
    "/checks",
    response_model=CheckSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_for_admin_access)]
)
async def add_check(
    check_dto: CheckCreate,
) -> CheckSchema:
    try:
        if (check_dto.checked_at is None
            or getattr(check_dto.checked_at, "tzinfo", None) is not None
        ):
            check_dto.checked_at = utc_now_naive()

        async with database.session() as session:
            new_check = await check_repo.create_check(session=session, check=check_dto)
    except CheckAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_check

@check_routes.put(
    "/checks/{id}",
    response_model=CheckSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)]
)
async def update_check(
    id: int,
    check_dto: CheckCreate,
) -> CheckSchema:
    try:
        if (check_dto.checked_at is None
            or getattr(check_dto.checked_at, "tzinfo", None) is not None
        ):
            check_dto.checked_at = utc_now_naive()

        async with database.session() as session:
            updated_check = await check_repo.update_check(
                session=session,
                check_id=id,
                check=check_dto,
            )
    except CheckNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except CheckAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return updated_check

@check_routes.delete(
    "/checks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_for_admin_access)]
)
async def delete_check(
    id: int,
) -> None:
    try:
        async with database.session() as session:
            await check_repo.delete_check(session=session, check_id=id)
    except CheckNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)