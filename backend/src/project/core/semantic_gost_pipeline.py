import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import aiohttp
import pdfplumber

from project.core.document_text_extractor import extract_document_text
from project.core.rule_store import load_rules


class SemanticGostPipeline:
    SECTION_LABELS = {
        "title_page": "Титульный лист",
        "content": "Содержание",
        "definitions": "Определения",
        "abbreviations": "Обозначения и сокращения",
        "introduction": "Введение",
        "conclusion": "Заключение",
        "references": "Список источников",
        "appendix": "Приложение",
    }

    SECTION_CANDIDATES = {
        "content": ["содержание", "оглавление"],
        "definitions": ["определения", "термины и определения"],
        "abbreviations": ["обозначения и сокращения", "сокращения", "условные обозначения"],
        "introduction": ["введение"],
        "conclusion": ["заключение"],
        "references": [
            "список использованных источников",
            "список литературы",
            "библиографический список",
            "список источников",
        ],
        "appendix": ["приложение", "приложения"],
    }

    def __init__(self, ruleset_code: str):
        self.ruleset_code = ruleset_code
        self.rules = load_rules(ruleset_code)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.enable_llm = os.getenv("ENABLE_LLM_CHECKS", "true").lower() == "true"

    def normalize_text(self, text: str) -> str:
        text = text or ""
        text = text.replace("\u00ad", "")
        text = text.replace("\xa0", " ")
        text = text.lower().replace("ё", "е")
        text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def resolve_file_path(self, file_path: str) -> Path:
        raw = Path(file_path)
        candidates: list[Path] = []

        if raw.is_absolute():
            candidates.append(raw)
        else:
            candidates.extend(
                [
                    Path.cwd() / raw,
                    Path("/app") / raw,
                    Path("/app/src") / raw,
                    Path("/app/uploads") / raw.name,
                    Path("uploads") / raw.name,
                ]
            )

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()

        raise FileNotFoundError(
            f"Файл не найден. Исходный путь: {file_path}. Проверены пути: "
            + ", ".join(str(x) for x in candidates)
        )

    def _median_or_none(self, values: list[float]) -> float | None:
        clean = [float(v) for v in values if v is not None]
        if not clean:
            return None
        clean.sort()
        mid = len(clean) // 2
        if len(clean) % 2:
            return round(clean[mid], 2)
        return round((clean[mid - 1] + clean[mid]) / 2, 2)

    def extract_pdf_pages(self, file_path: str) -> tuple[list[dict], dict]:
        resolved_path = self.resolve_file_path(file_path)

        pages = []
        font_sizes = []
        line_ratios = []
        margins_left = []
        margins_right = []
        margins_top = []
        margins_bottom = []
        first_line_indents = []
        page_number_candidates = []

        with pdfplumber.open(str(resolved_path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or "").strip()
                words = page.extract_words(extra_attrs=["size", "fontname"])
                chars = getattr(page, "chars", []) or []

                page_width = float(page.width)
                page_height = float(page.height)

                if words:
                    sizes = [float(w.get("size", 0)) for w in words if w.get("size") is not None]
                    if sizes:
                        font_sizes.extend(sizes)

                    tops = sorted({round(float(w["top"]), 1) for w in words if "top" in w})
                    if len(tops) > 1 and sizes:
                        deltas = [b - a for a, b in zip(tops, tops[1:]) if b - a > 0.5]
                        if deltas:
                            med_size = self._median_or_none(sizes)
                            med_gap = self._median_or_none(deltas)
                            if med_size and med_gap:
                                line_ratios.append(med_gap / med_size)

                    line_map: dict[float, list[dict]] = {}
                    for w in words:
                        top = round(float(w["top"]), 1)
                        line_map.setdefault(top, []).append(w)

                    sorted_tops = sorted(line_map.keys())
                    main_lefts = []

                    for top in sorted_tops:
                        items = line_map[top]
                        sorted_items = sorted(items, key=lambda x: float(x["x0"]))
                        xs = [float(x["x0"]) for x in sorted_items if "x0" in x]
                        if xs:
                            main_lefts.append(xs[0])

                        line_text = " ".join(str(x.get("text", "")).strip() for x in sorted_items).strip()
                        if re.fullmatch(r"\d+", line_text):
                            avg_x0 = sum(float(x["x0"]) for x in sorted_items) / len(sorted_items)
                            avg_x1 = sum(float(x["x1"]) for x in sorted_items) / len(sorted_items)
                            avg_top = sum(float(x["top"]) for x in sorted_items) / len(sorted_items)
                            page_number_candidates.append(
                                {
                                    "page": index,
                                    "text": line_text,
                                    "x0": avg_x0,
                                    "x1": avg_x1,
                                    "top": avg_top,
                                    "page_width": page_width,
                                    "page_height": page_height,
                                }
                            )

                    if main_lefts:
                        base_left = self._median_or_none(main_lefts)
                        for left in main_lefts:
                            if base_left is not None:
                                delta_mm = (left - base_left) * 25.4 / 72.0
                                if 2 <= delta_mm <= 30:
                                    first_line_indents.append(delta_mm)

                    x0s = [float(w["x0"]) for w in words if "x0" in w]
                    x1s = [float(w["x1"]) for w in words if "x1" in w]
                    tops_y = [float(w["top"]) for w in words if "top" in w]
                    bottoms_y = [float(w["bottom"]) for w in words if "bottom" in w]

                    if x0s:
                        margins_left.append(min(x0s) * 25.4 / 72.0)
                    if x1s:
                        margins_right.append((page_width - max(x1s)) * 25.4 / 72.0)
                    if tops_y:
                        margins_top.append(min(tops_y) * 25.4 / 72.0)
                    if bottoms_y:
                        margins_bottom.append((page_height - max(bottoms_y)) * 25.4 / 72.0)

                pages.append(
                    {
                        "page": index,
                        "text": text,
                        "normalized": self.normalize_text(text),
                        "chars": chars,
                    }
                )

        fonts = []
        for page in pages[: min(5, len(pages))]:
            for ch in page["chars"]:
                name = str(ch.get("fontname", "")).lower()
                if name:
                    fonts.append(name)

        font_family = None
        if fonts:
            top_font = Counter(fonts).most_common(1)[0][0]
            if "times" in top_font:
                font_family = "Times New Roman"
            elif "arial" in top_font:
                font_family = "Arial"
            elif "calibri" in top_font:
                font_family = "Calibri"
            else:
                font_family = top_font

        return pages, {
            "font_family": font_family,
            "font_size_pt": self._median_or_none(font_sizes),
            "line_spacing": self._median_or_none(line_ratios),
            "paragraph_first_line_indent_mm": self._median_or_none(first_line_indents),
            "margins_mm": {
                "left": self._median_or_none(margins_left),
                "right": self._median_or_none(margins_right),
                "top": self._median_or_none(margins_top),
                "bottom": self._median_or_none(margins_bottom),
            },
            "page_number_candidates": page_number_candidates,
            "source": "pdf_layout_heuristics",
            "confidence": "medium",
        }

    def extract_docx_pages(self, file_path: str) -> tuple[list[dict], dict]:
        from docx import Document

        resolved_path = self.resolve_file_path(file_path)
        doc = Document(str(resolved_path))

        paragraphs = [p for p in doc.paragraphs if p.text and p.text.strip()]
        text = "\n".join(p.text.strip() for p in paragraphs)

        font_names = []
        font_sizes = []
        line_spacings = []
        first_line_indents = []
        left_margins = []
        right_margins = []
        top_margins = []
        bottom_margins = []

        for p in paragraphs:
            pf = p.paragraph_format

            if pf.line_spacing is not None:
                try:
                    line_spacings.append(float(pf.line_spacing))
                except Exception:
                    pass

            if pf.first_line_indent is not None:
                try:
                    mm = float(pf.first_line_indent.mm)
                    if 2 <= mm <= 30:
                        first_line_indents.append(mm)
                except Exception:
                    try:
                        mm = float(pf.first_line_indent.pt) * 25.4 / 72.0
                        if 2 <= mm <= 30:
                            first_line_indents.append(mm)
                    except Exception:
                        pass

            for run in p.runs:
                if run.font.name:
                    font_names.append(str(run.font.name))
                if run.font.size:
                    try:
                        font_sizes.append(float(run.font.size.pt))
                    except Exception:
                        pass

        for section in doc.sections:
            try:
                left_margins.append(float(section.left_margin.mm))
            except Exception:
                pass
            try:
                right_margins.append(float(section.right_margin.mm))
            except Exception:
                pass
            try:
                top_margins.append(float(section.top_margin.mm))
            except Exception:
                pass
            try:
                bottom_margins.append(float(section.bottom_margin.mm))
            except Exception:
                pass

        font_family = Counter(font_names).most_common(1)[0][0] if font_names else None

        return (
            [{"page": 1, "text": text, "normalized": self.normalize_text(text)}],
            {
                "font_family": font_family,
                "font_size_pt": self._median_or_none(font_sizes),
                "line_spacing": self._median_or_none(line_spacings),
                "paragraph_first_line_indent_mm": self._median_or_none(first_line_indents),
                "margins_mm": {
                    "left": self._median_or_none(left_margins),
                    "right": self._median_or_none(right_margins),
                    "top": self._median_or_none(top_margins),
                    "bottom": self._median_or_none(bottom_margins),
                },
                "page_number_candidates": [],
                "source": "docx_styles",
                "confidence": "high",
            },
        )

    def extract_pages(self, file_path: str) -> tuple[list[dict], dict]:
        resolved = self.resolve_file_path(file_path)
        suffix = resolved.suffix.lower()

        if suffix == ".pdf":
            return self.extract_pdf_pages(str(resolved))

        if suffix == ".docx":
            return self.extract_docx_pages(str(resolved))

        text = extract_document_text(str(resolved))
        return (
            [{"page": 1, "text": text, "normalized": self.normalize_text(text)}],
            {
                "font_family": None,
                "font_size_pt": None,
                "line_spacing": None,
                "paragraph_first_line_indent_mm": None,
                "margins_mm": {"left": None, "right": None, "top": None, "bottom": None},
                "page_number_candidates": [],
                "source": "text_only",
                "confidence": "low",
            },
        )

    def is_heading_line(self, line: str, candidate: str) -> bool:
        l = self.normalize_text(line)
        c = self.normalize_text(candidate)

        if not l or len(l) > 120:
            return False

        if re.fullmatch(r"\d+(?:\.\d+)*", l):
            return False

        if re.search(r"\.{3,}\s*\d+$", l):
            return False

        if l == c:
            return True
        if l.startswith(c + " "):
            return True
        if l.startswith(c + "."):
            return True
        if re.fullmatch(rf"{re.escape(c)}\s+[а-яa-z0-9ivxlcdm\-]+", l):
            return True

        return False

    def detect_structure(self, pages: list[dict]) -> dict:
        structure = {}
        if pages:
            structure["title_page"] = 1

        for page in pages:
            raw_lines = [x.strip() for x in page["text"].splitlines() if x.strip()]
            for key, variants in self.SECTION_CANDIDATES.items():
                if key in structure:
                    continue
                for line in raw_lines:
                    if any(self.is_heading_line(line, variant) for variant in variants):
                        structure[key] = page["page"]
                        break

        return structure

    def collect_section_text(self, pages: list[dict], structure: dict, section_name: str) -> str:
        if not pages or section_name not in structure:
            return ""

        start_page = structure[section_name]
        later_pages = [p for name, p in structure.items() if isinstance(p, int) and p > start_page]
        end_page = min(later_pages) - 1 if later_pages else pages[-1]["page"]

        chunk = [p["text"] for p in pages if start_page <= p["page"] <= end_page]
        return "\n".join(chunk).strip()

    def extract_references_entries(self, references_text: str) -> list[str]:
        if not references_text.strip():
            return []

        text = references_text.replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)

        entries = re.split(r"(?m)^\s*(\d+)[\.\)]\s+", text)
        if len(entries) <= 1:
            entries = re.split(r"(?m)^\s*\[(\d+)\]\s+", text)

        if len(entries) > 1:
            result = []
            i = 1
            while i < len(entries):
                if i + 1 < len(entries):
                    block = entries[i + 1].strip()
                    if block:
                        result.append(block)
                i += 2
            if result:
                return result

        lines = [x.strip() for x in text.splitlines() if x.strip()]
        merged = []
        current = []

        for line in lines:
            if re.match(r"^\d+[\.\)]\s+", line) or re.match(r"^\[\d+\]\s+", line):
                if current:
                    merged.append(" ".join(current).strip())
                    current = []
                current.append(re.sub(r"^\d+[\.\)]\s+|^\[\d+\]\s+", "", line).strip())
            else:
                current.append(line)

        if current:
            merged.append(" ".join(current).strip())

        return [x for x in merged if x]

    def build_context(self, pages: list[dict], metrics: dict, structure: dict) -> dict:
        references_text = self.collect_section_text(pages, structure, "references")
        content_text = self.collect_section_text(pages, structure, "content")
        introduction_text = self.collect_section_text(pages, structure, "introduction")
        conclusion_text = self.collect_section_text(pages, structure, "conclusion")

        references_entries = self.extract_references_entries(references_text)

        return {
            "metrics": metrics,
            "structure": structure,
            "text": {
                "full": "\n".join(p["text"] for p in pages),
                "content": content_text,
                "introduction": introduction_text,
                "conclusion": conclusion_text,
                "references": references_text,
            },
            "references": {
                "count": len(references_entries),
                "entries": references_entries,
            },
            "pages": pages,
        }

    def build_finding(
        self,
        rule: dict,
        status: str,
        page: int | None,
        location: str,
        section: str,
        problem: str,
        evidence: str,
        fix: str,
        actual_value: Any = None,
    ) -> dict:
        full_rule_title = str(rule.get("description") or rule.get("title") or "").strip()

        return {
            "rule_code": rule.get("rule_number") or rule.get("id"),
            "rule_title": full_rule_title,
            "status": status,
            "page": page,
            "location": location,
            "section": section,
            "problem": problem,
            "evidence": evidence,
            "fix": fix,
            "expected_value": rule.get("expected"),
            "actual_value": actual_value,
        }

    def compare_number(self, actual: float | None, expected: float | int | None, tolerance: float) -> bool | None:
        if actual is None or expected is None:
            return None
        try:
            return abs(float(actual) - float(expected)) <= tolerance
        except Exception:
            return None

    def compare_text(self, actual: str | None, expected: str | None) -> bool | None:
        if actual is None or expected is None:
            return None
        a = self.normalize_text(str(actual))
        e = self.normalize_text(str(expected))
        if not a or not e:
            return None
        return a == e or a in e or e in a

    async def call_llm(self, system_prompt: str, user_prompt: str) -> dict | None:
        if not self.enable_llm or not self.openai_api_key:
            return None

        url = f"{self.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status >= 400:
                        return None
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception:
            return None

    async def execute_metric_rule(self, rule: dict, ctx: dict) -> dict:
        target = rule.get("target")
        expected = rule.get("expected")
        metrics = ctx["metrics"]

        tolerances = {
            "font_size_pt": 0.5,
            "line_spacing": 0.3,
            "paragraph_first_line_indent_mm": 2.0,
        }

        if target == "font_family":
            actual = metrics.get("font_family")
            ok = self.compare_text(actual, expected)
            if ok is None:
                return self.build_finding(rule, "manual_check", None, "Документ", "format", "", "Недостаточно данных для проверки шрифта.", "", actual)
            if ok:
                return self.build_finding(rule, "passed", None, "Документ", "format", "", f"Шрифт соответствует требованию: {actual}.", "", actual)
            return self.build_finding(rule, "failed", None, "Документ", "format", "Шрифт не соответствует требованию.", f"Ожидалось: {expected}. Обнаружено: {actual}.", "Использовать требуемый шрифт.", actual)

        if target in {"font_size_pt", "line_spacing", "paragraph_first_line_indent_mm"}:
            actual = metrics.get(target)
            ok = self.compare_number(actual, expected, tolerances[target])
            if ok is None:
                return self.build_finding(rule, "manual_check", None, "Документ", "format", "", "Недостаточно данных для проверки параметра форматирования.", "", actual)
            if ok:
                return self.build_finding(rule, "passed", None, "Документ", "format", "", f"Параметр {target} соответствует требованию.", "", actual)
            return self.build_finding(rule, "failed", None, "Документ", "format", f"Параметр {target} не соответствует требованию.", f"Ожидалось: {expected}. Обнаружено: {actual}.", "Исправить параметр форматирования.", actual)

        if target == "margins_mm":
            actual = metrics.get("margins_mm") or {}
            if not actual or all(v is None for v in actual.values()):
                return self.build_finding(rule, "manual_check", None, "Документ", "format", "", "Недостаточно данных для проверки полей страницы.", "", actual)

            mismatches = []
            for key in ["left", "right", "top", "bottom"]:
                ok = self.compare_number(actual.get(key), expected.get(key) if isinstance(expected, dict) else None, 2.0)
                if ok is False:
                    mismatches.append(f"{key}: ожидалось {expected.get(key)} мм, найдено {actual.get(key)} мм")

            if mismatches:
                return self.build_finding(rule, "failed", None, "Документ", "format", "Поля страницы не соответствуют требованию.", "; ".join(mismatches), "Установить требуемые поля страницы.", actual)

            return self.build_finding(rule, "passed", None, "Документ", "format", "", "Поля страницы соответствуют требованию.", "", actual)

        return self.build_finding(rule, "manual_check", None, "Документ", "document", "", "Для этого metric_rule нет обработчика.", "", None)

    async def execute_section_rule(self, rule: dict, ctx: dict) -> dict:
        target = str(rule.get("target") or "")
        structure = ctx["structure"]

        if not target.startswith("section:"):
            return self.build_finding(rule, "manual_check", None, "Документ", "document", "", "Некорректная цель section_rule.", "", None)

        section_name = target.split(":", 1)[1]
        exists = section_name in structure
        label = self.SECTION_LABELS.get(section_name, section_name)
        operator = rule.get("operator")

        if operator == "optional":
            if exists:
                return self.build_finding(rule, "passed", structure[section_name], label, section_name, "", f"Необязательный раздел найден на странице {structure[section_name]}.", "", True)
            return self.build_finding(rule, "not_applicable", None, label, section_name, "", "Раздел необязателен и не обнаружен.", "", False)

        if exists:
            return self.build_finding(rule, "passed", structure[section_name], label, section_name, "", f"Раздел найден на странице {structure[section_name]}.", "", True)

        return self.build_finding(rule, "failed", None, label, section_name, f"Не найден обязательный раздел «{label}».", f"В документе не обнаружен заголовок раздела «{label}».", f"Добавить раздел «{label}».", False)

    async def execute_count_rule(self, rule: dict, ctx: dict) -> dict:
        target = rule.get("target")
        expected = rule.get("expected")
        operator = rule.get("operator")

        if target == "reference:count":
            actual = ctx["references"]["count"]
            page = ctx["structure"].get("references")

            if actual is None or expected is None:
                return self.build_finding(rule, "manual_check", page, "Список источников", "references", "", "Недостаточно данных для проверки количества источников.", "", actual)

            if operator == "ge":
                if actual >= expected:
                    return self.build_finding(rule, "passed", page, "Список источников", "references", "", f"Количество источников соответствует требованию. Найдено: {actual}.", "", actual)
                return self.build_finding(rule, "failed", page, "Список источников", "references", "Количество источников меньше требуемого минимума.", f"Ожидалось не менее {expected}. Обнаружено: {actual}.", "Увеличить количество источников.", actual)

        return self.build_finding(rule, "manual_check", None, "Документ", "document", "", "Для этого count_rule нет обработчика.", "", None)

    async def execute_reference_rule(self, rule: dict, ctx: dict) -> dict:
        target = rule.get("target")
        expected = rule.get("expected")
        refs = ctx["references"]["entries"]
        page = ctx["structure"].get("references")

        if target == "reference:web_access_date":
            if not refs:
                return self.build_finding(rule, "not_applicable", page, "Список источников", "references", "", "Список источников отсутствует или не распознан.", "", None)

            checked = 0
            invalid = 0
            for entry in refs:
                entry_n = self.normalize_text(entry)
                if "url:" in entry_n or "http://" in entry_n or "https://" in entry_n:
                    checked += 1
                    if self.normalize_text(str(expected)) not in entry_n:
                        invalid += 1

            if checked == 0:
                return self.build_finding(rule, "not_applicable", page, "Список источников", "references", "", "Электронные ресурсы явно не обнаружены.", "", 0)

            if invalid > 0:
                return self.build_finding(rule, "failed", page, "Список источников", "references", "Часть электронных ресурсов оформлена неполно.", f"Электронных ресурсов: {checked}. Без поля «{expected}»: {invalid}.", "Добавить обязательное поле для электронных ресурсов.", {"checked": checked, "invalid": invalid})

            return self.build_finding(rule, "passed", page, "Список источников", "references", "", f"Электронные ресурсы содержат обязательное поле «{expected}». Количество: {checked}.", "", {"checked": checked, "invalid": 0})

        return self.build_finding(rule, "manual_check", page, "Документ", "document", "", "Для этого reference_rule нет обработчика.", "", None)

    async def execute_llm_semantic_check(
        self,
        rule: dict,
        location: str,
        raw_text: str,
        missing_hard: list[str],
        missing_soft: list[str],
        page: int | None,
        section: str,
    ) -> dict | None:
        if not self.enable_llm or not self.openai_api_key:
            return None

        snippet = raw_text[:15000]
        system_prompt = (
            "Ты эксперт по проверке документов на соответствие стандартам. "
            "Оценивай строго по тексту. "
            "Если обязательные смысловые элементы действительно присутствуют, ставь passed. "
            "Если отсутствуют важные элементы, ставь failed. "
            "Если есть частичное соответствие, ставь warning. "
            "Если по тексту невозможно сделать надёжный вывод, ставь manual_check. "
            "Отвечай только JSON."
        )

        user_payload = {
            "rule_title": rule.get("title"),
            "rule_description": rule.get("description"),
            "section_name": location,
            "heuristic_missing_hard": missing_hard,
            "heuristic_missing_soft": missing_soft,
            "section_text": snippet,
            "required_output": {
                "status": "passed|warning|failed|manual_check",
                "problem": "string",
                "evidence": "string",
                "fix": "string"
            }
        }

        result = await self.call_llm(
            system_prompt=system_prompt,
            user_prompt=json.dumps(user_payload, ensure_ascii=False),
        )

        if not isinstance(result, dict):
            return None

        status = result.get("status")
        if status not in {"passed", "warning", "failed", "manual_check"}:
            return None

        return self.build_finding(
            rule=rule,
            status=status,
            page=page,
            location=location,
            section=section,
            problem=str(result.get("problem") or ""),
            evidence=str(result.get("evidence") or "LLM semantic check"),
            fix=str(result.get("fix") or ""),
            actual_value={
                "missing_hard": missing_hard,
                "missing_soft": missing_soft,
                "llm": True,
            },
        )

    async def execute_content_rule(self, rule: dict, ctx: dict) -> dict:
        target = rule.get("target")
        hard = [self.normalize_text(x) for x in (rule.get("expected") or [])]
        soft = [self.normalize_text(x) for x in ((rule.get("options") or {}).get("soft_items", []))]

        if target == "content:toc":
            text = self.normalize_text(ctx["text"]["content"])
            raw_text = ctx["text"]["content"]
            page = ctx["structure"].get("content")
            location = "Содержание"
            section = "content"
        elif target == "content:introduction":
            text = self.normalize_text(ctx["text"]["introduction"])
            raw_text = ctx["text"]["introduction"]
            page = ctx["structure"].get("introduction")
            location = "Введение"
            section = "introduction"
        elif target == "content:conclusion":
            text = self.normalize_text(ctx["text"]["conclusion"])
            raw_text = ctx["text"]["conclusion"]
            page = ctx["structure"].get("conclusion")
            location = "Заключение"
            section = "conclusion"
        else:
            return self.build_finding(rule, "manual_check", None, "Документ", "document", "", "Для этого content_rule нет обработчика.", "", None)

        if not raw_text:
            return self.build_finding(rule, "not_applicable", page, location, section, "", f"Раздел «{location}» отсутствует или не распознан.", "", None)

        missing_hard = [x for x in hard if x not in text]
        missing_soft = [x for x in soft if x not in text]

        llm_result = await self.execute_llm_semantic_check(
            rule=rule,
            location=location,
            raw_text=raw_text,
            missing_hard=missing_hard,
            missing_soft=missing_soft,
            page=page,
            section=section,
        )
        if llm_result is not None:
            return llm_result

        if missing_hard:
            return self.build_finding(rule, "failed", page, location, section, f"В разделе «{location}» отсутствуют обязательные элементы.", f"Не найдены: {', '.join(missing_hard)}.", f"Дополнить раздел «{location}».", {"missing_hard": missing_hard, "missing_soft": missing_soft})

        if missing_soft:
            return self.build_finding(rule, "warning", page, location, section, f"В разделе «{location}» отсутствуют некоторые желательные элементы.", f"Не найдены: {', '.join(missing_soft)}.", f"Проверить полноту раздела «{location}».", {"missing_hard": [], "missing_soft": missing_soft})

        return self.build_finding(rule, "passed", page, location, section, "", f"Раздел «{location}» содержит ожидаемые элементы.", "", {"missing_hard": [], "missing_soft": []})

    async def execute_object_rule(self, rule: dict, ctx: dict) -> dict:
        target = rule.get("target")

        if target == "page:numbering":
            candidates = ctx["metrics"].get("page_number_candidates", [])
            for item in candidates:
                if item["page"] == 1 and item["text"] == "1":
                    return self.build_finding(rule, "failed", 1, "Титульный лист", "title_page", "На титульном листе обнаружен номер страницы.", "Титульный лист включается в общую нумерацию, но номер на нем не проставляют.", "Убрать номер страницы с титульного листа.", True)
            return self.build_finding(rule, "passed", 1, "Титульный лист", "title_page", "", "На титульном листе номер страницы не обнаружен.", "", False)

        if target == "figure:reference":
            return self.build_finding(rule, "manual_check", None, "Документ", "figures", "", "Для проверки ссылок на рисунки нужен анализ рисунков и ссылок в тексте.", "", None)

        if target == "table:reference":
            return self.build_finding(rule, "manual_check", None, "Документ", "tables", "", "Для проверки ссылок на таблицы нужен анализ таблиц и ссылок в тексте.", "", None)

        if target == "table:continuation":
            return self.build_finding(rule, "manual_check", None, "Документ", "tables", "", "Для проверки переноса таблиц нужен анализ макета таблиц.", "", None)

        if target == "formula:numbering":
            return self.build_finding(rule, "manual_check", None, "Документ", "formulas", "", "Для проверки нумерации формул нужен анализ формул и ссылок на них.", "", None)

        return self.build_finding(rule, "manual_check", None, "Документ", "document", "", "Для этого object_rule нет обработчика.", "", None)

    async def try_llm_for_any_rule(self, rule: dict, ctx: dict) -> dict | None:
        if not self.enable_llm or not self.openai_api_key:
            return None

        description = str(rule.get("description") or rule.get("title") or "").strip()
        full_text = ctx["text"]["full"][:18000]

        structure = ctx["structure"]
        section_texts = {
            "content": ctx["text"]["content"][:6000],
            "introduction": ctx["text"]["introduction"][:6000],
            "conclusion": ctx["text"]["conclusion"][:6000],
            "references": ctx["text"]["references"][:6000],
        }

        system_prompt = (
            "Ты эксперт по проверке документов на соответствие нормативным требованиям. "
            "Тебе даётся правило стандарта и текст документа. "
            "Нужно честно определить, нарушено правило, выполнено или недостаточно данных. "
            "Отвечай только JSON без markdown. "
            "Допустимые status: passed, warning, failed, manual_check. "
            "Если правило нельзя надёжно проверить по тексту документа, возвращай manual_check."
        )

        user_payload = {
            "rule_code": rule.get("rule_number") or rule.get("id"),
            "rule_title": rule.get("title"),
            "rule_description": description,
            "rule_category": rule.get("category"),
            "rule_check_type": rule.get("check_type"),
            "document_structure": structure,
            "section_texts": section_texts,
            "document_excerpt": full_text,
            "required_output": {
                "status": "passed|warning|failed|manual_check",
                "problem": "string",
                "evidence": "string",
                "fix": "string",
                "location": "string",
                "section": "string"
            }
        }

        result = await self.call_llm(
            system_prompt=system_prompt,
            user_prompt=json.dumps(user_payload, ensure_ascii=False),
        )

        if not isinstance(result, dict):
            return None

        status = result.get("status")
        if status not in {"passed", "warning", "failed", "manual_check"}:
            return None

        location = str(result.get("location") or "Документ")
        section = str(result.get("section") or "document")

        return self.build_finding(
            rule=rule,
            status=status,
            page=ctx["structure"].get(section) if section in ctx["structure"] else None,
            location=location,
            section=section,
            problem=str(result.get("problem") or ""),
            evidence=str(result.get("evidence") or "LLM semantic check"),
            fix=str(result.get("fix") or ""),
            actual_value={"llm": True},
        )

    async def execute_manual_check(self, rule: dict, ctx: dict) -> dict:
        llm_result = await self.try_llm_for_any_rule(rule, ctx)
        if llm_result is not None:
            return llm_result

        return self.build_finding(
            rule,
            "manual_check",
            None,
            "Документ",
            "document",
            "",
            "Для этого правила пока доступна только ручная проверка.",
            "",
            None,
        )

    async def execute_rule(self, rule: dict, ctx: dict) -> dict:
        check_type = rule.get("check_type")

        if check_type == "metric_rule":
            return await self.execute_metric_rule(rule, ctx)

        if check_type == "section_rule":
            return await self.execute_section_rule(rule, ctx)

        if check_type == "count_rule":
            return await self.execute_count_rule(rule, ctx)

        if check_type == "reference_rule":
            return await self.execute_reference_rule(rule, ctx)

        if check_type == "content_rule":
            return await self.execute_content_rule(rule, ctx)

        if check_type == "object_rule":
            return await self.execute_object_rule(rule, ctx)

        return await self.execute_manual_check(rule, ctx)

    def deduplicate_findings(self, findings: list[dict]) -> list[dict]:
        unique = []
        seen = set()

        for f in findings:
            key = (
                f.get("rule_code"),
                f.get("rule_title"),
                f.get("status"),
                f.get("page"),
                f.get("location"),
                f.get("problem"),
                f.get("evidence"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)

        return unique

    def calculate_overall(self, findings: list[dict]) -> tuple[float, str]:
        weights = {
            "passed": 1.0,
            "warning": 0.65,
            "failed": 0.2,
        }

        scored = [weights[f["status"]] for f in findings if f["status"] in weights]
        if not scored:
            return 0.0, "данных недостаточно"

        value = round(sum(scored) / len(scored), 4)

        if value >= 0.85:
            return value, "высокое соответствие"
        if value >= 0.65:
            return value, "среднее соответствие"
        return value, "низкое соответствие"

    def build_recommendation(self, findings: list[dict]) -> str:
        failed = [f for f in findings if f["status"] == "failed" and f["fix"]]
        warning = [f for f in findings if f["status"] == "warning" and f["fix"]]

        if failed:
            return " ".join(x["fix"] for x in failed[:3]).strip()

        if warning:
            return " ".join(x["fix"] for x in warning[:3]).strip()

        return "Явных нарушений по автоматически проверяемым правилам не обнаружено."

    async def run(self, file_path: str) -> dict:
        pages, metrics = self.extract_pages(file_path)
        structure = self.detect_structure(pages)
        ctx = self.build_context(pages, metrics, structure)

        findings = []
        for rule in self.rules:
            if not isinstance(rule, dict):
                continue
            findings.append(await self.execute_rule(rule, ctx))

        findings = self.deduplicate_findings(findings)
        overall_score, score_label = self.calculate_overall(findings)

        status_counts = {
            "passed": sum(1 for f in findings if f["status"] == "passed"),
            "warning": sum(1 for f in findings if f["status"] == "warning"),
            "failed": sum(1 for f in findings if f["status"] == "failed"),
            "manual_check": sum(1 for f in findings if f["status"] == "manual_check"),
            "not_applicable": sum(1 for f in findings if f["status"] == "not_applicable"),
        }

        problem_sections_counter: dict[str, int] = {}
        for f in findings:
            if f["status"] in {"warning", "failed"}:
                section = f["section"]
                problem_sections_counter[section] = problem_sections_counter.get(section, 0) + 1

        top_problem_sections = [
            k for k, _ in sorted(problem_sections_counter.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

        visible_findings = [
            f for f in findings
            if f["status"] in {"failed", "warning"}
        ]

        return {
            "ruleset_code": self.ruleset_code,
            "document_kind": "document",
            "total_pages": len(pages),
            "rules_count": len([r for r in self.rules if isinstance(r, dict)]),
            "overall_score": overall_score,
            "score_label": score_label,
            "status": "ok" if overall_score >= 0.85 else "warning" if overall_score >= 0.65 else "problem",
            "short_recommendation": self.build_recommendation(findings),
            "summary": {
                "total_checks": len(findings),
                "passed_checks": status_counts["passed"],
                "failed_checks": status_counts["failed"],
                "warning_checks": status_counts["warning"],
                "manual_checks": status_counts["manual_check"],
                "not_applicable_checks": status_counts["not_applicable"],
                "status_counts": status_counts,
                "top_problem_sections": top_problem_sections,
                "sections_found": structure,
                "format_metrics": metrics,
                "llm_enabled": bool(self.enable_llm and self.openai_api_key),
                "llm_model": self.openai_model if self.enable_llm and self.openai_api_key else None,
            },
            "findings": visible_findings,
        }