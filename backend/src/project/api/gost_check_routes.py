from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from decimal import Decimal

from project.infrastructure.postgres.database import database
from project.infrastructure.postgres.models import Users, Documents, Status
from project.schemas.gost_check import (
    GostCheckRequest,
    GostCheckResponse,
    GostCheckResult,
    GostCheckStatus,
    GostStandardOption,
)
from project.core.gost_service import GostCheckService
from project.api.depends import get_current_user, standard_repo

from project.infrastructure.kafka.publishers import publish_status, publish_report_task

router = APIRouter(prefix="/gost-check", tags=["GOST Check"])


@router.get("/standards", response_model=list[GostStandardOption])
async def list_gost_standards(
    current_user: Users = Depends(get_current_user),
):
    async with database.session() as session:
        standards = await standard_repo.list_state_standards(session=session)
    return [
        GostStandardOption(
            standart_id=s.standart_id,
            name=s.name,
            version=s.version,
            description=s.description,
        )
        for s in standards
    ]


@router.post("/start", response_model=GostCheckResponse)
async def start_gost_check(
    request_data: GostCheckRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Users = Depends(get_current_user),
):
    async with database.session() as session:
        kafka_producer = getattr(request.app.state, "kafka_producer", None)
        if request_data.standart_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Требуется выбрать ГОСТ перед запуском проверки",
            )

        from sqlalchemy import select
        stmt = select(Documents).where(
            Documents.document_id == request_data.document_id,
            Documents.user_id == current_user.user_id
        )
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )

        service = GostCheckService(session)

        try:
            await publish_status(
                kafka_producer=kafka_producer,
                document_id=request_data.document_id,
                status="processing",
                message="Проверка документа началась",
            )

            check_id = await service.start_gost_check(
                request_data.document_id,
                standart_id=request_data.standart_id,
            )

            await publish_status(
                kafka_producer=kafka_producer,
                document_id=request_data.document_id,
                status="done",
                message="Проверка документа завершена",
            )

            await publish_report_task(
                kafka_producer=kafka_producer,
                document_id=request_data.document_id,
                report_type="json",
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            await publish_status(
                kafka_producer=kafka_producer,
                document_id=request_data.document_id,
                status="failed",
                message="Ошибка при проверке документа",
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при запуске проверки ГОСТ: {str(e)}"
            )

        return GostCheckResponse(
            check_id=check_id,
            document_id=request_data.document_id,
            status="Анализируется",
            score=Decimal("0.0"),
            is_compliant=False,
            total_errors=0,
            total_warnings=0,
            checked_at=datetime.now()
        )


@router.get("/status/{document_id}", response_model=GostCheckStatus)
async def get_gost_check_status(
    document_id: int,
    current_user: Users = Depends(get_current_user),
):
    async with database.session() as session:
        from sqlalchemy import select
        stmt = select(Documents).where(
            Documents.document_id == document_id,
            Documents.user_id == current_user.user_id
        )
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )

        status_progress_map = {
            "Загружен": 0,
            "Анализируется": 50,
            "Проверен": 80,
            "Идеален": 100,
            "Отправлен на доработку": 100
        }

        stmt_status = select(Status).where(Status.status_id == document.status_id)
        result_status = await session.execute(stmt_status)
        current_status = result_status.scalar_one_or_none()

        progress = status_progress_map.get(current_status.status_name, 0) if current_status else 0

        return GostCheckStatus(
            document_id=document_id,
            status=current_status.status_name if current_status else "Неизвестно",
            progress=progress,
            estimated_time_remaining=0 if progress == 100 else 30
        )


@router.get("/result/{check_id}", response_model=GostCheckResult)
async def get_gost_check_result(
    check_id: int,
    current_user: Users = Depends(get_current_user),
):
    async with database.session() as session:
        service = GostCheckService(session)
        result = await service.get_check_result(check_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Результат проверки не найден"
            )

        from sqlalchemy import select
        stmt = select(Documents).where(
            Documents.document_id == result["document_id"],
            Documents.user_id == current_user.user_id
        )
        result_doc = await session.execute(stmt)
        document = result_doc.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к результатам проверки"
            )

        return GostCheckResult(
            check_id=result["check_id"],
            document_id=result["document_id"],
            is_compliant=result["status"] == "perfect",
            score=document.score,
            status=result["status"],
            filename=result.get("filename", "unknown"),
            errors=result["errors"],
            warnings=result["warnings"],
            details={},
            checked_at=result["checked_at"]
        )