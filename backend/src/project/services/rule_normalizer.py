import re
from typing import List, Optional

from project.schemas.bert_rules import ExtractedRule


SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\b")


def extract_section_from_text(text: str) -> Optional[str]:
    match = SECTION_RE.match(text)
    return match.group(1) if match else None


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .;:-")


def has_unbalanced_pairs(text: str) -> bool:
    pairs = [
        ("«", "»"),
        ('"', '"'),
        ("(", ")"),
        ("[", "]"),
    ]
    for left, right in pairs:
        if text.count(left) > text.count(right):
            return True
    return False


def looks_like_fragment(text: str) -> bool:
    text = normalize_spaces(text)

    if len(text) < 15:
        return True

    words = text.split()
    if len(words) < 3:
        return True

    if re.search(r"[А-Яа-яA-Za-z]-$", text):
        return True

    if has_unbalanced_pairs(text):
        return True

    if text.endswith(":"):
        return True

    return False


def is_appendix_template(text: str) -> bool:
    low = text.lower()

    appendix_markers = [
        "приложение а",
        "приложение б",
        "приложение в",
        "приложение г",
        "приложение д",
        "приложение е",
        "приложение ж",
        "приложение и",
        "форма отзыва",
        "форма рецензии",
        "форма титульного листа",
        "наименование факультета, института, колледжа",
        "подпись, дата инициалы, фамилия",
        "студента (ки) курса",
        "полное наименование темы",
    ]
    return any(marker in low for marker in appendix_markers)


def split_by_semicolon_if_enumeration(text: str) -> List[str]:
    if ":" in text and ";" in text:
        parts = [normalize_spaces(p) for p in text.split(";")]
        return [p for p in parts if p and not looks_like_fragment(p)]
    return [text]


def split_by_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [normalize_spaces(p) for p in parts]
    return [p for p in parts if p and not looks_like_fragment(p)]


def split_by_section_markers(text: str) -> List[str]:
    parts = re.split(r"(?=(?:^|\s)\d+(?:\.\d+)+\b)", text)
    parts = [normalize_spaces(p) for p in parts]
    return [p for p in parts if p]


def split_into_atomic_rules(text: str) -> List[str]:
    text = normalize_spaces(text)
    if not text:
        return []

    result: List[str] = []

    for part in split_by_section_markers(text):
        for subpart in split_by_semicolon_if_enumeration(part):
            items = split_by_sentences(subpart)
            if items:
                result.extend(items)
            elif not looks_like_fragment(subpart):
                result.append(subpart)

    cleaned: List[str] = []
    for item in result:
        item = normalize_spaces(item)
        if not item:
            continue
        if looks_like_fragment(item):
            continue
        cleaned.append(item)

    return cleaned


def detect_category(text: str, section: Optional[str]) -> str:
    low = text.lower()

    if section:
        if section.startswith("6.4"):
            return "headings"
        if section.startswith("6.5"):
            return "pagination"
        if section.startswith("6.8"):
            return "figures"
        if section.startswith("6.9"):
            return "tables"
        if section.startswith("6.10"):
            return "formulas"
        if section.startswith("6.12"):
            return "appendices"

    if any(x in low for x in ["таблиц", "граф", "боковик", "головка таблицы"]):
        return "tables"
    if any(x in low for x in ["рисунк", "иллюстрац", "подрисуноч"]):
        return "figures"
    if any(x in low for x in ["ссылк", "сноск", "библиограф"]):
        return "references"
    if any(x in low for x in ["формул", "уравнен", "символ"]):
        return "formulas"
    if any(x in low for x in ["шрифт", "интервал", "поля", "страницы", "номер страницы"]):
        return "formatting"
    if "заголов" in low:
        return "headings"
    if "приложени" in low:
        return "appendices"

    return "structure"


def build_title(section: Optional[str], text: str) -> str:
    if section:
        return f"Пункт {section}"
    short = text[:60].strip()
    return short + ("..." if len(text) > 60 else "")


def normalize_rule(
    text: str,
    section: Optional[str],
    page: int,
    confidence: float,
) -> ExtractedRule:
    text = normalize_spaces(text)
    actual_section = extract_section_from_text(text) or section
    actual_category = detect_category(text, actual_section)
    confidence = max(0.0, min(round(confidence, 2), 1.0))

    return ExtractedRule(
        section=actual_section,
        title=build_title(actual_section, text),
        text=text,
        page=page,
        category=actual_category,
        confidence=confidence,
    )