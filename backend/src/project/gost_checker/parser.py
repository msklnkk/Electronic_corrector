from collections import Counter
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
        fonts = []
        sizes = []
        line_spacings = []
        indents = []
        current_heading = ""

        # Структура: заголовки как элементы
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                data["full_text"] += text + " "

                if para.style.name.startswith("Heading"):
                    current_heading = text.lower()
                    data["required_elements"].append(current_heading)

                # Введение
                if "введение" in current_heading:
                    data["introduction_text"] += text + " "

                # Форматирование
                if para.runs:
                    for run in para.runs:
                        if run.font.name:
                            fonts.append(run.font.name)
                        if run.font.size:
                            sizes.append(run.font.size.pt)
                if para.paragraph_format.line_spacing:
                    line_spacings.append(para.paragraph_format.line_spacing)
                if para.paragraph_format.first_line_indent:
                    indents.append(para.paragraph_format.first_line_indent.cm)  # в см

        # Аггрегируем (берём самый частый)
        data["font_settings"]["font_family"] = max(Counter(fonts).items(), key=lambda x: x[1])[0] if fonts else None
        data["font_settings"]["font_size"] = max(Counter(sizes).items(), key=lambda x: x[1])[0] if sizes else None
        data["font_settings"]["line_spacing"] = max(Counter(line_spacings).items(), key=lambda x: x[1])[0] if line_spacings else None
        data["paragraph_indent"] = max(Counter(indents).items(), key=lambda x: x[1])[0] if indents else None

        # Поля (из первой секции)
        if doc.sections:
            s = doc.sections[0]
            data["page_margins"] = {
                "left": s.left_margin.inches * 2.54 if s.left_margin else None,
                "right": s.right_margin.inches * 2.54 if s.right_margin else None,
                "top": s.top_margin.inches * 2.54 if s.top_margin else None,
                "bottom": s.bottom_margin.inches * 2.54 if s.bottom_margin else None
            }

    elif ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            data["page_count"] = len(pdf.pages)
            fonts = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                data["full_text"] += text + " "

                # Простая эвристика заголовков
                lines = [l.strip().lower() for l in text.split("\n") if l.strip()]
                for line in lines:
                    if re.match(r"^(введение|заключение|список литературы|оглавление|\d+\.\s)", line):
                        data["required_elements"].append(line)

                # Шрифты (если доступны)
                for char in page.chars:
                    if 'fontname' in char:
                        fonts.append(char['fontname'])

            data["introduction_text"] = extract_introduction_from_text(data["full_text"])
            data["font_settings"]["font_family"] = max(Counter(fonts).items(), key=lambda x: x[1])[0] if fonts else None

    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")

    return data


def extract_introduction_from_text(full_text: str) -> str:
    # Простая эвристика: текст после "введение" до "1." или "глава"
    match = re.search(r"(введение)(.*?)(1\.|глава|основная часть|заключение)", full_text.lower(),
                      re.DOTALL | re.IGNORECASE)
    return match.group(2).strip() if match else full_text[:500]  # fallback