from fastapi import APIRouter, File, HTTPException, UploadFile
from typing import List
import pdfplumber
import re

router = APIRouter(prefix="/bert/rules", tags=["BERT Rules"])


def clean_text(text: str) -> str:
    text = text.replace("", "")
    text = text.replace("–", "-")
    text = text.replace("  ", " ")
    return text.strip()


def merge_lines_to_paragraphs(lines: List[str]) -> List[str]:
    paragraphs = []
    current = ""

    for line in lines:
        line = line.strip()

        if not line:
            if current:
                paragraphs.append(current.strip())
                current = ""
            continue

        if current and not current.endswith(('.', ':')):
            current += " " + line
        else:
            if current:
                paragraphs.append(current.strip())
            current = line

    if current:
        paragraphs.append(current.strip())

    return paragraphs



def is_valid_rule(text: str) -> bool:
    if len(text) < 40:
        return False
    if len(text.split()) < 6:
        return False

    if "рисунок" in text.lower() and len(text) < 60:
        return False

    return True



def categorize(text: str) -> str:
    t = text.lower()

    if "таблиц" in t:
        return "tables"
    if "рисунк" in t or "иллюстрац" in t:
        return "figures"
    if "ссыл" in t:
        return "references"
    if "формул" in t:
        return "formulas"
    if "шрифт" in t or "интервал" in t or "страниц" in t:
        return "formatting"

    return "structure"



def deduplicate(rules):
    seen = set()
    result = []

    for r in rules:
        key = r["text"][:100]
        if key not in seen:
            seen.add(key)
            result.append(r)

    return result



@router.post("/extract")
async def extract_rules(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Нужен PDF файл")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")

    try:
        rules = []
        total_pages = 0

        with pdfplumber.open(file.file) as pdf:
            total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()

                if not text:
                    continue

                lines = text.split("\n")
                paragraphs = merge_lines_to_paragraphs(lines)

                for p in paragraphs:
                    p = clean_text(p)

                    if not is_valid_rule(p):
                        continue

                    section_match = re.match(r"^\d+(\.\d+)*", p)

                    rules.append({
                        "section": section_match.group(0) if section_match else None,
                        "title": f"Пункт {section_match.group(0)}" if section_match else p[:50],
                        "text": p,
                        "page": page_num,
                        "category": categorize(p),
                        "confidence": 0.6,
                    })

        rules = deduplicate(rules)

        return {
            "filename": file.filename,
            "pages": total_pages,
            "rules_count": len(rules),
            "rules": rules,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")