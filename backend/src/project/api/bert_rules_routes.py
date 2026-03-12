from fastapi import APIRouter, File, HTTPException, UploadFile

from project.schemas.bert_rules import BertRulesResponse
from project.services.bert_rule_reader import BertRuleReader

router = APIRouter(prefix="/bert/rules", tags=["BERT Rules"])

_reader = None


def get_reader() -> BertRuleReader:
    global _reader
    if _reader is None:
        _reader = BertRuleReader()
    return _reader


@router.get("/health")
async def bert_rules_health():
    return {
        "status": "ok",
        "service": "bert-rules-reader",
        "model": "cointegrated/rubert-tiny2",
    }


@router.post("/extract", response_model=BertRulesResponse)
async def extract_rules(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Нужен PDF файл")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")

    try:
        reader = get_reader()
        pages, rules = reader.extract_rules_from_pdf(content)

        return BertRulesResponse(
            filename=file.filename,
            pages=pages,
            rules_count=len(rules),
            rules=rules,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки PDF: {str(e)}")