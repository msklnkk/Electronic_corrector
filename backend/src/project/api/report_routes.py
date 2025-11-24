from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import ReportNotFound, ReportAlreadyExists
from project.schemas.reports import ReportCreate, ReportSchema

from project.api.depends import database, report_repo, get_current_user, check_for_admin_access
from project.schemas.user import UserSchema

report_routes = APIRouter()

@report_routes.get(
    "/all_reports",
    response_model=list[ReportSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_all_reports() -> list[ReportSchema]:
    async with database.session() as session:
        all_reports = await report_repo.get_all_reports(session=session)
    return all_reports

@report_routes.get(
    "/report/{report_id}",
    response_model=ReportSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_report_by_id(report_id: int) -> ReportSchema:
    async with database.session() as session:
        report = await report_repo.get_report_by_id(session=session, report_id=report_id)
    return report

@report_routes.get(
    "/reports/check/{check_id}",
    response_model=list[ReportSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_reports_by_check_id(check_id: int) -> list[ReportSchema]:
    async with database.session() as session:
        reports = await report_repo.get_reports_by_check_id(session=session, check_id=check_id)
        return [ReportSchema.model_validate(obj=report) for report in reports]

@report_routes.post(
    "/add_report",
    response_model=ReportSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_report(
    report_dto: ReportCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> ReportSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            new_report = await report_repo.create_report(session=session, report=report_dto)
    except ReportAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_report

@report_routes.put(
    "/update_report/{report_id}",
    response_model=ReportSchema,
    status_code=status.HTTP_200_OK,
)
async def update_report(
    report_id: int,
    report_dto: ReportCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> ReportSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            updated_report = await report_repo.update_report(
                session=session,
                report_id=report_id,
                report=report_dto,
            )
    except ReportNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except ReportAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return updated_report

@report_routes.delete(
    "/delete_report/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_report(
    report_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            await report_repo.delete_report(session=session, report_id=report_id)
    except ReportNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)