# backend/src/project/gost_checker/parser.py
from collections import Counter
from pathlib import Path
from typing import Dict, Any, Optional
import io
import re

from docx import Document as DocxDocument
import pdfplumber


async def extract_document_data(
        file_path: Optional[str] = None,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None
) -> Dict[str, Any]:
    # Извлекает данные из документа для проверки по ГОСТ.
    #
    # Поддерживает два режима работы:
    # 1. file_path — для текущего FastAPI (как было раньше)
    # 2. file_content + filename — для gRPC (байты в памяти)
    # Определяем расширение и источник данных
    if file_content is not None:
        if filename is None:
            raise ValueError("При передаче file_content обязательно укажите filename для определения типа файла")
        ext = Path(filename).suffix.lower()
        file_stream = io.BytesIO(file_content)
    elif file_path is not None:
        path = Path(file_path)
        ext = path.suffix.lower()
        file_stream = None
    else:
        raise ValueError("Необходимо передать либо file_path, либо (file_content + filename)")

    data: Dict[str, Any] = {
        "required_elements": [],
        "font_settings": {"font_family": None, "font_size": None, "line_spacing": None},
        "page_margins": {"left": None, "right": None, "top": None, "bottom": None},
        "paragraph_indent": None,
        "introduction_text": "",
        "full_text": "",
        "page_count": 0,
        "word_count": 0,
    }

    try:
        if ext == ".docx":
            # ====================== DOCX ======================
            if file_content is not None:
                doc = DocxDocument(file_stream)
            else:
                doc = DocxDocument(file_path)

            fonts = []
            sizes = []
            line_spacings = []
            indents = []
            has_chapters = False
            intro_started = False
            intro_text = []

            for para_num, para in enumerate(doc.paragraphs):
                text = para.text.strip()
                if not text:
                    continue

                data["full_text"] += text + " "
                data["word_count"] += len(text.split())

                lower_text = text.lower()

                # Определение заголовков
                is_heading = (
                        para.style.name.startswith("Heading") or
                        any(getattr(run, 'bold', False) for run in para.runs) or
                        (len(text) < 50 and text.isupper()) or
                        re.match(r"^\d+\.?\s", lower_text)
                )

                if is_heading:
                    cleaned = re.sub(r'^\d+\.?\s*', '', lower_text).strip()
                    if cleaned and cleaned not in data["required_elements"]:
                        data["required_elements"].append(cleaned)
                    if re.match(r'^\d+\.', lower_text):
                        has_chapters = True

                # Титульный лист
                if para_num < 50 and any(keyword in lower_text for keyword in [
                    "курсовая работа", "дипломная работа", "выпускная квалификационная работа",
                    "студент", "преподаватель", "университет", "факультет"
                ]):
                    if "титульный лист" not in data["required_elements"]:
                        data["required_elements"].append("титульный лист")

                # Введение
                if "введение" in lower_text:
                    intro_started = True
                if intro_started:
                    intro_text.append(text)

                # Форматирование
                if para.runs:
                    for run in para.runs:
                        if getattr(run.font, 'name', None):
                            fonts.append(run.font.name)
                        if getattr(run.font, 'size', None):
                            sizes.append(run.font.size.pt)

                if para.paragraph_format.line_spacing is not None:
                    line_spacings.append(para.paragraph_format.line_spacing)

                if para.paragraph_format.first_line_indent is not None:
                    indent_cm = para.paragraph_format.first_line_indent.cm
                    if indent_cm > 0:
                        indents.append(indent_cm)

            data["introduction_text"] = " ".join(intro_text).strip()

            # Агрегация значений
            data["font_settings"]["font_family"] = max(Counter(fonts).items(), key=lambda x: x[1])[0] if fonts else None
            data["font_settings"]["font_size"] = round(
                max(Counter(sizes).items(), key=lambda x: x[1])[0]) if sizes else None
            data["font_settings"]["line_spacing"] = round(
                max(Counter(line_spacings).items(), key=lambda x: x[1])[0], 1) if line_spacings else None
            data["paragraph_indent"] = round(
                max(Counter(indents).items(), key=lambda x: x[1])[0], 2) if indents else None

            # Поля страницы
            if doc.sections:
                s = doc.sections[0]
                data["page_margins"] = {
                    "left": round(s.left_margin.mm, 1) if s.left_margin else None,
                    "right": round(s.right_margin.mm, 1) if s.right_margin else None,
                    "top": round(s.top_margin.mm, 1) if s.top_margin else None,
                    "bottom": round(s.bottom_margin.mm, 1) if s.bottom_margin else None,
                }

            if has_chapters:
                if "основная часть" not in data["required_elements"]:
                    data["required_elements"].append("основная часть")

        elif ext == ".pdf":
            # ====================== PDF ======================
            if file_content is not None:
                pdf = pdfplumber.open(file_stream)
            else:
                pdf = pdfplumber.open(file_path)

            with pdf:
                data["page_count"] = len(pdf.pages)
                fonts = []
                sizes = []
                line_y_diffs = []
                indent_x = []
                all_x0, all_x1, all_y0, all_y1 = [], [], [], []

                has_chapters = False

                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    data["full_text"] += text + " "
                    data["word_count"] += len(re.findall(r'\w+', text))

                    # Структура документа
                    char_sizes = [char.get('size', 0) for char in page.chars]
                    avg_size = sum(char_sizes) / len(char_sizes) if char_sizes else 12
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    for line in lines:
                        lower_line = line.lower()
                        pattern = r"^(содержание|оглавление|определения|обозначения и сокращения|введение|заключение|список (использованных|литературы|источников)|приложения|\d+\.?\s?[\w]+|глава \d+)"
                        if re.match(pattern, lower_line) or any(
                                char.get('size', 0) > avg_size + 1 for char in page.chars if char.get('text') in line
                        ):
                            cleaned = re.sub(r'^\d+\.?\s*', '', lower_line).strip()
                            if cleaned and cleaned not in data["required_elements"]:
                                data["required_elements"].append(cleaned)
                            if re.match(r'^\d+\.', line):
                                has_chapters = True

                    # Титульный лист
                    if page_num == 1 and any(kw in lower_line for kw in
                                             ["курсовая работа", "дипломная работа", "студент", "преподаватель",
                                              "университет"]):
                        if "титульный лист" not in data["required_elements"]:
                            data["required_elements"].append("титульный лист")

                    # Сбор шрифтов и размеров
                    for char in page.chars:
                        if 'fontname' in char:
                            font_name = re.sub(r'^[A-Z]{6}\+', '', char['fontname'])
                            font_name = re.sub(r'-(Regular|Bold|Italic|BoldItalic)$', '', font_name)
                            fonts.append(font_name)
                        if 'size' in char:
                            sizes.append(char['size'])
                        if 'x0' in char and char.get('text', '').strip():
                            all_x0.append(char['x0'])
                        if 'x1' in char and char.get('text', '').strip():
                            all_x1.append(char['x1'])
                        if 'y0' in char:
                            all_y0.append(char['y0'])
                        if 'y1' in char:
                            all_y1.append(char['y1'])

                    # Line spacing и indent
                    y_positions = sorted(set(char['y0'] for char in page.chars if 'y0' in char), reverse=True)
                    for i in range(len(y_positions) - 1):
                        diff = y_positions[i] - y_positions[i + 1]
                        if avg_size * 0.5 < diff < avg_size * 3:
                            line_y_diffs.append(diff)

                    # Indent
                    first_chars_x = []
                    prev_y = None
                    for char in sorted(page.chars, key=lambda c: (-c.get('y1', 0), c.get('x0', 0))):
                        if 'y1' in char and (prev_y is None or abs(char['y1'] - prev_y) > avg_size * 0.5):
                            if char.get('size', 0) <= avg_size + 1:
                                first_chars_x.append(char['x0'])
                            prev_y = char['y1']
                    if first_chars_x:
                        avg_indent_pt = sum(first_chars_x) / len(first_chars_x)
                        indent_x.append(avg_indent_pt / 28.346)

                data["introduction_text"] = extract_introduction_from_text(data["full_text"])

                # Агрегация
                data["font_settings"]["font_family"] = max(Counter(fonts).items(), key=lambda x: x[1])[
                    0] if fonts else None
                data["font_settings"]["font_size"] = round(
                    max(Counter(sizes).items(), key=lambda x: x[1])[0]) if sizes else None

                avg_diff = sum(line_y_diffs) / len(line_y_diffs) if line_y_diffs else None
                avg_size = data["font_settings"]["font_size"] or 14
                data["font_settings"]["line_spacing"] = round(avg_diff / avg_size, 1) if avg_diff else None

                data["paragraph_indent"] = round(sum(indent_x) / len(indent_x), 2) if indent_x else None

                # Margins
                pt_to_mm = 0.3528
                if all_x0 and all_x1 and all_y0 and all_y1:
                    min_x = min(all_x0)
                    max_x = max(all_x1)
                    min_y = min(all_y0)
                    max_y = max(all_y1)
                    width = pdf.pages[0].width if pdf.pages else 595
                    height = pdf.pages[0].height if pdf.pages else 842
                    data["page_margins"] = {
                        "left": round(min_x * pt_to_mm, 1) if min_x > 0 else 0,
                        "right": round((width - max_x) * pt_to_mm, 1) if max_x < width else 0,
                        "top": round((height - max_y) * pt_to_mm, 1) if max_y < height else 0,
                        "bottom": round(min_y * pt_to_mm, 1) if min_y > 0 else 0,
                    }

                if has_chapters:
                    data["required_elements"].append("основная часть")

        else:
            raise ValueError(f"Неподдерживаемый формат: {ext}")

    except Exception as e:
        raise RuntimeError(f"Ошибка при парсинге документа ({ext}): {str(e)}") from e

    return data


def extract_introduction_from_text(full_text: str) -> str:
    # Извлекает текст введения из полного текста
    match = re.search(
        r"(введение|introduction)\s*([\s\S]*?)\s*(?:заключение|conclusion|список использованных|список литературы|приложения|\d+\.\s|глава)",
        full_text.lower(),
        re.IGNORECASE | re.DOTALL
    )
    return match.group(2).strip() if match else full_text[:1000]