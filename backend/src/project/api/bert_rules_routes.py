from fastapi import APIRouter, File, HTTPException, UploadFile
from project.schemas.bert_rules import BertRulesResponse
from project.services.rule_extraction_service import RuleExtractionService

router = APIRouter(prefix="/bert/rules", tags=["BERT Rules"])

_service = None


def get_service() -> RuleExtractionService:
    global _service
    if _service is None:
        _service = RuleExtractionService()
    return _service


@router.get("/health")
async def bert_rules_health():
    return {
        "status": "ok",
        "service": "rule-extraction-service",
    }


@router.post("/extract", response_model=BertRulesResponse)
async def extract_rules(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Не удалось определить имя файла")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Поддерживается только PDF")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")

    try:
        service = get_service()
        pages, rules = service.extract_from_pdf(content)

        return BertRulesResponse(
            filename=file.filename,
            pages=pages,
            rules_count=len(rules),
            rules=rules,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки PDF: {str(e)}")