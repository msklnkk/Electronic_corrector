from pathlib import Path
from typing import Dict, Any
from docx import Document as DocxDocument
import pdfplumber
import re

async def extract_document_data(file_path: str) -> Dict[str, Any]:
    path = Path(file_path)
    ext = path.suffix.lower()

    data = {
        "required_elements": [],
        "font_settings": {"font_family": None, "font_size": None, "line_spacing": None},
        "page_margins": {"left": None, "right": None, "top": None, "bottom": None},
        "paragraph_indent": None,
        "introduction_text": "",
        "full_text": "",
    }

    if ext == ".docx":
        doc = DocxDocument(file_path)
        # Структура: заголовки как элементы
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                data["full_text"] += text + " "
                if para.style.name.startswith("Heading"):
                    data["required_elements"].append(text.lower())

        # Введение — ищем после "введение" до следующего заголовка
        intro_mode = False
        for para in doc.paragraphs:
            text = para.text.strip().lower()
            if "введение" in text:
                intro_mode = True
                continue
            if intro_mode and para.style.name.startswith("Heading"):
                break
            if intro_mode:
                data["introduction_text"] += para.text + " "

        # Форматирование (примерно из первых параграфов)
        for para in doc.paragraphs[:30]:
            for run in para.runs:
                if run.font.name:
                    data["font_settings"]["font_family"] = run.font.name
                if run.font.size:
                    data["font_settings"]["font_size"] = run.font.size.pt
            if para.paragraph_format.line_spacing:
                data["font_settings"]["line_spacing"] = para.paragraph_format.line_spacing

        if para.paragraph_format.first_line_indent:
            data["paragraph_indent"] = para.paragraph_format.first_line_indent.inches * 2.54  # см

    elif ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                data["full_text"] += text + " "
                # Простая эвристика для элементов структуры
                lines = text.split("\n")
                for line in lines:
                    line = line.strip().lower()
                    if re.match(r"^\d+\.?\s", line) or "введение" in line or "заключение" in line:
                        data["required_elements"].append(line)

            data["introduction_text"] = extract_introduction_from_text(data["full_text"])

    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")

    return data


def extract_introduction_from_text(full_text: str) -> str:
    # Простая эвристика: текст после "введение" до "1." или "глава"
    match = re.search(r"введение(.*?)(\d+\.|глава|основная часть)", full_text.lower(), re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""