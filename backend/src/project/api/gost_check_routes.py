from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request

from project.infrastructure.postgres.database import database
from project.infrastructure.postgres.models import Users, Documents, Status
from project.schemas.gost_check import (
    GostCheckRequest,
    GostCheckResponse,
    GostCheckResult,
    GostCheckStatus,
    GostStandardOption,
    UserTemplateCheckRequest,
    UserTemplateCheckResult,
)
from project.core.gost_service import GostCheckService
from project.api.depends import get_current_user, standard_repo
from project.infrastructure.kafka.publishers import publish_status

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
                status="Анализируется",
                message="Проверка документа началась",
            )

            check_id = await service.start_gost_check(
                request_data.document_id,
                standart_id=request_data.standart_id,
            )

            await publish_status(
                kafka_producer=kafka_producer,
                document_id=request_data.document_id,
                status="Проверен",
                message="Проверка документа завершена",
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
                status="Ошибка",
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
            "Отправлен на доработку": 100,
            "Ошибка": 0,
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


def _build_user_template_rules(form: UserTemplateCheckRequest) -> dict:
    structure: dict = {}
    formatting: dict = {}

    if form.required_sections:
        structure["5.1_required_elements"] = {
            "title": "Обязательные разделы документа",
            "expected_value": form.required_sections,
            "severity": "critical",
            "rule_type": "structure",
            "check_type": "list_presence",
            "section": "5.1",
        }

    font_expected: dict = {}
    if form.font_name:
        font_expected["font_family"] = form.font_name
    if form.font_size is not None:
        font_expected["font_size"] = float(form.font_size)
    if font_expected:
        formatting["6.1.1_font"] = {
            "title": "Шрифт документа",
            "expected_value": font_expected,
            "severity": "critical",
            "rule_type": "formatting",
            "check_type": "object_equals",
            "section": "6.1.1",
        }

    margins: dict = {}
    if form.margin_left_mm is not None:
        margins["left"] = float(form.margin_left_mm)
    if form.margin_right_mm is not None:
        margins["right"] = float(form.margin_right_mm)
    if form.margin_top_mm is not None:
        margins["top"] = float(form.margin_top_mm)
    if form.margin_bottom_mm is not None:
        margins["bottom"] = float(form.margin_bottom_mm)
    if margins:
        formatting["6.1.1_margins"] = {
            "title": "Поля страницы (мм)",
            "expected_value": margins,
            "severity": "critical",
            "rule_type": "formatting",
            "check_type": "object_equals",
            "section": "6.1.1",
        }

    if form.paragraph_indent_cm is not None:
        formatting["6.1.2_paragraph"] = {
            "title": "Абзацный отступ (см)",
            "expected_value": round(form.paragraph_indent_cm, 2),
            "severity": "warning",
            "rule_type": "formatting",
            "check_type": "equals",
            "section": "6.1.2",
        }

    return {"rules": {"structure": structure, "formatting": formatting}}


@router.post("/user-template/{document_id}", response_model=UserTemplateCheckResult)
async def run_user_template_check(
    document_id: int,
    request_data: UserTemplateCheckRequest,
    current_user: Users = Depends(get_current_user),
):
    import json as _json
    import os
    import tempfile

    from sqlalchemy import select as sa_select

    from project.gost_checker.checker import GOSTDocumentChecker
    from project.gost_checker.models import RuleSeverity

    async with database.session() as session:
        stmt = sa_select(Documents).where(
            Documents.document_id == document_id,
            Documents.user_id == current_user.user_id,
        )
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    rules_data = _build_user_template_rules(request_data)
    has_rules = (
        rules_data["rules"]["structure"] or rules_data["rules"]["formatting"]
    )
    if not has_rules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не задано ни одного правила для проверки",
        )

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            _json.dump(rules_data, f, ensure_ascii=False)

        checker = GOSTDocumentChecker(rules_file=tmp_path)
        report = await checker.check_document(
            file_path=document.filepath,
            document_id=str(document_id),
            original_filename=document.filename,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    score = int(round((report.passed_checks / max(report.total_checks, 1)) * 100))
    errors = [
        r.message
        for r in report.results
        if not r.is_passed and r.severity == RuleSeverity.CRITICAL
    ]
    warnings = [
        r.message
        for r in report.results
        if not r.is_passed and r.severity == RuleSeverity.WARNING
    ]

    return UserTemplateCheckResult(
        document_id=document_id,
        filename=document.filename,
        status="Соответствует" if report.passed_checks == report.total_checks else "Требует доработки",
        score=score,
        is_compliant=report.passed_checks == report.total_checks,
        errors=errors,
        warnings=warnings,
        total_checks=report.total_checks,
        passed_checks=report.passed_checks,
    )