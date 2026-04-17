from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile
import os
import traceback
from pathlib import Path

router = APIRouter(prefix="/rules", tags=["rules"])

DEFAULT_THRESHOLD = float(os.getenv("RULE_THRESHOLD", "0.65"))
DEFAULT_USE_CATEGORY = os.getenv("USE_CATEGORY_MODEL", "true").lower() == "true"

MODEL_BASE_DIR = Path(os.getenv("MODEL_BASE_DIR", "/app/models"))
RULE_MODEL = MODEL_BASE_DIR / "rule_classifier"
CATEGORY_MODEL = MODEL_BASE_DIR / "category_classifier"


def validate_model_dir(model_dir: Path, model_name: str) -> None:
    if not model_dir.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Папка модели не найдена: {model_dir}"
        )

    required_files = ["config.json", "model.safetensors"]
    missing = [name for name in required_files if not (model_dir / name).exists()]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Модель {model_name} неполная. Нет файлов: {', '.join(missing)}"
        )


@router.post(
    "/extract",
    summary="Извлечь правила из PDF",
    description="Загрузите PDF, система автоматически извлечёт правила."
)
async def extract_rules(
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Нужен PDF")

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            from src.ml.predict_rules_pdf import process_pdf
        except Exception as e:
            print("IMPORT ERROR")
            traceback.print_exc()
            raise HTTPException(
                status_code=503,
                detail=f"Ошибка импорта ML-модуля: {type(e).__name__}: {str(e)}"
            ) from e

        validate_model_dir(RULE_MODEL, "rule_classifier")

        category_model_path = None
        if DEFAULT_USE_CATEGORY:
            validate_model_dir(CATEGORY_MODEL, "category_classifier")
            category_model_path = str(CATEGORY_MODEL)

        result = process_pdf(
            pdf_path=tmp_path,
            rule_model_path=str(RULE_MODEL),
            category_model_path=category_model_path,
            threshold=DEFAULT_THRESHOLD,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка извлечения правил: {str(e)}"
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        await file.close()