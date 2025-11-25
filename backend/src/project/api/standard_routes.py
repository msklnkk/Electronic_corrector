from fastapi import APIRouter, Depends, HTTPException, status

from project.api.depends import (
    database,
    get_current_user,
    standard_repo,
    check_for_admin_access,
)
from project.schemas.standart import StandardCreate, StandardSchema
from project.core.exceptions import StandardNotFound, StandardAlreadyExists

standard_routes = APIRouter()


@standard_routes.get(
    "/all_standards",
    response_model=list[StandardSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_all_standards() -> list[StandardSchema]:
    async with database.session() as session:
        all_standards = await standard_repo.get_all_standards(session=session)
    return all_standards



@standard_routes.get(
    "/standard/{standart_id}",
    response_model=StandardSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_standard_by_id(standart_id: int) -> StandardSchema:
    try:
        async with database.session() as session:
            standard = await standard_repo.get_standard_by_id(
                session=session,
                standart_id=standart_id,
            )
    except StandardNotFound as error:
        raise HTTPException(status_code=404, detail=error.message)

    return standard



@standard_routes.get(
    "/standard_by_name_version",
    response_model=StandardSchema | None,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_standard_by_name_version(
    name: str,
    version: str | None = None,
):

    async with database.session() as session:
        standard = await standard_repo.get_standard_by_name_version(
            session=session,
            name=name,
            version=version,
        )
        if standard:
            return StandardSchema.model_validate(standard)
        return None



@standard_routes.post(
    "/add_standard",
    response_model=StandardSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_for_admin_access)],
)
async def add_standard(
    standard_dto: StandardCreate,
) -> StandardSchema:
    try:
        async with database.session() as session:
            new_standard = await standard_repo.create_standard(
                session=session,
                standard=standard_dto
            )
    except StandardAlreadyExists as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.message
        )

    return new_standard



@standard_routes.put(
    "/update_standard/{standart_id}",
    response_model=StandardSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def update_standard(
    standart_id: int,
    standard_dto: StandardCreate,
) -> StandardSchema:
    try:
        async with database.session() as session:
            updated_standard = await standard_repo.update_standard(
                session=session,
                standart_id=standart_id,
                standard=standard_dto,
            )
    except StandardNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.message
        )
    except StandardAlreadyExists as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.message
        )

    return updated_standard


@standard_routes.delete(
    "/delete_standard/{standart_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_for_admin_access)],
)
async def delete_standard(
    standart_id: int,
) -> None:
    try:
        async with database.session() as session:
            await standard_repo.delete_standard(
                session=session,
                standart_id=standart_id,
            )
    except StandardNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.message
        )
