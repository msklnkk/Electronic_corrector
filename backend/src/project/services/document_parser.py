import io
import re
from typing import List, Optional, TypedDict
import pdfplumber


class ParsedBlock(TypedDict):
    page: int
    section: Optional[str]
    text: str
    block_type: str


SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\b")


def clean_line(text: str) -> str:
    text = text.replace("", "-")
    text = text.replace("•", "-")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("…", "...")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_service_line(line: str) -> bool:
    low = line.lower().strip()

    if not low:
        return True

    if re.fullmatch(r"\d+", low):
        return True

    if "сто " in low and re.search(r"\d{4}", low):
        return True

    return False


def detect_section(text: str) -> Optional[str]:
    match = SECTION_RE.match(text)
    return match.group(1) if match else None


def starts_new_block(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    if SECTION_RE.match(line):
        return True

    if re.match(r"^[-•]\s+", line):
        return True

    if re.match(r"^[а-яa-z]\)\s+", line, flags=re.IGNORECASE):
        return True

    return False


def merge_lines_to_blocks(lines: List[str], page_num: int) -> List[ParsedBlock]:
    blocks: List[ParsedBlock] = []
    current: List[str] = []

    for raw_line in lines:
        line = clean_line(raw_line)

        if is_service_line(line):
            continue

        if not line:
            if current:
                text = " ".join(current).strip()
                blocks.append(
                    {
                        "page": page_num,
                        "section": detect_section(text),
                        "text": text,
                        "block_type": "paragraph",
                    }
                )
                current = []
            continue

        if current and starts_new_block(line):
            text = " ".join(current).strip()
            blocks.append(
                {
                    "page": page_num,
                    "section": detect_section(text),
                    "text": text,
                    "block_type": "paragraph",
                }
            )
            current = [line]
            continue

        current.append(line)

    if current:
        text = " ".join(current).strip()
        blocks.append(
            {
                "page": page_num,
                "section": detect_section(text),
                "text": text,
                "block_type": "paragraph",
            }
        )

    return blocks


def parse_pdf_to_blocks(content: bytes) -> List[ParsedBlock]:
    result: List[ParsedBlock] = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            result.extend(merge_lines_to_blocks(lines, page_num))

    return result