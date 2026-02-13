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
        "page_count": 0,
        "word_count": 0,
    }

    if ext == ".docx":
        doc = DocxDocument(file_path)
        data["page_count"] = len(doc.sections)  # приблизительно, по секциям
        fonts = []
        sizes = []
        line_spacings = []
        indents = []
        has_chapters = False
        intro_started = False
        intro_text = []

        for para_num, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            if text:
                data["full_text"] += text + " "
                data["word_count"] += len(text.split())

                lower_text = text.lower()
                # Структура: heading styles или эвристика (большой шрифт, жирный, центрированный, паттерн)
                is_heading = para.style.name.startswith("Heading") or any(run.bold for run in para.runs) or len(
                    text) < 50 and text.isupper() or re.match(r"^\d+\.?\s", lower_text)
                if is_heading:
                    cleaned = re.sub(r'^\d+\.?\s*', '', lower_text)  # убрать номера
                    if cleaned not in data["required_elements"]:
                        data["required_elements"].append(cleaned)
                    if re.match(r'^\d+\.', lower_text):  # глава
                        has_chapters = True

                    # Конец введения если следующий заголовок после "введение"
                    if intro_started and cleaned not in ["введение"]:
                        intro_started = False

                # Титульный лист: ключевые слова на первой странице (первые 50 параграфов)
                if para_num < 50 and any(keyword in lower_text for keyword in
                                         ["курсовая работа", "дипломная работа", "студент", "преподаватель",
                                          "университет", "факультет", "москва", "год"]):
                    if "титульный лист" not in data["required_elements"]:
                        data["required_elements"].append("титульный лист")

                # Введение: собираем текст после "введение" до следующего заголовка
                if "введение" in lower_text:
                    intro_started = True
                if intro_started:
                    intro_text.append(text)

                # Форматирование
                if para.runs:
                    for run in para.runs:
                        if run.font.name:
                            fonts.append(run.font.name)
                        if run.font.size:
                            sizes.append(run.font.size.pt)
                if para.paragraph_format.line_spacing:
                    line_spacings.append(para.paragraph_format.line_spacing)
                if para.paragraph_format.first_line_indent and para.paragraph_format.first_line_indent.cm > 0:  # только положительные
                    indents.append(para.paragraph_format.first_line_indent.cm)  # в см

        data["introduction_text"] = " ".join(intro_text)

        # Аггрегируем (берём самый частый)
        data["font_settings"]["font_family"] = max(Counter(fonts).items(), key=lambda x: x[1])[0] if fonts else None
        data["font_settings"]["font_size"] = round(
            max(Counter(sizes).items(), key=lambda x: x[1])[0]) if sizes else None
        data["font_settings"]["line_spacing"] = round(max(Counter(line_spacings).items(), key=lambda x: x[1])[0],
                                                      1) if line_spacings else None
        data["paragraph_indent"] = round(max(Counter(indents).items(), key=lambda x: x[1])[0], 2) if indents else None

        # Поля (из первой секции)
        if doc.sections:
            s = doc.sections[0]
            data["page_margins"] = {
                "left": round(s.left_margin.mm, 1) if s.left_margin else None,
                # cm to mm *10? No, left_margin is in twips, but docx uses cm property
                "right": round(s.right_margin.mm, 1) if s.right_margin else None,
                # Add .mm property if not, or *10 if cm
                "top": round(s.top_margin.mm, 1) if s.top_margin else None,
                "bottom": round(s.bottom_margin.mm, 1) if s.bottom_margin else None
            }  # If docx doesn't have .mm, add: round(s.left_margin.cm * 10, 1)

        # Добавить "основная часть" если есть главы
        if has_chapters:
            data["required_elements"].append("основная часть")

    elif ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            data["page_count"] = len(pdf.pages)
            fonts = []
            sizes = []
            line_y_diffs = []  # для line_spacing
            indent_x = []  # для paragraph_indent

            all_x0 = []  # для left margin
            all_x1 = []  # для right
            all_y0 = []  # для bottom
            all_y1 = []  # для top

            has_chapters = False
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                data["full_text"] += text + " "
                data["word_count"] += len(re.findall(r'\w+', text))

                # Улучшенная структура: заголовки по паттерну или большому шрифту
                char_sizes = [char.get('size', 0) for char in page.chars]
                avg_size = sum(char_sizes) / len(char_sizes) if char_sizes else 12
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                for line in lines:
                    lower_line = line.lower()
                    # Расширенный паттерн для типичных разделов курсовой
                    pattern = r"^(содержание|оглавление|определения|обозначения и сокращения|введение|заключение|список (использованных|литературы|источников)|приложения|\d+\.?\s?[\w]+|глава \d+)"
                    if re.match(pattern, lower_line) or any(char['size'] > avg_size + 1 for char in page.chars if char['text'] in line):
                        cleaned = re.sub(r'^\d+\.?\s*', '', lower_line)  # убрать номера
                        if cleaned not in data["required_elements"]:
                            data["required_elements"].append(cleaned)
                            if re.match(r'^\d+\.', line):  # глава
                                has_chapters = True

                    # Для титульного листа (первая страница): ключевые слова
                    if page_num == 1 and any(keyword in lower_line for keyword in ["курсовая работа", "дипломная работа", "студент", "преподаватель", "университет", "факультет"]):
                        if "титульный лист" not in data["required_elements"]:
                            data["required_elements"].append("титульный лист")

                # Шрифты, размеры
                for char in page.chars:
                    if 'fontname' in char:
                        # Очистка и маппинг
                        font_name = re.sub(r'^[A-Z]{6}\+', '', char['fontname'])
                        font_name = re.sub(r'-(Regular|Bold|Italic|BoldItalic)$', '', font_name)
                        fonts.append(font_name)
                    if 'size' in char:
                        sizes.append(char['size'])
                    if 'x0' in char and char['text'].strip():
                        all_x0.append(char['x0'])
                    if 'x1' in char and char['text'].strip():
                        all_x1.append(char['x1'])
                    if 'y0' in char:
                        all_y0.append(char['y0'])
                    if 'y1' in char:
                        all_y1.append(char['y1'])

                # Line spacing: разница y между уникальными y0 (строки)
                y_positions = sorted(set(char['y0'] for char in page.chars if 'y0' in char), reverse=True)
                for i in range(len(y_positions) - 1):
                    diff = y_positions[i] - y_positions[i + 1]  # положительная разница
                    if avg_size * 0.5 < diff < avg_size * 3:  # фильтр: между 0.5x и 3x размера шрифта
                        line_y_diffs.append(diff)

                # Indent: средний x0 первых символов строк (игнор если <10pt)
                first_chars_x = []
                prev_y = None
                for char in sorted(page.chars, key=lambda c: (-c.get('y1', 0), c.get('x0', 0))):  # top-down, left-right
                    if 'y1' in char and (prev_y is None or abs(char['y1'] - prev_y) > avg_size * 0.5):  # новая строка
                        if char.get('size', 0) <= avg_size + 1:  # не заголовок (маленький/средний размер)
                            first_chars_x.append(char['x0'])
                        prev_y = char['y1']
                if first_chars_x:
                    avg_indent_pt = sum(first_chars_x) / len(first_chars_x)
                    indent_x.append(avg_indent_pt / 28.346)  # pt to cm (72 pt/inch, 2.54 cm/inch → 28.346 pt/cm)

            data["introduction_text"] = extract_introduction_from_text(data["full_text"])

            # Аггрегация
            font_counter = Counter(fonts)
            data["font_settings"]["font_family"] = max(font_counter.items(), key=lambda x: x[1])[0] if font_counter else None

            size_counter = Counter(sizes)
            most_common_size = max(size_counter.items(), key=lambda x: x[1])[0] if size_counter else None
            data["font_settings"]["font_size"] = round(most_common_size) if most_common_size else None

            # Line spacing
            avg_diff = sum(line_y_diffs) / len(line_y_diffs) if line_y_diffs else None
            avg_size = data["font_settings"]["font_size"] or 14
            data["font_settings"]["line_spacing"] = round(avg_diff / avg_size, 1) if avg_diff else None

            # Indent: средний
            data["paragraph_indent"] = round(sum(indent_x) / len(indent_x), 2) if indent_x else None

            # Margins: по содержимому (mm)
            pt_to_mm = 0.3528
            if all_x0 and all_x1 and all_y0 and all_y1:
                min_x = min(all_x0)
                max_x = max(all_x1)
                min_y = min(all_y0)
                max_y = max(all_y1)
                width = pdf.pages[0].width if pdf.pages else 595  # A4 default pt
                height = pdf.pages[0].height if pdf.pages else 842
                data["page_margins"] = {
                    "left": round(min_x * pt_to_mm, 1) if min_x > 0 else 0,
                    "right": round((width - max_x) * pt_to_mm, 1) if max_x < width else 0,
                    "top": round((height - max_y) * pt_to_mm, 1) if max_y < height else 0,
                    "bottom": round(min_y * pt_to_mm, 1) if min_y > 0 else 0
                }

            # Добавить "основная часть" если есть главы
            if has_chapters:
                data["required_elements"].append("основная часть")

    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")

    return data


def extract_introduction_from_text(full_text: str) -> str:
    # Улучшенный регекс: захватывает после "введение" до любого следующего заголовка (число, "глава", "заключение" и т.д.)
    match = re.search(r"(введение|introduction)\s*([\s\S]*?)\s*(\d+\.?\s|глава|основная часть|заключение|conclusion|references|приложения|appendix|список|section)", full_text.lower(), re.DOTALL | re.IGNORECASE)
    return match.group(2).strip() if match else full_text[:1000]  # fallback больше текста