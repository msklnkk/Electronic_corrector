import io
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pdfplumber
import PyPDF2
import torch
from transformers import AutoModel, AutoTokenizer

from project.schemas.bert_rules import ExtractedRule


MODEL_NAME = "cointegrated/rubert-tiny2"

CATEGORY_ANCHORS = {
    "formatting": [
        "оформление текста",
        "шрифт размер поля интервал отступ",
        "требования к форматированию",
        "текст работы следует печатать",
        "размер шрифта межстрочный интервал поля страницы",
    ],
    "structure": [
        "структура документа",
        "обязательные разделы",
        "введение заключение содержание",
        "структурные элементы работы",
        "титульный лист содержание введение основная часть заключение приложения",
        "работа должна содержать разделы",
    ],
    "tables": [
        "оформление таблиц",
        "название таблицы",
        "таблицы и подписи",
        "таблицы следует нумеровать",
    ],
    "figures": [
        "оформление рисунков",
        "подпись рисунка",
        "иллюстрации и схемы",
        "рисунки следует нумеровать",
    ],
    "references": [
        "список использованных источников",
        "оформление литературы",
        "библиографические ссылки",
        "оформление ссылок и источников",
    ],
    "general": [
        "требования к документу",
        "правила оформления",
        "нормативные требования",
        "общие требования к оформлению",
    ],
}

RULE_PATTERNS = [
    r"\bдолжен\b",
    r"\bдолжна\b",
    r"\bдолжны\b",
    r"\bдолжно\b",
    r"\bследует\b",
    r"\bнеобходимо\b",
    r"\bтребуется\b",
    r"\bне допускается\b",
    r"\bне допускаются\b",
    r"\bдопускается\b",
    r"\bрекомендуется\b",
    r"\bоформляется\b",
    r"\bоформляются\b",
    r"\bпечатают\b",
    r"\bследует печатать\b",
    r"\bследует указывать\b",
    r"\bследует располагать\b",
    r"\bследует нумеровать\b",
    r"\bдолжен содержать\b",
    r"\bдолжно содержать\b",
    r"\bдолжна быть\b",
    r"\bдолжен быть\b",
    r"\bдолжны быть\b",
    r"\bдолжна включать\b",
    r"\bвключает\b",
    r"\bвключают\b",
    r"\bначинается с нового листа\b",
    r"\bнумеровать\b",
    r"\bпроставляют\b",
    r"\bрасполагают\b",
    r"\bне ставится\b",
    r"\bне ставят\b",
    r"\bшрифт\b",
    r"\bинтервал\b",
    r"\bполя\b",
    r"\bполя страницы\b",
    r"\bотступ\b",
    r"\bтаблица\b",
    r"\bтаблицы\b",
    r"\bрисунок\b",
    r"\bрисунки\b",
    r"\bиллюстрации\b",
    r"\bсписок использованных источников\b",
    r"\bссылк(?:а|и|ок)\b",
]

SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,3})[\)\.]?\s+(.+)$")
RULE_RE = re.compile("|".join(RULE_PATTERNS), flags=re.IGNORECASE)
MULTISPACE_RE = re.compile(r"\s+")
BULLET_RE = re.compile(r"^[\-\u2022\u25CF\u25E6\u2043\u2219•]\s*")
HYPHEN_LINEBREAK_RE = re.compile(r"(\w+)-\s+(\w+)")


@dataclass
class TextBlock:
    page: int
    section: Optional[str]
    title: str
    text: str


class BertRuleReader:
    def __init__(self, model_name: str = MODEL_NAME):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

        self.anchor_embeddings = {
            category: [self._embed_text(anchor) for anchor in anchors]
            for category, anchors in CATEGORY_ANCHORS.items()
        }

    def extract_rules_from_pdf(self, pdf_bytes: bytes) -> Tuple[int, List[ExtractedRule]]:
        pages = self._extract_pages_text(pdf_bytes)
        blocks = self._build_blocks(pages)
        rules = self._extract_rules(blocks)
        return len(pages), rules

    def _extract_pages_text(self, pdf_bytes: bytes) -> List[str]:
        texts: List[str] = []

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text() or ""
                    texts.append(self._postprocess_page_text(txt))
        except Exception:
            texts = []

        if not any(t.strip() for t in texts):
            texts = []
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                txt = page.extract_text() or ""
                texts.append(self._postprocess_page_text(txt))

        return texts

    def _build_blocks(self, pages: List[str]) -> List[TextBlock]:
        blocks: List[TextBlock] = []

        for page_num, page_text in enumerate(pages, start=1):
            lines = [self._normalize(line) for line in page_text.splitlines()]
            lines = [line for line in lines if line]

            current_section: Optional[str] = None
            current_lines: List[str] = []

            def flush():
                nonlocal current_lines, current_section
                if current_lines:
                    text = self._normalize(" ".join(current_lines))
                    if len(text) > 25:
                        blocks.append(
                            TextBlock(
                                page=page_num,
                                section=current_section,
                                title=self._make_title(current_section, text),
                                text=text,
                            )
                        )
                current_lines = []

            for line in lines:
                if self._is_noise_line(line):
                    continue

                section_match = SECTION_RE.match(line)
                if section_match:
                    flush()
                    current_section = section_match.group(1)
                    rest = section_match.group(2).strip()
                    if rest:
                        current_lines.append(rest)
                    continue

                current_lines.append(line)

            flush()

        return blocks

    def _extract_rules(self, blocks: List[TextBlock]) -> List[ExtractedRule]:
        results: List[ExtractedRule] = []

        for block in blocks:
            sentences = self._split_sentences(block.text)

            for sentence in sentences:
                sentence = self._normalize(sentence)

                if len(sentence) < 20:
                    continue
                if self._should_skip_sentence(sentence):
                    continue

                lexical_score = self._lexical_score(sentence)
                semantic_score, bert_category = self._semantic_score(sentence)
                keyword_category = self._keyword_category(sentence)

                category = keyword_category or bert_category
                final_score = 0.55 * lexical_score + 0.45 * semantic_score

                if final_score < 0.45:
                    continue

                results.append(
                    ExtractedRule(
                        section=block.section,
                        title=self._make_title(block.section, sentence),
                        text=sentence,
                        page=block.page,
                        category=category,
                        confidence=round(float(final_score), 3),
                    )
                )

        return self._deduplicate(results)

    def _keyword_category(self, text: str) -> Optional[str]:
        low = text.lower()

        table_words = [
            "таблица", "таблицы", "графа", "графы", "строка", "строки",
            "боковик", "головка таблицы", "продолжение таблицы"
        ]
        figure_words = [
            "рисунок", "рисунки", "иллюстрация", "иллюстрации", "под рисунком"
        ]
        reference_words = [
            "ссылка", "ссылки", "сноска", "сноски", "источник",
            "источники", "библиограф", "список использованных источников"
        ]
        formatting_words = [
            "шрифт", "кегль", "интервал", "межстрочный", "поля", "поля страницы",
            "отступ", "цвет шрифта", "размером 14", "размер шрифта", "центр", "слева"
        ]
        structure_words = [
            "раздел", "подраздел", "пункт", "подпункт", "приложение",
            "содержание", "введение", "заключение", "титульный лист",
            "структурный элемент", "основная часть", "нумерация страниц", "страницы работы"
        ]

        if any(word in low for word in table_words):
            return "tables"
        if any(word in low for word in figure_words):
            return "figures"
        if any(word in low for word in reference_words):
            return "references"
        if any(word in low for word in formatting_words):
            return "formatting"
        if any(word in low for word in structure_words):
            return "structure"

        return None

    def _lexical_score(self, text: str) -> float:
        hits = len(RULE_RE.findall(text))
        number_bonus = 0.12 if re.search(r"\b\d+[.,]?\d*\b", text) else 0.0
        gost_bonus = 0.10 if "гост" in text.lower() else 0.0
        section_like_bonus = 0.08 if re.search(r"\b[А-ЯA-Z]?\d+([.,]\d+)?\b", text) else 0.0
        length_penalty = -0.10 if len(text.split()) < 4 else 0.0

        score = hits * 0.20 + number_bonus + gost_bonus + section_like_bonus + length_penalty
        return max(0.0, min(1.0, score))

    def _semantic_score(self, text: str) -> Tuple[float, str]:
        text_embedding = self._embed_text(text)
        best_score = 0.0
        best_category = "general"

        for category, anchor_embeddings in self.anchor_embeddings.items():
            sims = [self._cosine_similarity(text_embedding, emb) for emb in anchor_embeddings]
            category_score = max(sims) if sims else 0.0
            if category_score > best_score:
                best_score = category_score
                best_category = category

        return float(best_score), best_category

    def _embed_text(self, text: str) -> torch.Tensor:
        encoded = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256,
        )

        with torch.no_grad():
            output = self.model(**encoded)

        hidden = output.last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1)
        masked_hidden = hidden * mask
        summed = masked_hidden.sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1)
        mean_pooled = summed / counts

        return mean_pooled[0]

    def _cosine_similarity(self, a: torch.Tensor, b: torch.Tensor) -> float:
        return torch.nn.functional.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0)).item()

    def _split_sentences(self, text: str) -> List[str]:
        text = self._normalize(text)
        parts = re.split(r"(?<=[.!?;:])\s+", text)
        merged: List[str] = []

        buffer = ""
        for part in parts:
            part = part.strip()
            if not part:
                continue

            if buffer:
                if len(buffer.split()) < 4:
                    buffer = f"{buffer} {part}"
                else:
                    merged.append(buffer)
                    buffer = part
            else:
                buffer = part

        if buffer:
            merged.append(buffer)

        return merged

    def _should_skip_sentence(self, sentence: str) -> bool:
        words = sentence.split()
        low = sentence.lower()

        if BULLET_RE.match(sentence) and len(words) < 5:
            return True

        if sentence.endswith(";") and len(words) < 6:
            return True

        if len(words) <= 2:
            return True

        if sentence.startswith(("Пример -", "Пример оформления")):
            return True

        if low.startswith("пример "):
            return True

        if "пример оформления таблицы" in low:
            return True

        return False

    def _make_title(self, section: Optional[str], text: str) -> str:
        if section:
            return f"Пункт {section}"

        words = text.split()
        short = " ".join(words[:8]).strip()
        if len(words) > 8:
            short += "..."
        return short or "Без названия"

    def _deduplicate(self, rules: List[ExtractedRule]) -> List[ExtractedRule]:
        seen = set()
        result = []

        for rule in sorted(rules, key=lambda x: (x.page, x.section or "", -x.confidence)):
            normalized_text = re.sub(r"[«»\"'()]", "", rule.text.lower()).strip()
            key = ((rule.section or "").strip().lower(), normalized_text)
            if key in seen:
                continue
            seen.add(key)
            result.append(rule)

        return result

    def _normalize(self, text: str) -> str:
        text = text.replace("\u00ad", "")
        text = HYPHEN_LINEBREAK_RE.sub(r"\1\2", text)
        text = text.replace("–", "-").replace("—", "-")
        return MULTISPACE_RE.sub(" ", text).strip()

    def _postprocess_page_text(self, text: str) -> str:
        text = text.replace("\u00ad", "")
        text = HYPHEN_LINEBREAK_RE.sub(r"\1\2", text)
        return text

    def _is_noise_line(self, line: str) -> bool:
        if re.fullmatch(r"\d+", line):
            return True

        low = line.lower()
        noise = [
            "министерство науки",
            "федеральное государственное",
            "кафедра",
        ]
        return any(x in low for x in noise)