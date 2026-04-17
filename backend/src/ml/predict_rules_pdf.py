import os
import re
import json
import argparse
from typing import List, Dict, Tuple, Optional

import torch
import fitz
from transformers import AutoTokenizer, AutoModelForSequenceClassification


ABBREVIATION_PATTERNS = [
    r'\b[А-ЯЁA-Z]\.\s*[А-ЯЁA-Z]\.',
    r'\b[А-ЯЁA-Z]\.',
    r'\b\d+\.\d+\.\d+\b',
    r'\b\d+\.\d+\b',
    r'\b(?:т\.д\.|т\.п\.|и т\.д\.|и т\.п\.|и др\.|др\.|пр\.|см\.|рис\.|табл\.|форм\.|гл\.|разд\.|п\.|подп\.|стр\.|с\.|ч\.|вып\.|ред\.|изд\.|им\.|г\.|гг\.|ст\.)',
]

RULE_START_PATTERNS = [
    r'^\s*\d+(?:\.\d+){0,5}[\.\)]?\s+',
    r'^\s*(?:[-–—•●▪◦]|\(?\d+\)|\d+\.|[а-яёa-z]\))\s+',
]

RULE_CUE_PATTERNS = [
    r'\bдолжен\b', r'\bдолжна\b', r'\bдолжны\b',
    r'\bследует\b', r'\bнеобходимо\b',
    r'\bдопускается\b', r'\bне допускается\b',
    r'\bрекомендуется\b',
    r'\bприводят\b', r'\bуказывают\b', r'\bоформляют\b',
    r'\bпомещают\b', r'\bрасполагают\b', r'\bнумеруют\b',
    r'\bвключают\b', r'\bобозначают\b', r'\bзаписывают\b',
    r'\bпечатают\b', r'\bприменяют\b',
    r'\bначинается\b', r'\bначинаются\b',
    r'\bсодержит\b', r'\bсодержат\b',
    r'\bоформляется\b', r'\bоформляются\b',
    r'\bиспользуется\b', r'\bиспользуются\b',
    r'\bставится\b', r'\bставятся\b',
]

SHORT_CONTINUATION_PATTERNS = [
    r'^(?:нельзя|не допускается|допускается|рекомендуется|используется|используются)\b',
    r'^(?:обязательно|обязательна|обязательны)\b',
    r'^(?:при этом|в отличие|кроме того|также|затем)\b',
    r'^(?:фамилии|заголовки|выводы|номер|номера|точка|список|сноски)\b',
]

HEADING_PATTERNS = [
    r'^(?:раздел|глава|приложение)\s+[A-ZА-ЯЁ0-9IVXLC]+(?:\s+.*)?$',
    r'^\d+(?:\.\d+){0,5}$',
    r'^\d+(?:\.\d+){0,5}\s+[^\n]+$',
]


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r'(?<=\w)-\n(?=\w)', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    text = re.sub(r' +([.,;:!?])', r'\1', text)
    text = re.sub(r'([(\[«])\s+', r'\1', text)
    text = re.sub(r'\s+([)\]»])', r'\1', text)
    return text.strip()


def clean_line_artifacts(text: str) -> str:
    lines = [x.strip() for x in text.split("\n")]
    out = []

    for line in lines:
        if not line:
            continue

        if re.fullmatch(r'\d+', line):
            continue

        if re.fullmatch(
            r'(?:СТО|ГОСТ|СП|СНиП)?\s*\d+(?:\.\d+)*(?:\s*[-–]\s*\d+)?',
            line,
            flags=re.IGNORECASE,
        ):
            continue

        out.append(line)

    return normalize_text("\n".join(out))


def is_heading(text: str) -> bool:
    t = text.strip()
    if not t:
        return False

    if len(t) > 220:
        return False

    for pattern in HEADING_PATTERNS:
        if re.fullmatch(pattern, t, flags=re.IGNORECASE):
            return True

    if t.upper() == t and re.search(r'[А-ЯЁA-Z]', t):
        return True

    return False


def is_list_item(text: str) -> bool:
    return bool(
        re.match(
            r'^\s*(?:[-–—•●▪◦]|\(?\d+\)|\d+\.|[а-яёa-z]\))\s+',
            text,
            flags=re.IGNORECASE,
        )
    )


def extract_rule_number(text: str) -> Optional[str]:
    m = re.match(r'^\s*(\d+(?:\.\d+){0,5})[\.\)]?\s+', text)
    if m:
        return m.group(1)
    return None


def protect_abbreviations(text: str) -> Tuple[str, Dict[str, str]]:
    protected = text
    mapping = {}
    idx = 0

    for pattern in ABBREVIATION_PATTERNS:
        while True:
            m = re.search(pattern, protected, flags=re.IGNORECASE)
            if not m:
                break
            original = m.group(0)
            token = f"__PROT_{idx}__"
            idx += 1
            protected = protected[:m.start()] + token + protected[m.end():]
            mapping[token] = original

    return protected, mapping


def restore_abbreviations(text: str, mapping: Dict[str, str]) -> str:
    for token, value in mapping.items():
        text = text.replace(token, value)
    return text


def split_sentences_safely(text: str) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    protected, mapping = protect_abbreviations(text)
    parts = re.split(r'(?<=[.!?])\s+(?=[А-ЯЁA-Z0-9«"(])', protected)
    return [restore_abbreviations(x.strip(), mapping) for x in parts if x.strip()]


def looks_like_rule(text: str) -> bool:
    t = text.lower()

    if any(re.search(p, t, flags=re.IGNORECASE) for p in RULE_CUE_PATTERNS):
        return True

    if any(re.search(p, text, flags=re.IGNORECASE) for p in RULE_START_PATTERNS):
        return True

    return False


def is_short_continuation(text: str) -> bool:
    t = text.strip()
    if not t:
        return False

    if extract_rule_number(t):
        return False

    if len(t) <= 120:
        return True

    for pattern in SHORT_CONTINUATION_PATTERNS:
        if re.match(pattern, t, flags=re.IGNORECASE):
            return True

    return False


def should_append_to_previous(current: str, previous: str) -> bool:
    current = current.strip()
    previous = previous.strip()

    if not current or not previous:
        return False

    if extract_rule_number(current):
        return False

    if is_heading(current):
        return False

    if is_list_item(current):
        return False

    if re.search(r'[:;,]\s*$', previous):
        return True

    if len(previous) < 250 and not re.search(r'[.!?]\s*$', previous):
        return True

    if current[:1].islower():
        return True

    if is_short_continuation(current):
        return True

    if re.match(
        r'^(?:а|б|в|г|д|е|при этом|в этом случае|если|где|затем|после|причем|'
        r'которые|который|которая|которое|нельзя|рекомендуется|используется|'
        r'используются|обязательно|обязательна|обязательны)\b',
        current,
        flags=re.IGNORECASE,
    ):
        return True

    return False


def split_block_into_fragments(block: str) -> List[str]:
    block = clean_line_artifacts(block)
    if not block:
        return []

    lines = [x.strip() for x in block.split("\n") if x.strip()]
    if not lines:
        return []

    if len(lines) == 1 and is_heading(lines[0]):
        return [lines[0]]

    fragments: List[str] = []
    current = ""

    for line in lines:
        line = normalize_text(line)
        if not line:
            continue

        if is_heading(line) and not extract_rule_number(line):
            if current.strip():
                fragments.append(normalize_text(current))
                current = ""
            fragments.append(line)
            continue

        if extract_rule_number(line):
            if current.strip():
                fragments.append(normalize_text(current))
            current = line
            continue

        if is_list_item(line):
            if current.strip():
                fragments.append(normalize_text(current))
                current = ""
            fragments.append(line)
            continue

        if current:
            current = normalize_text(current + " " + line)
        else:
            current = line

    if current.strip():
        fragments.append(normalize_text(current))

    merged: List[str] = []
    for frag in fragments:
        if merged and should_append_to_previous(frag, merged[-1]):
            merged[-1] = normalize_text(merged[-1] + " " + frag)
        else:
            merged.append(frag)

    return [x for x in merged if x]


def read_pdf_pages(pdf_path: str) -> List[Dict]:
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        text = normalize_text(text)
        pages.append({"page": i + 1, "text": text})

    doc.close()
    return pages


def generate_fragments(pages: List[Dict]) -> List[Dict]:
    fragments = []
    frag_id = 1
    pending_fragment: Optional[Dict] = None

    for page in pages:
        blocks = re.split(r'\n{2,}', page["text"])

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            parts = split_block_into_fragments(block)

            for part in parts:
                if len(part) < 2:
                    continue

                part_number = extract_rule_number(part)

                item = {
                    "id": frag_id,
                    "text": part,
                    "page_start": page["page"],
                    "page_end": page["page"],
                    "rule_number": part_number,
                }

                if pending_fragment and should_append_to_previous(part, pending_fragment["text"]):
                    pending_fragment["text"] = normalize_text(pending_fragment["text"] + " " + part)
                    pending_fragment["page_end"] = page["page"]
                    if pending_fragment.get("rule_number") is None and part_number is not None:
                        pending_fragment["rule_number"] = part_number
                else:
                    if pending_fragment:
                        fragments.append(pending_fragment)
                        frag_id += 1
                    pending_fragment = item

    if pending_fragment:
        fragments.append(pending_fragment)

    for i, fragment in enumerate(fragments, 1):
        fragment["id"] = i

    return fragments


def chunk_for_model(text: str, tokenizer, max_length: int) -> List[str]:
    words = text.split()
    if not words:
        return [text]

    chunks = []
    cur = []

    for w in words:
        candidate = " ".join(cur + [w]).strip()
        token_count = len(tokenizer(candidate, truncation=False, add_special_tokens=True)["input_ids"])

        if token_count <= max_length:
            cur.append(w)
        else:
            if cur:
                chunks.append(" ".join(cur))
            cur = [w]

    if cur:
        chunks.append(" ".join(cur))

    return chunks or [text]


def load_model(model_path: str):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    return tokenizer, model


def softmax_probs(logits: torch.Tensor) -> torch.Tensor:
    return torch.softmax(logits, dim=-1)


def get_id2label(model) -> Dict[int, str]:
    id2label = model.config.id2label
    if isinstance(id2label, dict):
        return {int(k): v for k, v in id2label.items()}
    return {i: str(v) for i, v in enumerate(id2label)}


def predict_single_text(text: str, tokenizer, model) -> Tuple[str, float]:
    max_length = min(getattr(tokenizer, "model_max_length", 512), 512)
    if max_length is None or max_length > 4096:
        max_length = 512

    chunks = chunk_for_model(text, tokenizer, max_length=max_length - 2)
    probs_accum = None

    with torch.no_grad():
        for chunk in chunks:
            inputs = tokenizer(
                chunk,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=False,
            )
            outputs = model(**inputs)
            probs = softmax_probs(outputs.logits)[0]
            probs_accum = probs if probs_accum is None else probs_accum + probs

    probs_mean = probs_accum / len(chunks)
    pred_idx = int(torch.argmax(probs_mean).item())
    conf = float(probs_mean[pred_idx].item())
    id2label = get_id2label(model)
    label = id2label[pred_idx]

    return label, conf


def apply_rule_heuristics(text: str, label: str, conf: float) -> Tuple[str, float, str]:
    source = "model"

    if looks_like_rule(text):
        if label != "rule" and conf < 0.80:
            return "rule", max(conf, 0.70), "heuristic"
        if label == "rule":
            return label, conf, source
    else:
        if label == "rule" and conf < 0.55:
            return "not_rule", max(1.0 - conf, 0.55), "heuristic"

    return label, conf, source


def continuation_score(prev_text: str, cur_text: str) -> bool:
    prev_text = prev_text.strip()
    cur_text = cur_text.strip()

    if not prev_text or not cur_text:
        return False

    if extract_rule_number(cur_text):
        return False

    if cur_text[:1].islower():
        return True

    if is_list_item(cur_text):
        return True

    if re.search(r'[:;,]\s*$', prev_text):
        return True

    if len(prev_text) < 250 and not re.search(r'[.!?]\s*$', prev_text):
        return True

    if is_short_continuation(cur_text):
        return True

    if re.match(
        r'^(?:а|б|в|г|д|е|при этом|в этом случае|если|где|затем|после|причем|'
        r'которые|который|которая|которое|нельзя|рекомендуется|используется|'
        r'используются|обязательно|обязательна|обязательны)\b',
        cur_text,
        flags=re.IGNORECASE,
    ):
        return True

    return False


def merge_adjacent_same_rules(results: List[Dict]) -> List[Dict]:
    if not results:
        return results

    merged = [results[0].copy()]

    for cur in results[1:]:
        prev = merged[-1]

        same_rule = prev.get("rule") == "rule" and cur.get("rule") == "rule"
        same_category = prev.get("category") == cur.get("category")
        close_pages = cur.get("page_start", 0) <= prev.get("page_end", 0) + 1
        continuation = continuation_score(prev.get("text", ""), cur.get("text", ""))

        same_rule_number = (
            prev.get("rule_number") is not None
            and cur.get("rule_number") is not None
            and prev.get("rule_number") == cur.get("rule_number")
        )

        should_merge = False

        if same_rule_number:
            should_merge = True
        elif same_rule and same_category and close_pages and continuation:
            should_merge = True
        elif same_rule and close_pages and continuation and is_short_continuation(cur.get("text", "")):
            should_merge = True

        if should_merge:
            prev["text"] = normalize_text(prev["text"] + " " + cur["text"])
            prev["page_end"] = cur.get("page_end", prev.get("page_end"))
            prev["rule_confidence"] = round(
                max(prev.get("rule_confidence", 0.0), cur.get("rule_confidence", 0.0)),
                4,
            )

            pc = prev.get("category_confidence")
            cc = cur.get("category_confidence")
            if pc is not None and cc is not None:
                prev["category_confidence"] = round(max(pc, cc), 4)

            if prev.get("source") != cur.get("source"):
                prev["source"] = "hybrid"

            if prev.get("rule_number") is None and cur.get("rule_number") is not None:
                prev["rule_number"] = cur["rule_number"]
        else:
            merged.append(cur.copy())

    for i, item in enumerate(merged, 1):
        item["id"] = i

    return merged


def postprocess_results(results: List[Dict]) -> List[Dict]:
    cleaned = []

    for item in results:
        text = normalize_text(item["text"])

        if len(text) < 12:
            continue

        if is_heading(text) and not looks_like_rule(text):
            continue

        item = item.copy()
        item["text"] = text
        cleaned.append(item)

    cleaned = merge_adjacent_same_rules(cleaned)

    for i, item in enumerate(cleaned, 1):
        item["id"] = i

    return cleaned


def classify_fragments(
    fragments: List[Dict],
    rule_tokenizer,
    rule_model,
    category_tokenizer=None,
    category_model=None,
    threshold: float = 0.65,
) -> List[Dict]:
    results = []

    for fragment in fragments:
        text = fragment["text"]

        rule_label, rule_conf = predict_single_text(text, rule_tokenizer, rule_model)
        rule_label, rule_conf, source = apply_rule_heuristics(text, rule_label, rule_conf)

        if rule_label == "rule" and rule_conf < threshold:
            rule_label = "not_rule"

        category = None
        category_conf = None

        if rule_label == "rule" and category_tokenizer is not None and category_model is not None:
            category, category_conf = predict_single_text(text, category_tokenizer, category_model)
            category_conf = float(category_conf)

        results.append({
            "id": fragment["id"],
            "text": text,
            "page_start": fragment["page_start"],
            "page_end": fragment["page_end"],
            "rule_number": fragment.get("rule_number"),
            "rule": rule_label,
            "rule_confidence": round(float(rule_conf), 4),
            "source": source,
            "category": category,
            "category_confidence": round(category_conf, 4) if category_conf is not None else None,
        })

    return results


def process_pdf(
    pdf_path: str,
    rule_model_path: str,
    category_model_path: Optional[str] = None,
    threshold: float = 0.65,
    dump_fragments_path: Optional[str] = None,
) -> Dict:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF не найден: {pdf_path}")

    if not os.path.exists(rule_model_path):
        raise FileNotFoundError(f"Модель правил не найдена: {rule_model_path}")

    if category_model_path and not os.path.exists(category_model_path):
        raise FileNotFoundError(f"Модель категорий не найдена: {category_model_path}")

    pages = read_pdf_pages(pdf_path)
    fragments = generate_fragments(pages)

    if dump_fragments_path:
        with open(dump_fragments_path, "w", encoding="utf-8") as f:
            json.dump(fragments, f, ensure_ascii=False, indent=2)

    rule_tokenizer, rule_model = load_model(rule_model_path)

    category_tokenizer = None
    category_model = None
    if category_model_path:
        category_tokenizer, category_model = load_model(category_model_path)

    results = classify_fragments(
        fragments=fragments,
        rule_tokenizer=rule_tokenizer,
        rule_model=rule_model,
        category_tokenizer=category_tokenizer,
        category_model=category_model,
        threshold=threshold,
    )

    results = [x for x in results if x["rule"] == "rule"]
    results = postprocess_results(results)

    for i, item in enumerate(results, 1):
        item["id"] = i

    return {
        "total_fragments": len(fragments),
        "total_rules": len(results),
        "rule_threshold": threshold,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--rule-model", required=True)
    parser.add_argument("--category-model", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument("--dump-fragments", default=None)
    args = parser.parse_args()

    output = process_pdf(
        pdf_path=args.pdf,
        rule_model_path=args.rule_model,
        category_model_path=args.category_model,
        threshold=args.threshold,
        dump_fragments_path=args.dump_fragments,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()