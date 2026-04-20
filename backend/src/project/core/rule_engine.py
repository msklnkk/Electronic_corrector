from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import pdfplumber
from project.core.rule_store import load_rules


def _repair_text(text: Any) -> str:
    value = str(text or "")
    if not value:
        return ""

    def suspicious_score(s: str) -> int:
        suspicious_chars = (
            0x0420,  # Р
            0x0421,  # С
            0x0403,
            0x0402,
            0x0404,
            0x045E,
        )
        score = sum(s.count(chr(cp)) for cp in suspicious_chars)
        score += s.count("в" + chr(0x0402))
        return score

    best = value
    best_score = suspicious_score(best)

    if best_score == 0:
        return best

    current = value
    for _ in range(3):
        improved = False
        for encoding in ("cp1251", "latin1"):
            try:
                repaired = current.encode(encoding).decode("utf-8")
            except Exception:
                continue
            repaired_score = suspicious_score(repaired)
            if repaired_score < best_score:
                best = repaired
                best_score = repaired_score
                current = repaired
                improved = True
        if not improved:
            break

    return best


def _norm(text: str) -> str:
    text = _repair_text(text)
    text = text.replace("\u00ad", "").replace("\xa0", " ")
    text = text.lower().replace("ё", "е")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fb(rule: dict, status: str, page: int | None, location: str, section: str,
        problem: str, evidence: str, fix: str, actual_value: Any = None) -> dict:
    title = _display_rule_title(rule)
    return {
        "rule_code": rule.get("rule_number") or rule.get("id"),
        "rule_title": _repair_text(title),
        "status": status,
        "page": page,
        "location": _repair_text(location),
        "section": section,
        "problem": _repair_text(problem),
        "evidence": _repair_text(evidence),
        "fix": _repair_text(fix),
        "expected_value": rule.get("expected"),
        "actual_value": actual_value,
    }


def _display_rule_title(rule: dict) -> str:
    raw = _repair_text(rule.get("description") or rule.get("title") or "").strip()
    check_type = str(rule.get("check_type") or "")
    target = str(rule.get("target") or "")
    expected = rule.get("expected")

    if check_type == "metric_rule":
        if target == "font_family":
            return f"Требование к шрифту: {expected}"
        if target == "font_size_pt":
            return f"Требование к размеру шрифта: {expected} pt"
        if target == "line_spacing":
            return f"Требование к межстрочному интервалу: {expected}"
        if target == "paragraph_first_line_indent_mm":
            return f"Требование к абзацному отступу: {expected} мм"
        if target == "margins_mm":
            return "Требование к полям страницы"

    if check_type == "count_rule" and target == "reference:count":
        return "Требование к количеству источников"

    if check_type == "section_rule" and target.startswith("section:"):
        section_name = target.split(":", 1)[1]
        label = SECTION_LABELS.get(section_name, section_name)
        return f"Требование к разделу «{label}»"

    if check_type == "content_rule":
        mapping = {
            "content:toc": "Требование к содержанию",
            "content:introduction": "Требование к разделу «Введение»",
            "content:conclusion": "Требование к разделу «Заключение»",
        }
        if target in mapping:
            return mapping[target]

    if raw:
        raw = raw.rstrip(" ,;:.-")
        if len(raw) > 180:
            return raw[:177].rstrip() + "..."
        return raw

    return "Проверяемое правило"


def _canonical_font_name(name: Any) -> str | None:
    raw = _repair_text(name).strip()
    if not raw:
        return None
    low = raw.lower()
    if "times" in low:
        return "Times New Roman"
    if "arial" in low:
        return "Arial"
    if "calibri" in low:
        return "Calibri"
    if "cambria math" in low:
        return "Cambria Math"
    if "courier" in low:
        return "Courier New"
    return raw


def resolve_section_operators(rules: list[dict]) -> dict[str, str]:

    section_ops: dict[str, set[str]] = defaultdict(set)
    for rule in rules:
        if rule.get("check_type") == "section_rule":
            target = str(rule.get("target") or "")
            if target.startswith("section:"):
                section_name = target.split(":", 1)[1]
                section_ops[section_name].add(rule.get("operator", "required"))
    result = {}
    for section, ops in section_ops.items():
        result[section] = "optional" if "optional" in ops else "required"
    return result



class MetricChecker:
    TOLERANCES = {
        "font_size_pt": 0.5,
        "line_spacing": 0.3,
        "paragraph_first_line_indent_mm": 2.0,
        "margins_mm": 2.0,
    }

    def _font_size_outliers(self, expected: Any, metrics: dict) -> list[dict]:
        outliers: list[dict] = []
        profiles = metrics.get("font_size_profile") or []
        if expected is None:
            return outliers

        for profile in profiles:
            if profile.get("role") in {"math", "code"}:
                continue
            dominant = profile.get("dominant")
            if dominant is None:
                continue
            try:
                if abs(float(dominant) - float(expected)) <= self.TOLERANCES["font_size_pt"]:
                    continue
            except Exception:
                continue
            outliers.append(profile)
        return outliers

    def _font_family_outliers(self, expected: Any, metrics: dict) -> list[dict]:
        outliers: list[dict] = []
        profiles = metrics.get("font_family_profile") or []
        expected_norm = _norm(str(expected or ""))
        if not expected_norm:
            return outliers

        for profile in profiles:
            if profile.get("role") in {"math", "code"}:
                continue
            dominant = _norm(str(profile.get("dominant") or ""))
            if not dominant:
                continue
            if dominant == expected_norm or dominant in expected_norm or expected_norm in dominant:
                continue
            outliers.append(profile)
        return outliers

    def _format_profile_locations(self, items: list[dict], kind: str) -> str:
        parts: list[str] = []
        for item in items[:6]:
            if kind == "page":
                parts.append(f"стр. {item.get('page')}: {item.get('dominant')}")
            else:
                parts.append(f"абз. {item.get('paragraph')}: {item.get('dominant')}")
        return "; ".join(parts)

    def check(self, rule: dict, metrics: dict) -> dict:
        target = rule.get("target")
        expected = rule.get("expected")

        if target == "font_family":
            actual = metrics.get("font_family")
            if actual is None:
                return _fb(rule, "manual_check", None, "Документ", "format", "", "Нет данных о шрифте.", "", actual)
            a, e = _norm(str(actual)), _norm(str(expected or ""))
            outliers = self._font_family_outliers(expected, metrics)
            ok = a == e or a in e or e in a
            if ok and not outliers:
                return _fb(rule, "passed", None, "Документ", "format", "", f"Шрифт соответствует: {actual}.", "", actual)
            if outliers:
                kind = "page" if "page" in outliers[0] else "paragraph"
                evidence = self._format_profile_locations(outliers, kind)
                return _fb(
                    rule,
                    "failed",
                    outliers[0].get("page"),
                    "Документ",
                    "format",
                    "Шрифт не одинаков по документу.",
                    f"Ожидался: {expected}. Отклонения: {evidence}.",
                    f"Привести весь текст к шрифту {expected}.",
                    actual,
                )
            return _fb(rule, "failed", None, "Документ", "format", "Шрифт не соответствует.", f"Ожидалось: {expected}. Найдено: {actual}.", f"Использовать: {expected}.", actual)

        if target in ("font_size_pt", "line_spacing", "paragraph_first_line_indent_mm"):
            actual = metrics.get(target)
            tol = self.TOLERANCES[target]
            if actual is None or expected is None:
                return _fb(rule, "manual_check", None, "Документ", "format", "", f"Нет данных для {target}.", "", actual)
            if target == "font_size_pt":
                outliers = self._font_size_outliers(expected, metrics)
                if outliers:
                    kind = "page" if "page" in outliers[0] else "paragraph"
                    evidence = self._format_profile_locations(outliers, kind)
                    return _fb(
                        rule,
                        "failed",
                        outliers[0].get("page"),
                        "Документ",
                        "format",
                        "Размер шрифта не одинаков по документу.",
                        f"Ожидался: {expected} pt. Отклонения: {evidence}.",
                        f"Привести весь текст к {expected} pt.",
                        actual,
                    )
            ok = abs(float(actual) - float(expected)) <= tol
            if ok:
                return _fb(rule, "passed", None, "Документ", "format", "", f"{target} соответствует: {actual}.", "", actual)
            return _fb(rule, "failed", None, "Документ", "format", f"{target} не соответствует.", f"Ожидалось: {expected}. Найдено: {actual}.", f"Исправить {target}.", actual)

        if target == "margins_mm":
            actual = metrics.get("margins_mm") or {}
            if not actual or all(v is None for v in actual.values()):
                return _fb(rule, "manual_check", None, "Документ", "format", "", "Нет данных о полях.", "", actual)
            if not isinstance(expected, dict):
                return _fb(rule, "manual_check", None, "Документ", "format", "", "Ожидаемые поля не заданы.", "", actual)
            mismatches = []
            for key in ("left", "right", "top", "bottom"):
                ev, av = expected.get(key), actual.get(key)
                if ev is not None and av is not None and abs(float(av) - float(ev)) > self.TOLERANCES["margins_mm"]:
                    mismatches.append(f"{key}: ожидалось {ev} мм, найдено {av} мм")
            if mismatches:
                return _fb(rule, "failed", None, "Документ", "format", "Поля не соответствуют.", "; ".join(mismatches), "Установить требуемые поля.", actual)
            return _fb(rule, "passed", None, "Документ", "format", "", "Поля соответствуют.", "", actual)

        return _fb(rule, "manual_check", None, "Документ", "format", "", "Нет обработчика для metric_rule.", "", None)


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


class SectionChecker:
    def check(self, rule: dict, structure: dict, effective_operators: dict[str, str]) -> dict:
        target = str(rule.get("target") or "")
        if not target.startswith("section:"):
            return _fb(rule, "manual_check", None, "Документ", "document", "", "Некорректная цель section_rule.", "", None)

        section_name = target.split(":", 1)[1]
        exists = section_name in structure
        label = SECTION_LABELS.get(section_name, section_name)

        effective_op = effective_operators.get(section_name, rule.get("operator", "required"))

        if effective_op == "optional":
            if exists:
                return _fb(rule, "passed", structure[section_name], label, section_name, "", f"Необязательный раздел найден на стр. {structure[section_name]}.", "", True)
            return _fb(rule, "not_applicable", None, label, section_name, "", "Раздел необязателен и не обнаружен.", "", False)

        if exists:
            return _fb(rule, "passed", structure[section_name], label, section_name, "", f"Раздел найден на стр. {structure[section_name]}.", "", True)
        return _fb(rule, "failed", None, label, section_name, f"Не найден обязательный раздел «{label}».", f"Заголовок «{label}» не обнаружен.", f"Добавить раздел «{label}».", False)


class CountChecker:
    def _select_expected(self, rule: dict, texts: dict) -> tuple[int | None, str | None]:
        expected = rule.get("expected")
        options = rule.get("options") or {}
        conditional_thresholds = options.get("conditional_thresholds") or []

        if not conditional_thresholds:
            return expected, None

        full_text = _norm(texts.get("full", ""))
        priority_text = _norm("\n".join([
            texts.get("content", ""),
            texts.get("introduction", ""),
            full_text[:2000],
        ]))

        matched: list[tuple[int, str]] = []
        all_values: list[int] = []

        for condition in conditional_thresholds:
            min_count = condition.get("min_count")
            context = str(condition.get("context") or "").strip()
            markers = [_norm(x) for x in (condition.get("when_any") or []) if x]

            if isinstance(min_count, int):
                all_values.append(min_count)

            if markers and any(marker in priority_text or marker in full_text for marker in markers):
                if isinstance(min_count, int):
                    matched.append((min_count, context))

        if matched:
            selected = max(matched, key=lambda item: item[0])
            return selected[0], selected[1]

        if all_values:
            return min(all_values), "fallback:min_condition"

        return expected, None

    def check(self, rule: dict, references: dict, structure: dict, texts: dict) -> dict:
        target = rule.get("target")
        expected, expected_context = self._select_expected(rule, texts)
        operator = rule.get("operator")
        effective_rule = {**rule, "expected": expected}

        if target == "reference:count":
            actual = references.get("count", 0)
            page = structure.get("references")
            if expected is None:
                return _fb(effective_rule, "manual_check", page, "Список источников", "references", "", "Нет данных о требуемом количестве источников.", "", actual)
            if operator == "ge":
                if actual >= expected:
                    evidence = f"Источников: {actual} (>= {expected})."
                    if expected_context:
                        evidence += f" Порог выбран по контексту: {_repair_text(expected_context)}."
                    return _fb(effective_rule, "passed", page, "Список источников", "references", "", evidence, "", actual)
                evidence = f"Ожидалось >= {expected}. Найдено: {actual}."
                if expected_context:
                    evidence += f" Порог выбран по контексту: {_repair_text(expected_context)}."
                return _fb(effective_rule, "failed", page, "Список источников", "references", "Источников меньше минимума.", evidence, "Увеличить число источников.", actual)

        return _fb(effective_rule, "manual_check", None, "Документ", "document", "", "Нет обработчика для count_rule.", "", None)


class ReferenceChecker:
    def check(self, rule: dict, references: dict, structure: dict) -> dict:
        target = rule.get("target")
        expected = rule.get("expected")
        refs = references.get("entries", [])
        page = structure.get("references")

        if target == "reference:web_access_date":
            if not refs:
                return _fb(rule, "not_applicable", page, "Список источников", "references", "", "Список источников отсутствует.", "", None)
            checked = invalid = 0
            for entry in refs:
                n = _norm(entry)
                if "http://" in n or "https://" in n or "url:" in n:
                    checked += 1
                    if _norm(str(expected)) not in n:
                        invalid += 1
            if checked == 0:
                return _fb(rule, "not_applicable", page, "Список источников", "references", "", "Электронных ресурсов не обнаружено.", "", 0)
            if invalid:
                return _fb(rule, "failed", page, "Список источников", "references", "Электронные ресурсы оформлены неполно.", f"Из {checked} ресурсов, {invalid} без поля «{expected}».", f"Добавить «{expected}» для электронных ресурсов.", {"checked": checked, "invalid": invalid})
            return _fb(rule, "passed", page, "Список источников", "references", "", f"Электронных ресурсов: {checked}. Поле «{expected}» присутствует.", "", {"checked": checked, "invalid": 0})

        return _fb(rule, "manual_check", page, "Документ", "document", "", "Нет обработчика для reference_rule.", "", None)


class ContentChecker:
    TARGET_MAP = {
        "content:toc": ("content", "Содержание"),
        "content:introduction": ("introduction", "Введение"),
        "content:conclusion": ("conclusion", "Заключение"),
    }

    def check(self, rule: dict, texts: dict, structure: dict) -> dict:
        target = rule.get("target")
        if target not in self.TARGET_MAP:
            return _fb(rule, "manual_check", None, "Документ", "document", "", "Нет обработчика для content_rule.", "", None)

        key, location = self.TARGET_MAP[target]
        raw_text = texts.get(key, "")
        page = structure.get(key)

        if not raw_text:
            return _fb(rule, "not_applicable", page, location, key, "", f"Раздел «{location}» не найден.", "", None)

        norm_text = _norm(raw_text)
        hard = [_norm(x) for x in (rule.get("expected") or [])]
        soft = [_norm(x) for x in ((rule.get("options") or {}).get("soft_items", []))]

        missing_hard = [x for x in hard if x not in norm_text]
        missing_soft = [x for x in soft if x not in norm_text]

        if missing_hard:
            return _fb(rule, "failed", page, location, key, f"В «{location}» отсутствуют обязательные элементы.", f"Не найдены: {', '.join(missing_hard)}.", f"Дополнить «{location}».", {"missing_hard": missing_hard, "missing_soft": missing_soft})
        if missing_soft:
            return _fb(rule, "warning", page, location, key, f"В «{location}» отсутствуют желательные элементы.", f"Не найдены: {', '.join(missing_soft)}.", f"Проверить полноту «{location}».", {"missing_hard": [], "missing_soft": missing_soft})
        return _fb(rule, "passed", page, location, key, "", f"«{location}» содержит ожидаемые элементы.", "", {"missing_hard": [], "missing_soft": []})


class ObjectChecker:
    def check(self, rule: dict, metrics: dict) -> dict:
        target = rule.get("target")

        if target == "page:numbering":
            candidates = metrics.get("page_number_candidates", [])
            for item in candidates:
                if item.get("page") == 1 and item.get("text") == "1":
                    return _fb(rule, "failed", 1, "Титульный лист", "title_page", "На титульном листе обнаружен номер страницы.", "Номер «1» найден на первой странице.", "Убрать номер с титульного листа.", True)
            return _fb(rule, "passed", 1, "Титульный лист", "title_page", "", "Номер на титульном листе не обнаружен.", "", False)

        manual_targets = ("figure:reference", "table:reference", "table:continuation", "formula:numbering")
        if target in manual_targets:
            return _fb(rule, "manual_check", None, "Документ", target.split(":")[0] + "s", "", f"Требуется ручная проверка: {target}.", "", None)

        return _fb(rule, "manual_check", None, "Документ", "document", "", "Нет обработчика для object_rule.", "", None)


class DocumentExtractor:
    SECTION_CANDIDATES = {
        "content": [
            "содержание", "оглавление",
        ],
        "definitions": [
            "определения",
            "термины и определения",
            "термины, определения и сокращения",
        ],
        "abbreviations": [
            "обозначения и сокращения",
            "список сокращений",
            "перечень сокращений",
            "условные обозначения",
            "список условных обозначений",
        ],
        "introduction": ["введение"],
        "conclusion": [
            "заключение",
            "выводы",
            "выводы и заключение",
        ],
        "references": [
            "список использованных источников",
            "список используемых источников",
            "список литературы",
            "библиографический список",
            "список источников",
            "список использованной литературы",
            "литература",
            "библиография",
            "использованные источники",
            "использованная литература",
            "источники и литература",
            "список источников и литературы",
        ],
        "appendix": ["приложение", "приложения"],
    }

    def extract(self, file_path: str) -> tuple[list[dict], dict, dict, dict, dict]:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            pages, metrics = self._extract_pdf(file_path)
        elif suffix == ".docx":
            pages, metrics = self._extract_docx(file_path)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            pages = [{"page": 1, "text": text, "normalized": _norm(text)}]
            metrics = self._empty_metrics("text_only", "low")

        structure = self._detect_structure(pages)
        texts = self._collect_texts(pages, structure)
        references = self._extract_references_v2(texts.get("references", ""))
        return pages, metrics, structure, texts, references

    def _try_extract_docx_via_pdf(self, file_path: str) -> tuple[list[dict], dict] | None:
        soffice = shutil.which("soffice")
        if not soffice:
            return None

        try:
            with tempfile.TemporaryDirectory(prefix="gost_docx_pdf_") as temp_dir:
                result = subprocess.run(
                    [soffice, "--headless", "--convert-to", "pdf", "--outdir", temp_dir, file_path],
                    capture_output=True,
                    text=True,
                    timeout=90,
                    check=False,
                )
                if result.returncode != 0:
                    return None

                pdf_path = Path(temp_dir) / f"{Path(file_path).stem}.pdf"
                if not pdf_path.exists():
                    pdf_candidates = sorted(Path(temp_dir).glob("*.pdf"))
                    if not pdf_candidates:
                        return None
                    pdf_path = pdf_candidates[0]

                pages, metrics = self._extract_pdf(str(pdf_path))
                metrics["source"] = "docx_via_pdf"
                metrics["confidence"] = "high"
                return pages, metrics
        except Exception:
            return None

    def _extract_docx_text_fallback(self, file_path: str) -> str:
        try:
            with zipfile.ZipFile(file_path) as archive:
                xml_bytes = archive.read("word/document.xml")
        except Exception:
            return ""

        try:
            root = ET.fromstring(xml_bytes)
        except Exception:
            return ""

        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs: list[str] = []
        for paragraph in root.findall(".//w:p", ns):
            chunks = []
            for node in paragraph.findall(".//w:t", ns):
                if node.text:
                    chunks.append(node.text)
            line = "".join(chunks).strip()
            if line:
                paragraphs.append(line)
        return "\n".join(paragraphs)

    def _empty_metrics(self, source, confidence):
        return {
            "font_family": None, "font_size_pt": None, "line_spacing": None,
            "paragraph_first_line_indent_mm": None,
            "margins_mm": {"left": None, "right": None, "top": None, "bottom": None},
            "font_size_profile": [], "font_family_profile": [],
            "page_number_candidates": [], "source": source, "confidence": confidence,
        }

    def _median(self, values: list[float]) -> float | None:
        clean = sorted(float(v) for v in values if v is not None)
        if not clean:
            return None
        mid = len(clean) // 2
        return round(clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2, 2)

    def _classify_docx_paragraph_role(self, text: str, fonts: list[str]) -> str | None:
        norm_text = _norm(text)
        if not norm_text:
            return None

        fonts_norm = {_norm(font) for font in fonts if font}
        if "cambria math" in fonts_norm:
            return "math"

        math_markers = [
            "∑", "√", "≤", "≥", "≈", "∞", "∫", "⊂", "⊆", "γ", "λ", "π", "σ",
            "formula", "theorem",
        ]
        if any(marker in text for marker in math_markers):
            return "math"

        code_fonts = {"courier new"}
        looks_code_font = bool(fonts_norm & code_fonts)
        looks_code_text = (
            ("{" in text and "}" in text)
            or ("#include" in norm_text)
            or ("int main" in norm_text)
            or ("def " in norm_text)
            or ("class " in norm_text)
            or ("import " in norm_text)
            or ("for (" in text)
            or ("while (" in text)
            or ("printf" in norm_text)
            or ("return " in norm_text)
            or ("->" in text)
            or ("==" in text)
            or ("::" in text)
            or ("graph6" in norm_text and len(text) < 120)
        )
        if looks_code_font or looks_code_text:
            return "code"

        return None

    def _classify_pdf_page_role(self, text: str, fonts: list[str]) -> str | None:
        norm_text = _norm(text)
        if not norm_text:
            return None

        fonts_norm = {_norm(font) for font in fonts if font}
        if "cambria math" in fonts_norm:
            return "math"

        math_markers = ["∑", "√", "≤", "≥", "≈", "∞", "∫", "⊂", "⊆", "γ", "λ", "π", "σ"]
        if any(marker in text for marker in math_markers):
            return "math"

        code_fonts = {"courier new", "courier", "couriernew"}
        looks_code_font = bool(fonts_norm & code_fonts)
        code_hits = sum(
            1
            for marker in ["#include", "int main", "def ", "class ", "import ", "return ", "printf", "while (", "for ("]
            if marker in norm_text
        )
        symbol_hits = sum(text.count(marker) for marker in ["{", "}", "::", "->", "=="])
        if looks_code_font or code_hits >= 2 or symbol_hits >= 6:
            return "code"

        return None

    def _extract_pdf(self, file_path: str) -> tuple[list[dict], dict]:
        pages = []
        font_sizes, line_ratios = [], []
        margins_l, margins_r, margins_t, margins_b = [], [], [], []
        first_line_indents = []
        pn_candidates = []
        fonts = []
        font_size_profile = []
        font_family_profile = []

        with pdfplumber.open(file_path) as pdf:
            for idx, page in enumerate(pdf.pages, 1):
                text = (page.extract_text() or "").strip()
                words = page.extract_words(extra_attrs=["size", "fontname"])
                chars = page.chars or []
                pw, ph = float(page.width), float(page.height)

                if words:
                    sizes = [float(w["size"]) for w in words if w.get("size")]
                    font_sizes.extend(sizes)
                    page_fonts = []
                    for w in words:
                        page_font = _canonical_font_name(w.get("fontname"))
                        if page_font:
                            page_fonts.append(page_font)
                    page_role = self._classify_pdf_page_role(text, page_fonts)
                    if sizes:
                        size_counts = Counter(round(v, 1) for v in sizes)
                        dominant_size = size_counts.most_common(1)[0][0]
                        font_size_profile.append({"page": idx, "dominant": dominant_size, "total": len(sizes), "role": page_role})

                    if page_fonts:
                        family_counts = Counter(page_fonts)
                        dominant_family = family_counts.most_common(1)[0][0]
                        font_family_profile.append({"page": idx, "dominant": dominant_family, "total": len(page_fonts), "role": page_role})

                    tops = sorted({round(float(w["top"]), 1) for w in words if "top" in w})
                    if len(tops) > 1 and sizes:
                        deltas = [b - a for a, b in zip(tops, tops[1:]) if b - a > 0.5]
                        if deltas:
                            ms = self._median(sizes)
                            mg = self._median(deltas)
                            if ms and mg:
                                line_ratios.append(mg / ms)

                    line_map: dict[float, list[dict]] = {}
                    for w in words:
                        line_map.setdefault(round(float(w["top"]), 1), []).append(w)

                    main_lefts = []
                    for top in sorted(line_map):
                        items = sorted(line_map[top], key=lambda x: float(x["x0"]))
                        xs = [float(x["x0"]) for x in items if "x0" in x]
                        if xs:
                            main_lefts.append(xs[0])
                        line_text = " ".join(str(x.get("text", "")).strip() for x in items).strip()
                        if re.fullmatch(r"\d+", line_text):
                            ax = sum(float(x["x0"]) for x in items) / len(items)
                            ax1 = sum(float(x["x1"]) for x in items) / len(items)
                            at = sum(float(x["top"]) for x in items) / len(items)
                            pn_candidates.append({"page": idx, "text": line_text, "x0": ax, "x1": ax1, "top": at, "page_width": pw, "page_height": ph})

                    if main_lefts:
                        bl = self._median(main_lefts)
                        for left in main_lefts:
                            if bl is not None:
                                d = (left - bl) * 25.4 / 72.0
                                if 2 <= d <= 30:
                                    first_line_indents.append(d)

                    x0s = [float(w["x0"]) for w in words if "x0" in w]
                    x1s = [float(w["x1"]) for w in words if "x1" in w]
                    ts = [float(w["top"]) for w in words if "top" in w]
                    bs = [float(w["bottom"]) for w in words if "bottom" in w]
                    if x0s: margins_l.append(min(x0s) * 25.4 / 72.0)
                    if x1s: margins_r.append((pw - max(x1s)) * 25.4 / 72.0)
                    if ts: margins_t.append(min(ts) * 25.4 / 72.0)
                    if bs: margins_b.append((ph - max(bs)) * 25.4 / 72.0)

                pages.append({"page": idx, "text": text, "normalized": _norm(text), "chars": chars})
                if idx <= 5:
                    for ch in chars:
                        name = str(ch.get("fontname", "")).lower()
                        if name:
                            fonts.append(name)

        font_family = None
        if fonts:
            top = Counter(fonts).most_common(1)[0][0]
            for key, val in [("times", "Times New Roman"), ("arial", "Arial"), ("calibri", "Calibri")]:
                if key in top:
                    font_family = val
                    break
            if not font_family:
                font_family = top

        return pages, {
            "font_family": font_family,
            "font_size_pt": self._median(font_sizes),
            "line_spacing": self._median(line_ratios),
            "paragraph_first_line_indent_mm": self._median(first_line_indents),
            "margins_mm": {
                "left": self._median(margins_l), "right": self._median(margins_r),
                "top": self._median(margins_t), "bottom": self._median(margins_b),
            },
            "font_size_profile": font_size_profile,
            "font_family_profile": font_family_profile,
            "page_number_candidates": pn_candidates,
            "source": "pdf_layout_heuristics", "confidence": "medium",
        }

    def _extract_docx(self, file_path: str) -> tuple[list[dict], dict]:
        from docx import Document

        converted = self._try_extract_docx_via_pdf(file_path)
        if converted is not None:
            return converted

        fallback_text = self._extract_docx_text_fallback(file_path)

        try:
            doc = Document(file_path)
        except Exception:
            text = fallback_text
            return (
                [{"page": 1, "text": text, "normalized": _norm(text)}],
                self._empty_metrics("docx_text_fallback", "low"),
            )

        paragraphs = [p for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(p.text.strip() for p in paragraphs)
        if not text and fallback_text:
            text = fallback_text

        font_names, font_sizes, line_spacings, indents = [], [], [], []
        margins_l, margins_r, margins_t, margins_b = [], [], [], []
        font_size_profile = []
        font_family_profile = []

        for idx, p in enumerate(paragraphs, 1):
            pf = p.paragraph_format
            try:
                line_spacing = pf.line_spacing
            except Exception:
                line_spacing = None
            if line_spacing is not None:
                try:
                    line_spacings.append(float(line_spacing))
                except Exception:
                    pass

            try:
                first_line_indent = pf.first_line_indent
            except Exception:
                first_line_indent = None
            if first_line_indent is not None:
                try:
                    mm = float(first_line_indent.mm)
                    if 2 <= mm <= 30:
                        indents.append(mm)
                except Exception:
                    try:
                        mm = float(first_line_indent.pt) * 25.4 / 72.0
                        if 2 <= mm <= 30:
                            indents.append(mm)
                    except Exception:
                        pass
            paragraph_fonts: list[str] = []
            paragraph_sizes: list[float] = []
            for run in p.runs:
                try:
                    font_name = run.font.name
                except Exception:
                    font_name = None
                if font_name:
                    canonical_name = _canonical_font_name(font_name)
                    if canonical_name:
                        font_names.append(canonical_name)
                        paragraph_fonts.append(canonical_name)

                try:
                    font_size = run.font.size
                except Exception:
                    font_size = None
                if font_size is not None:
                    try:
                        size_pt = float(font_size.pt)
                        font_sizes.append(size_pt)
                        paragraph_sizes.append(size_pt)
                    except Exception:
                        pass

            sample = _repair_text(p.text.strip())
            role = self._classify_docx_paragraph_role(sample, paragraph_fonts)
            if paragraph_sizes:
                size_counts = Counter(round(v, 1) for v in paragraph_sizes)
                dominant_size = size_counts.most_common(1)[0][0]
                font_size_profile.append({"paragraph": idx, "dominant": dominant_size, "sample": sample, "role": role})
            if paragraph_fonts:
                family_counts = Counter(paragraph_fonts)
                dominant_family = family_counts.most_common(1)[0][0]
                font_family_profile.append({"paragraph": idx, "dominant": dominant_family, "sample": sample, "role": role})

        for sec in doc.sections:
            for attr, lst in [("left_margin", margins_l), ("right_margin", margins_r), ("top_margin", margins_t), ("bottom_margin", margins_b)]:
                try:
                    value = getattr(sec, attr)
                    if value is not None:
                        lst.append(float(value.mm))
                except Exception:
                    pass

        font_family = Counter(font_names).most_common(1)[0][0] if font_names else None
        return (
            [{"page": 1, "text": text, "normalized": _norm(text)}],
            {
                "font_family": font_family,
                "font_size_pt": self._median(font_sizes),
                "line_spacing": self._median(line_spacings),
                "paragraph_first_line_indent_mm": self._median(indents),
                "margins_mm": {
                    "left": self._median(margins_l), "right": self._median(margins_r),
                    "top": self._median(margins_t), "bottom": self._median(margins_b),
                },
                "font_size_profile": font_size_profile,
                "font_family_profile": font_family_profile,
                "page_number_candidates": [], "source": "docx_styles", "confidence": "high",
            },
        )


    def _is_section_heading(self, line: str, candidate: str) -> bool:
        l = _norm(line)
        c = _norm(candidate)
        if not l or not c:
            return False
        if re.search(r"\.{2,}\s*\d+\s*$", l):
            return False
        l_stripped = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", l).strip()
        if l == c or l_stripped == c:
            return True
        if l.startswith(c) or l_stripped.startswith(c):
            rest = l_stripped[len(c):]
            if re.fullmatch(r"\s*\d+\s*", rest):
                return False
            if not rest or not rest[0].isalpha():
                return True
        return False

    def _reference_page_score(self, text: str) -> int:
        if not text or not text.strip():
            return 0

        score = 0
        numbered = len(re.findall(r"(?m)^\s*(?:\d+[\.\)]|\[\d+\])\s+", text))
        urls = len(re.findall(r"https?://|url\s*:", text, flags=re.IGNORECASE))
        access_dates = len(re.findall(r"дата\s+обращения|:\s*\d{2}\.\d{2}\.\d{4}", _norm(text)))
        years = len(re.findall(r"(19|20)\d{2}", text))

        score += min(numbered, 6) * 3
        score += min(urls, 3) * 2
        score += min(access_dates, 3) * 2
        if years >= 3:
            score += 2

        return score

    def _reference_page_score_v2(self, text: str) -> int:
        score = self._reference_page_score(text)
        norm_text = _norm(text)
        if any(marker in norm_text for marker in ("литератур", "библиограф", "источник")):
            score += 3
        return score

    def _clean_reference_line(self, line: str) -> str:
        line = line.replace("\x0c", " ").strip()
        line = re.sub(r"\s+", " ", line)
        line = re.sub(r"^[•·§\-–—]\s*", "", line)
        return line.strip()

    def _looks_like_reference_entry(self, text: str) -> bool:
        n = _norm(text)
        if len(n) < 20:
            return False

        score = 0
        if re.search(r"(19|20)\d{2}", text):
            score += 2
        if re.search(r"https?://|url\s*:", text, flags=re.IGNORECASE):
            score += 3
        if "isbn" in n or "doi" in n:
            score += 2
        if "[" in text and "]" in text:
            score += 1
        if "изд" in n or "м." in n or "спб" in n or "москва" in n:
            score += 1
        if "," in text and "." in text:
            left_part, right_part = text.split(",", 1)
            left_part = left_part.strip()
            right_part = right_part.strip()
            if left_part and left_part[0].isalpha() and any(ch == "." for ch in right_part[:8]):
                score += 1
        if text.count(".") >= 2:
            score += 1

        return score >= 3

    def _looks_like_reference_continuation(self, text: str) -> bool:
        n = _norm(text)
        if not n or len(n) < 8:
            return False
        if re.search(r"https?://|url\s*:", text, flags=re.IGNORECASE):
            return True
        if any(marker in n for marker in ("дата обращения", "загл. с экрана", "электронный ресурс")):
            return True
        if text.startswith("—") or text.startswith("-"):
            return True
        if text[:1].islower():
            return True
        return False

    def _finalize_reference_entries(self, entries: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for entry in entries:
            cleaned = re.sub(r"\s+", " ", entry).strip(" .;\n\t")
            if not cleaned:
                continue
            norm_cleaned = _norm(cleaned)
            if re.match(r"^(список|литература|библиография)\b", norm_cleaned):
                continue
            if len(norm_cleaned) < 10:
                continue
            if norm_cleaned in seen:
                continue
            seen.add(norm_cleaned)
            result.append(cleaned)

        return result

    def _detect_references_by_content(self, pages: list[dict], structure: dict) -> int | None:
        if not pages:
            return None

        appendix_page = structure.get("appendix")
        conclusion_page = structure.get("conclusion")
        candidates: list[tuple[int, int, int]] = []

        for page in pages:
            page_no = page["page"]
            if appendix_page and page_no >= appendix_page:
                continue
            if page_no <= max(2, len(pages) // 3):
                continue

            score = self._reference_page_score_v2(page["text"])
            if score >= 6:
                priority = score
                if conclusion_page and page_no > conclusion_page:
                    priority += 5
                if conclusion_page and page_no == conclusion_page:
                    priority += 2
                if page_no >= int(len(pages) * 0.65):
                    priority += 2
                candidates.append((page_no, score, priority))

        if not candidates:
            return None

        best_page, _, _ = max(candidates, key=lambda item: (item[2], item[0]))
        return best_page

    def _find_section_heading_indices(self, lines: list[str]) -> dict[str, int]:
        found: dict[str, int] = {}
        for idx, line in enumerate(lines):
            norm_line = _norm(line)
            if (
                "references" not in found
                and "список" in norm_line
                and any(marker in norm_line for marker in ("источник", "литератур", "библиограф"))
                and not re.search(r"\d+\s*$", norm_line)
            ):
                found["references"] = idx
            for key, variants in self.SECTION_CANDIDATES.items():
                if key in found:
                    continue
                if any(self._is_section_heading(line, v) for v in variants):
                    found[key] = idx
        return found

    def _detect_reference_start_index(self, lines: list[str]) -> int | None:
        if not lines:
            return None

        heading_indices = self._find_section_heading_indices(lines)
        if "references" in heading_indices:
            return heading_indices["references"]

        candidates: list[tuple[int, int, int]] = []
        total = len(lines)

        for idx, line in enumerate(lines):
            clean = self._clean_reference_line(line)
            if not clean:
                continue

            window = lines[idx:min(total, idx + 12)]
            block = "\n".join(window)
            score = self._reference_page_score_v2(block)
            is_numbered = bool(re.match(r"^\d+[\.\)]\s+", clean)) or bool(re.match(r"^\[\d+\]\s+", clean))
            looks_like_entry = self._looks_like_reference_entry(clean)

            if is_numbered:
                score += 3
            elif looks_like_entry:
                score += 2
            else:
                continue

            if score < 5:
                continue

            priority = score
            if idx >= int(total * 0.6):
                priority += 3
            if idx >= int(total * 0.75):
                priority += 2
            candidates.append((idx, score, priority))

        if not candidates:
            return None

        best_idx, _, _ = max(candidates, key=lambda item: (item[2], item[0]))
        return best_idx

    def _detect_structure(self, pages: list[dict]) -> dict:
        structure: dict = {}
        if pages:
            structure["title_page"] = 1

        for page in pages:
            raw_lines = [x.strip() for x in page["text"].splitlines() if x.strip()]
            for key, variants in self.SECTION_CANDIDATES.items():
                if key in structure:
                    continue
                for line in raw_lines:
                    if any(self._is_section_heading(line, v) for v in variants):
                        structure[key] = page["page"]
                        break

        if len(pages) == 1 and "references" not in structure:
            raw_lines = [x.strip() for x in pages[0]["text"].splitlines() if x.strip()]
            if self._detect_reference_start_index(raw_lines) is not None:
                structure["references"] = 1

        if "references" not in structure:
            fallback_references_page = self._detect_references_by_content(pages, structure)
            if fallback_references_page is not None:
                structure["references"] = fallback_references_page

        return structure

    def _collect_texts(self, pages: list[dict], structure: dict) -> dict:
        result = {}

        if len(pages) == 1:
            raw_lines = [x.strip() for x in pages[0]["text"].splitlines() if x.strip()]
            heading_indices = self._find_section_heading_indices(raw_lines)

            reference_start = self._detect_reference_start_index(raw_lines)
            if reference_start is not None:
                heading_indices["references"] = reference_start

            for key in ("content", "introduction", "conclusion", "references"):
                start = heading_indices.get(key)
                if start is None:
                    result[key] = ""
                    continue

                later = [idx for name, idx in heading_indices.items() if idx > start and name != key]
                end = min(later) if later else len(raw_lines)
                result[key] = "\n".join(raw_lines[start:end]).strip()

            result["full"] = pages[0]["text"]
            return result

        all_pages = pages[-1]["page"] if pages else 1

        for key in ("content", "introduction", "conclusion", "references"):
            if key not in structure:
                result[key] = ""
                continue
            start = structure[key]
            later = [p for k, p in structure.items() if isinstance(p, int) and p > start]

            if later:
                end = min(later) - 1
            else:
                end = all_pages
            result[key] = "\n".join(p["text"] for p in pages if start <= p["page"] <= end).strip()

        result["full"] = "\n".join(p["text"] for p in pages)
        return result

    def _extract_references(self, text: str) -> dict:
        if not text or not text.strip():
            return {"count": 0, "entries": []}

        text = text.replace("\r", "\n")
        text = text.replace("\x0c", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        lines_v2 = [self._clean_reference_line(ln) for ln in text.splitlines() if self._clean_reference_line(ln)]
        merged_v2: list[str] = []
        current_v2: list[str] = []

        for line in lines_v2:
            is_new = bool(re.match(r"^\d+[\.\)]\s+", line)) or bool(re.match(r"^\[\d+\]\s+", line))
            if is_new:
                if current_v2:
                    merged_v2.append(re.sub(r"\s+", " ", " ".join(current_v2)).strip())
                    current_v2 = []
                clean = re.sub(r"^\d+[\.\)]\s+|^\[\d+\]\s+", "", line).strip()
                if clean:
                    current_v2.append(clean)
            elif current_v2:
                current_v2.append(line)
            elif self._looks_like_reference_entry(line):
                current_v2 = [line]

        if current_v2:
            merged_v2.append(re.sub(r"\s+", " ", " ".join(current_v2)).strip())

        merged_v2 = self._finalize_reference_entries(merged_v2)
        if merged_v2:
            return {"count": len(merged_v2), "entries": merged_v2}

        pattern_dot = re.compile(
            r"(?:^|\n)\s*(\d+)[\.\)]\s+(.+?)(?=(?:\n\s*\d+[\.\)]\s)|\Z)",
            re.DOTALL
        )
        matches = list(pattern_dot.finditer(text))
        if matches:
            result = [re.sub(r"\s+", " ", m.group(2)).strip() for m in matches if len(m.group(2).strip()) > 10]
            result = self._finalize_reference_entries(result)
            if result:
                return {"count": len(result), "entries": result}

        pattern_bracket = re.compile(
            r"(?:^|\n)\s*\[\d+\]\s+(.+?)(?=(?:\n\s*\[\d+\]\s)|\Z)",
            re.DOTALL
        )
        matches = list(pattern_bracket.finditer(text))
        if matches:
            result = [re.sub(r"\s+", " ", m.group(1)).strip() for m in matches if len(m.group(1).strip()) > 10]
            result = self._finalize_reference_entries(result)
            if result:
                return {"count": len(result), "entries": result}

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        merged: list[str] = []
        current: list[str] = []

        for line in lines:
            is_new = bool(re.match(r"^\d+[\.\)]\s+", line)) or bool(re.match(r"^\[\d+\]\s+", line))
            if is_new:
                if current:
                    entry = re.sub(r"\s+", " ", " ".join(current)).strip()
                    if len(entry) > 10:
                        merged.append(entry)
                    current = []
                clean = re.sub(r"^\d+[\.\)]\s+|^\[\d+\]\s+", "", line).strip()
                if clean:
                    current.append(clean)
            elif current:
                current.append(line)

        if current:
            entry = re.sub(r"\s+", " ", " ".join(current)).strip()
            if len(entry) > 10:
                merged.append(entry)

        merged = self._finalize_reference_entries(merged)
        if merged:
            return {"count": len(merged), "entries": merged}

        blocks = [
            re.sub(r"\s+", " ", block).strip()
            for block in re.split(r"\n\s*\n", text)
            if block and block.strip()
        ]
        block_entries = self._finalize_reference_entries(
            [block for block in blocks if self._looks_like_reference_entry(block)]
        )
        if block_entries:
            return {"count": len(block_entries), "entries": block_entries}

        fallback = []
        for ln in text.splitlines():
            ln = ln.strip()
            if len(ln) > 30 and ("—" in ln or (":" in ln and any(c.isalpha() for c in ln))):
                if not re.match(r"^список\s", _norm(ln)):
                    fallback.append(ln)
        if fallback:
            return {"count": len(fallback), "entries": fallback}

        return {"count": 0, "entries": []}

    def _extract_references_v2(self, text: str) -> dict:
        if not text or not text.strip():
            return {"count": 0, "entries": []}

        text = text.replace("\r", "\n").replace("\x0c", "\n")
        text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        lines = [self._clean_reference_line(ln) for ln in text.splitlines() if self._clean_reference_line(ln)]

        def is_start_line(line: str) -> bool:
            return bool(re.match(r"^\d+[\.\)]\s+", line)) or bool(re.match(r"^\[\d+\]\s+", line))

        def clean_start_line(line: str) -> str:
            return re.sub(r"^\d+[\.\)]\s+|^\[\d+\]\s+", "", line).strip()

        def score_block(block_lines: list[str], entries: list[str]) -> int:
            block = "\n".join(block_lines)
            score = 0
            score += len([ln for ln in block_lines if is_start_line(ln)]) * 3
            score += len(re.findall(r"https?://|url\s*:", block, flags=re.IGNORECASE)) * 2
            score += len(re.findall(r"(19|20)\d{2}", block))
            score += len(entries) * 2
            if any(marker in _norm(block) for marker in ("литератур", "библиограф", "источник")):
                score += 3
            return score

        def parse_cluster(cluster_lines: list[str]) -> list[str]:
            entries: list[str] = []
            current: list[str] = []

            for line in cluster_lines:
                if is_start_line(line):
                    if current:
                        entries.append(re.sub(r"\s+", " ", " ".join(current)).strip())
                    current = []
                    clean = clean_start_line(line)
                    if clean:
                        current.append(clean)
                elif current:
                    current.append(line)

            if current:
                entries.append(re.sub(r"\s+", " ", " ".join(current)).strip())

            return self._finalize_reference_entries(entries)

        start_indices = [idx for idx, line in enumerate(lines) if is_start_line(line)]
        clusters: list[tuple[int, int]] = []
        if start_indices:
            cluster_start = start_indices[0]
            prev_idx = start_indices[0]
            for idx in start_indices[1:]:
                if idx - prev_idx <= 4:
                    prev_idx = idx
                    continue
                clusters.append((cluster_start, prev_idx))
                cluster_start = idx
                prev_idx = idx
            clusters.append((cluster_start, prev_idx))

        best_entries: list[str] = []
        best_score = -1

        for start_idx, end_idx in clusters:
            window_end = min(len(lines), end_idx + 8)
            cluster_lines = lines[start_idx:window_end]
            entries = parse_cluster(cluster_lines)
            score = score_block(cluster_lines, entries)
            if score > best_score:
                best_score = score
                best_entries = entries

        if best_entries:
            return {"count": len(best_entries), "entries": best_entries}

        pattern_dot = re.compile(
            r"(?:^|\n)\s*(\d+)[\.\)]\s+(.+?)(?=(?:\n\s*\d+[\.\)]\s)|(?:\n\s*\[\d+\]\s)|\Z)",
            re.DOTALL
        )
        matches = list(pattern_dot.finditer(text))
        if matches:
            result = [re.sub(r"\s+", " ", m.group(2)).strip() for m in matches if len(m.group(2).strip()) > 10]
            result = self._finalize_reference_entries(result)
            if result:
                return {"count": len(result), "entries": result}

        merged_unordered: list[str] = []
        current_unordered: list[str] = []

        for line in lines:
            if self._looks_like_reference_entry(line):
                if current_unordered:
                    merged_unordered.append(re.sub(r"\s+", " ", " ".join(current_unordered)).strip())
                current_unordered = [line]
                continue

            if current_unordered and self._looks_like_reference_continuation(line):
                current_unordered.append(line)
                continue

            if current_unordered:
                merged_unordered.append(re.sub(r"\s+", " ", " ".join(current_unordered)).strip())
                current_unordered = []

        if current_unordered:
            merged_unordered.append(re.sub(r"\s+", " ", " ".join(current_unordered)).strip())

        merged_unordered = self._finalize_reference_entries(merged_unordered)
        if merged_unordered:
            return {"count": len(merged_unordered), "entries": merged_unordered}

        blocks = [
            re.sub(r"\s+", " ", block).strip()
            for block in re.split(r"\n\s*\n", text)
            if block and block.strip()
        ]
        block_entries = self._finalize_reference_entries(
            [block for block in blocks if self._looks_like_reference_entry(block)]
        )
        if block_entries:
            return {"count": len(block_entries), "entries": block_entries}

        fallback = self._finalize_reference_entries(
            [ln for ln in lines if self._looks_like_reference_entry(ln)]
        )
        if fallback:
            return {"count": len(fallback), "entries": fallback}

        return {"count": 0, "entries": []}



class RuleEngine:
    def __init__(self, ruleset_code: str):
        self.ruleset_code = ruleset_code
        self.rules = load_rules(ruleset_code)
        self._metric = MetricChecker()
        self._section = SectionChecker()
        self._count = CountChecker()
        self._ref = ReferenceChecker()
        self._content = ContentChecker()
        self._object = ObjectChecker()
        self._extractor = DocumentExtractor()
        self._effective_operators = resolve_section_operators(self.rules)

    def _dispatch(self, rule: dict, ctx: dict) -> dict:
        ct = rule.get("check_type")
        if ct == "metric_rule":
            return self._metric.check(rule, ctx["metrics"])
        if ct == "section_rule":
            return self._section.check(rule, ctx["structure"], self._effective_operators)
        if ct == "count_rule":
            return self._count.check(rule, ctx["references"], ctx["structure"], ctx["texts"])
        if ct == "reference_rule":
            return self._ref.check(rule, ctx["references"], ctx["structure"])
        if ct == "content_rule":
            return self._content.check(rule, ctx["texts"], ctx["structure"])
        if ct == "object_rule":
            return self._object.check(rule, ctx["metrics"])
        return _fb(rule, "manual_check", None, "Документ", "document", "", "Требуется ручная проверка.", "", None)

    def _deduplicate(self, findings: list[dict]) -> list[dict]:
        seen: set = set()
        unique: list[dict] = []
        for f in findings:
            key = (
                f.get("section"),
                f.get("status"),
                f.get("problem"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)
        return unique

    def _score(self, findings: list[dict]) -> tuple[float, str]:
        weights = {"passed": 1.0, "warning": 0.65, "failed": 0.2}
        scored = [weights[f["status"]] for f in findings if f["status"] in weights]
        if not scored:
            return 0.0, "данных недостаточно"
        v = round(sum(scored) / len(scored), 4)
        if v >= 0.85:
            return v, "высокое соответствие"
        if v >= 0.65:
            return v, "среднее соответствие"
        return v, "низкое соответствие"

    def _recommendation(self, findings: list[dict]) -> str:
        failed = [f for f in findings if f["status"] == "failed" and f.get("fix")]
        warning = [f for f in findings if f["status"] == "warning" and f.get("fix")]
        if failed:
            seen_fix: set[str] = set()
            fixes = []
            for f in failed[:5]:
                if f["fix"] not in seen_fix:
                    seen_fix.add(f["fix"])
                    fixes.append(f["fix"])
            return " ".join(fixes[:3])
        if warning:
            return " ".join(f["fix"] for f in warning[:3])
        return "Явных нарушений по автоматически проверяемым правилам не обнаружено."

    def _compact_metrics_for_output(self, metrics: dict) -> dict:
        compact = dict(metrics)
        source = str(metrics.get("source") or "")

        if source.startswith("docx"):
            compact["font_size_profile"] = [
                {
                    "paragraph": item.get("paragraph"),
                    "dominant": item.get("dominant"),
                    "role": item.get("role"),
                }
                for item in (metrics.get("font_size_profile") or [])[:12]
            ]
            compact["font_family_profile"] = [
                {
                    "paragraph": item.get("paragraph"),
                    "dominant": item.get("dominant"),
                    "role": item.get("role"),
                }
                for item in (metrics.get("font_family_profile") or [])[:12]
            ]
            compact["font_size_profile_truncated"] = max(0, len(metrics.get("font_size_profile") or []) - len(compact["font_size_profile"]))
            compact["font_family_profile_truncated"] = max(0, len(metrics.get("font_family_profile") or []) - len(compact["font_family_profile"]))

        return compact

    def run(self, file_path: str) -> dict:
        pages, metrics, structure, texts, references = self._extractor.extract(file_path)
        ctx = {"metrics": metrics, "structure": structure, "texts": texts, "references": references}

        raw_findings = []
        for rule in self.rules:
            if isinstance(rule, dict):
                raw_findings.append(self._dispatch(rule, ctx))

        findings = self._deduplicate(raw_findings)
        overall_score, score_label = self._score(findings)

        status_counts = {s: sum(1 for f in findings if f["status"] == s)
                         for s in ("passed", "warning", "failed", "manual_check", "not_applicable")}

        problem_sections: dict[str, int] = {}
        for f in findings:
            if f["status"] in ("warning", "failed"):
                s = f["section"]
                problem_sections[s] = problem_sections.get(s, 0) + 1
        top_problem_sections = sorted(problem_sections, key=problem_sections.get, reverse=True)[:3]

        visible = [f for f in findings if f["status"] in ("failed", "warning")]

        return {
            "ruleset_code": self.ruleset_code,
            "document_kind": "document",
            "total_pages": len(pages),
            "rules_count": len([r for r in self.rules if isinstance(r, dict)]),
            "overall_score": overall_score,
            "score_label": score_label,
            "status": "ok" if overall_score >= 0.85 else "warning" if overall_score >= 0.65 else "problem",
            "short_recommendation": self._recommendation(findings),
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
                "format_metrics": self._compact_metrics_for_output(metrics),
                "references_found": references["count"],
                "llm_enabled": False,
                "llm_model": None,
            },
            "findings": visible,
        }
