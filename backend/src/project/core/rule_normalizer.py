import re


def norm(text: str) -> str:
    text = text or ""
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    text = text.lower().replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_rule_prefix(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^\s*\d+(?:\.\d+){0,6}[\.\)]?\s*", "", text)
    return text.strip()


def to_float(value: str) -> float | None:
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def extract_numbers(text: str) -> list[float]:
    out = []
    for m in re.findall(r"(?<![A-Za-zА-Яа-я])(\d+(?:[.,]\d+)?)(?![A-Za-zА-Яа-я])", text):
        v = to_float(m)
        if v is not None:
            out.append(v)
    return out


def detect_severity(text: str) -> str:
    t = norm(text)
    if any(x in t for x in ["не допускается", "запрещается", "обязател", "должен", "должна", "должны", "необходимо"]):
        return "critical"
    if any(x in t for x in ["следует", "рекомендуется", "допускается"]):
        return "warning"
    return "warning"


def make_rule(
    item: dict,
    check_type: str,
    target: str,
    operator: str,
    expected=None,
    options: dict | None = None,
) -> dict:
    description = str(item.get("description") or item.get("text") or "").strip()
    full_title = str(item.get("title") or description).strip()

    return {
        "id": item.get("id"),
        "rule_number": item.get("rule_number"),
        "title": full_title,
        "description": description,
        "category": item.get("category"),
        "severity": item.get("severity") or detect_severity(description),
        "check_type": check_type,
        "target": target,
        "operator": operator,
        "expected": expected,
        "options": options or {},
        "source": item.get("source"),
        "rule_confidence": item.get("rule_confidence"),
        "category_confidence": item.get("category_confidence"),
        "page_start": item.get("page_start"),
        "page_end": item.get("page_end"),
    }


def is_meta_rule(text: str, rule_number: str | None) -> bool:
    t = norm(text)

    meta_markers = [
        "настоящий стандарт устанавливает",
        "область применения",
        "нормативные ссылки",
        "термины и определения",
        "цель работы",
        "темы выпускных квалификационных работ",
        "студенту может предоставляться право выбора темы",
        "назначается научный руководитель",
        "допуск к государственной итоговой аттестации",
        "примеры библиографического описания",
        "форма титульного листа",
        "форма задания",
        "форма отзыва",
        "форма рецензии",
    ]

    if any(x in t for x in meta_markers):
        return True

    if rule_number and rule_number.startswith(("1.", "2.", "3.", "4.")):
        if not any(x in t for x in [
            "шрифт",
            "интервал",
            "поля",
            "абзацный отступ",
            "номер страницы",
            "содержание",
            "введение",
            "заключение",
            "список использованных источников",
            "приложение",
        ]):
            return True

    return False


BIBLIOGRAPHY_MARKERS = [
    "область ответственности",
    "область выходных данных",
    "место издания",
    "название издательства",
    "фамилия автора приводится",
    "инициалы и фамилии авторов",
    "наименования учреждений",
    "год издания",
    "авторского права",
    "подписания в печать",
    "двоеточие", 
]


def is_bibliography_formatting_rule(text: str) -> bool:
    t = norm(text)
    return sum(1 for m in BIBLIOGRAPHY_MARKERS if m in t) >= 2


def parse_font_family(text: str) -> str | None:
    t = norm(text)
    families = {
        "times new roman": "Times New Roman",
        "arial": "Arial",
        "calibri": "Calibri",
        "courier new": "Courier New",
        "verdana": "Verdana",
        "tahoma": "Tahoma",
    }
    for key, value in families.items():
        if key in t:
            return value
    return None


def parse_font_size(text: str) -> float | None:
    t = norm(text)

    patterns = [
        r"(?:размер(?:ом)?|кегл(?:ем|ь)?)\s*(?:шрифта\s*)?(\d+(?:[.,]\d+)?)\s*(?:пт|pt)\b",
        r"(\d+(?:[.,]\d+)?)\s*(?:пт|pt)\b",
    ]

    for pattern in patterns:
        m = re.search(pattern, t, flags=re.IGNORECASE)
        if m:
            value = to_float(m.group(1))
            if value is not None and 5 <= value <= 72:
                return value

    return None


def parse_line_spacing(text: str) -> float | None:
    t = norm(text)

    if "полтора интервала" in t or "через полтора интервала" in t:
        return 1.5
    if "двойной интервал" in t or "через два интервала" in t:
        return 2.0

    m = re.search(r"(?:межстроч(?:ный)?\s+интервал|интервал)\s*(\d+(?:[.,]\d+)?)", t)
    if m:
        value = to_float(m.group(1))
        if value is not None and 1 <= value <= 4:
            return value

    return None


def parse_indent_mm(text: str) -> float | None:
    t = norm(text)

    patterns = [
        r"абзацн(?:ый|ого)?\s+отступ[а-я\s]*?(\d+(?:[.,]\d+)?)\s*мм",
        r"отступ[а-я\s]*?(\d+(?:[.,]\d+)?)\s*мм",
        r"абзацн(?:ый|ого)?\s+отступ[а-я\s]*?(\d+(?:[.,]\d+)?)\s*см",
    ]

    for pattern in patterns:
        m = re.search(pattern, t)
        if not m:
            continue
        value = to_float(m.group(1))
        if value is None:
            continue
        if "см" in m.group(0):
            value = value * 10
        if 1 <= value <= 30:
            return round(value, 2)

    return None


def parse_margins_mm(text: str) -> dict | None:
    t = norm(text)

    if "пол" not in t:
        return None

    patterns = {
        "left": r"лев(?:ое|ое поле|ое\s+поле)?\s*[—\-:–]?\s*(\d+(?:[.,]\d+)?)\s*мм",
        "right": r"прав(?:ое|ое поле|ое\s+поле)?\s*[—\-:–]?\s*(\d+(?:[.,]\d+)?)\s*мм",
        "top": r"верхн(?:ее|ее поле|ее\s+поле)?\s*[—\-:–]?\s*(\d+(?:[.,]\d+)?)\s*мм",
        "bottom": r"нижн(?:ее|ее поле|ее\s+поле)?\s*[—\-:–]?\s*(\d+(?:[.,]\d+)?)\s*мм",
    }

    result = {}
    for key, pattern in patterns.items():
        m = re.search(pattern, t)
        if m:
            value = to_float(m.group(1))
            if value is not None and 1 <= value <= 60:
                result[key] = value

    if len(result) == 4:
        return result

    return None


def parse_references_count(text: str) -> int | None:
    t = norm(text)

    if not any(x in t for x in ["источник", "литератур", "библиограф"]):
        return None
    if "не менее" not in t:
        return None

    candidates = []
    for m in re.finditer(r"не\s+менее\s+(\d+(?:[.,]\d+)?)", t):
        value = to_float(m.group(1))
        if value is not None and 1 <= value <= 1000:
            candidates.append(int(value))

    if candidates:
        return max(candidates)

    return None


def parse_reference_count_conditions(text: str) -> list[dict]:
    t = norm(text)

    if not any(x in t for x in ["источ", "литератур", "библиограф"]):
        return []
    if "не менее" not in t:
        return []

    conditions: list[dict] = []

    clauses = [
        clause.strip(" ,;:")
        for clause in re.split(r"\s*,\s+а\s+(?=при\s+выполнении|для\s+)|[.;]", t)
        if clause and clause.strip()
    ]

    for clause in clauses:
        if "не менее" not in clause:
            continue

        match = re.search(
            r"(?:при\s+выполнении|для)\s+(.+?)\s*(?:составляет,\s+как\s+правило,)?\s*(?:[-–—])?\s*не\s+менее\s+(\d+(?:[.,]\d+)?)",
            clause,
            flags=re.IGNORECASE,
        )
        if not match:
            continue

        context = match.group(1).strip(" ,;:()")
        context = re.sub(r"\s+", " ", context).strip()
        context = re.sub(r"[\(\[]+$", "", context).strip()
        context = re.sub(r"[,.!?:;]+$", "", context).strip()
        value = to_float(match.group(2))
        if not context or value is None:
            continue

        condition = {
            "context": context,
            "min_count": int(value),
            "when_any": [],
        }

        if "курсов" in context:
            condition["when_any"].extend(["курсов", "курсовой проект"])
        if "выпуск" in context or "квалификацион" in context:
            condition["when_any"].extend(["выпуск", "квалификацион", "вкр"])
        if "магист" in context:
            condition["when_any"].append("магист")
        if "диплом" in context:
            condition["when_any"].append("диплом")
        if "реферат" in context:
            condition["when_any"].append("реферат")

        conditions.append(condition)

    unique: list[dict] = []
    seen = set()
    for condition in conditions:
        key = (
            condition.get("context"),
            condition.get("min_count"),
            tuple(condition.get("when_any") or []),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(condition)

    return unique


def infer_structure_targets(text: str) -> list[tuple[str, bool]]:
    t = norm(text)


    if is_bibliography_formatting_rule(text):
        return []

    section_map = [
        ("section:title_page", ["титульный лист"]),
        ("section:content", ["содержание", "оглавление"]),
        ("section:definitions", ["определения", "термины и определения"]),
        ("section:abbreviations", ["обозначения и сокращения", "сокращения", "условные обозначения"]),
        ("section:introduction", ["введение"]),
        ("section:conclusion", ["заключение"]),
        ("section:references", [
            "список использованных источников",
            "список литературы",
            "библиографический список",
            "список источников",
        ]),
        ("section:appendix", ["приложение", "приложения"]),
    ]

    section_anchor_words = [
        "структурный элемент",
        "структурные элементы",
        "является обязательным",
        "не являются обязательными",
        "включают в работу",
        "включают следующие",
        "структурными элементами",
    ]

    weak_anchors = [
        "раздел",
        "заголовок",
        "перечень",
        "оформляется",
        "приводится в",
        "приводят в",
    ]

    is_optional = any(x in t for x in [
        "не является обязательным",
        "не являются обязательными",
        "по усмотрению исполнителя",
        "по усмотрению",
    ])

    results: list[tuple[str, bool]] = []

    for target, variants in section_map:
        if not any(v in t for v in variants):
            continue

        has_strong_anchor = any(x in t for x in section_anchor_words)
        has_weak_anchor = any(x in t for x in weak_anchors)

        if has_strong_anchor or has_weak_anchor:
            results.append((target, is_optional))

    unique: list[tuple[str, bool]] = []
    seen = set()
    for target, optional in results:
        key = (target, optional)
        if key in seen:
            continue
        seen.add(key)
        unique.append((target, optional))

    return unique


def infer_content_rule(text: str) -> tuple[str, list[str], list[str]] | None:
    t = norm(text)

    if "содержание включает" in t or ("содержание" in t and "перечень" in t and "структурных элементов" in t):
        hard = []
        soft = []

        mapping = [
            ("введение", "введение"),
            ("заключение", "заключение"),
            ("список использованных источников", "список использованных источников"),
            ("список литературы", "список литературы"),
            ("приложение", "приложение"),
        ]

        for needle, token in mapping:
            if needle in t:
                if token in {"введение", "заключение"}:
                    hard.append(token)
                else:
                    soft.append(token)

        if not hard:
            hard = ["введение", "заключение"]

        return "content:toc", hard, soft

    if "заключение" in t and "должно содержать" in t:
        hard = []
        soft = []

        if "результат" in t:
            hard.append("результат")
        if "вывод" in t:
            hard.append("вывод")
        if "рекомендац" in t:
            soft.append("рекомендац")
        if "эффективност" in t:
            soft.append("эффективност")
        if "поставленных задач" in t:
            soft.append("поставленных задач")

        if not hard:
            hard = ["результат", "вывод"]

        return "content:conclusion", hard, soft

    if "введение" in t and "должно содержать" in t:
        hard = []
        soft = []

        if "актуаль" in t:
            hard.append("актуаль")
        if "цель" in t:
            hard.append("цель")
        if "задач" in t:
            hard.append("задач")
        if "новизн" in t:
            soft.append("новизн")
        if "связь" in t:
            soft.append("связь")
        if "состояние разработок" in t or "степень разработанности" in t:
            soft.append("состояние разработок")

        if not hard:
            hard = ["актуаль", "цель", "задач"]

        return "content:introduction", hard, soft

    return None


def infer_required_section_from_content_target(target: str, text: str) -> str | None:
    t = norm(text)

    optional_markers = [
        "не является обязательным",
        "не являются обязательными",
        "по усмотрению",
        "при необходимости",
        "может содержать",
        "могут содержать",
    ]
    if any(marker in t for marker in optional_markers):
        return None

    mapping = {
        "content:toc": "section:content",
        "content:introduction": "section:introduction",
        "content:conclusion": "section:conclusion",
    }
    return mapping.get(target)


def infer_implied_required_sections(text: str) -> list[str]:
    t = norm(text)

    optional_markers = [
        "не является обязательным",
        "не являются обязательными",
        "по усмотрению",
        "при необходимости",
        "может",
        "могут",
        "допускается",
    ]
    if any(marker in t for marker in optional_markers):
        return []

    implied: list[str] = []

    references_markers = [
        "список использованных источников",
        "список источников",
        "список литературы",
        "библиографический список",
    ]
    references_predicates = [
        "должен",
        "должна",
        "должны",
        "включает",
        "включать",
        "приводят",
        "приводится",
        "оформляют",
        "помещают",
    ]
    if any(marker in t for marker in references_markers) and any(predicate in t for predicate in references_predicates):
        implied.append("section:references")

    toc_markers = ["содержание", "оглавление"]
    toc_predicates = [
        "включает",
        "включать",
        "приводят",
        "приводится",
        "указывают",
        "перечисляют",
        "состоит",
    ]
    if any(marker in t for marker in toc_markers) and any(predicate in t for predicate in toc_predicates):
        implied.append("section:content")

    unique: list[str] = []
    seen = set()
    for target_name in implied:
        if target_name in seen:
            continue
        seen.add(target_name)
        unique.append(target_name)
    return unique


def normalize_extracted_rules(items: list[dict]) -> list[dict]:
    normalized: list[dict] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        text = str(item.get("description") or item.get("text") or item.get("title") or "").strip()
        rule_number = item.get("rule_number")

        if not text:
            continue

        if is_meta_rule(text, rule_number):
            continue

        if is_bibliography_formatting_rule(text):
            normalized.append(
                make_rule(
                    item=item,
                    check_type="manual_check",
                    target="reference:formatting",
                    operator="manual",
                )
            )
            continue

        margins = parse_margins_mm(text)
        if margins:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="metric_rule",
                    target="margins_mm",
                    operator="equals",
                    expected=margins,
                )
            )
            continue

        font_family = parse_font_family(text)
        if font_family:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="metric_rule",
                    target="font_family",
                    operator="equals",
                    expected=font_family,
                )
            )

        font_size = parse_font_size(text)
        if font_size is not None:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="metric_rule",
                    target="font_size_pt",
                    operator="equals",
                    expected=font_size,
                )
            )

        line_spacing = parse_line_spacing(text)
        if line_spacing is not None:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="metric_rule",
                    target="line_spacing",
                    operator="equals",
                    expected=line_spacing,
                )
            )

        indent = parse_indent_mm(text)
        if indent is not None:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="metric_rule",
                    target="paragraph_first_line_indent_mm",
                    operator="equals",
                    expected=indent,
                )
            )

        ref_count = parse_references_count(text)
        if ref_count is not None:
            conditional_thresholds = parse_reference_count_conditions(text)
            options = {}
            if conditional_thresholds:
                options["conditional_thresholds"] = conditional_thresholds
                options["selection_strategy"] = "contextual_or_min"

            normalized.append(
                make_rule(
                    item=item,
                    check_type="count_rule",
                    target="reference:count",
                    operator="ge",
                    expected=ref_count,
                    options=options,
                )
            )

        structure_targets = infer_structure_targets(text)
        for target, is_optional in structure_targets:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="section_rule",
                    target=target,
                    operator="optional" if is_optional else "required",
                    expected=True,
                )
            )

        for target in infer_implied_required_sections(text):
            normalized.append(
                make_rule(
                    item=item,
                    check_type="section_rule",
                    target=target,
                    operator="required",
                    expected=True,
                )
            )

        content_rule = infer_content_rule(text)
        if content_rule is not None:
            target, hard, soft = content_rule
            normalized.append(
                make_rule(
                    item=item,
                    check_type="content_rule",
                    target=target,
                    operator="contains",
                    expected=hard,
                    options={"soft_items": soft},
                )
            )
            implied_section_target = infer_required_section_from_content_target(target, text)
            if implied_section_target:
                normalized.append(
                    make_rule(
                        item=item,
                        check_type="section_rule",
                        target=implied_section_target,
                        operator="required",
                        expected=True,
                    )
                )

        t = norm(text)

        if "номер страницы" in t and ("титульн" in t or "первой странице" in t):
            normalized.append(
                make_rule(
                    item=item,
                    check_type="object_rule",
                    target="page:numbering",
                    operator="rule_based",
                    expected=False,
                )
            )

        if "рисунк" in t and "ссыл" in t:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="object_rule",
                    target="figure:reference",
                    operator="manual_or_llm",
                )
            )

        if "таблиц" in t and "ссыл" in t:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="object_rule",
                    target="table:reference",
                    operator="manual_or_llm",
                )
            )

        if "продолжение таблицы" in t or ("таблиц" in t and "перенос" in t):
            normalized.append(
                make_rule(
                    item=item,
                    check_type="object_rule",
                    target="table:continuation",
                    operator="manual_or_llm",
                )
            )

        if "формул" in t and "нумерац" in t:
            normalized.append(
                make_rule(
                    item=item,
                    check_type="object_rule",
                    target="formula:numbering",
                    operator="manual_or_llm",
                )
            )

    unique = []
    seen = set()

    for rule in normalized:
        key = (
            rule.get("rule_number"),
            rule.get("check_type"),
            rule.get("target"),
            str(rule.get("expected")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(rule)

    return unique
