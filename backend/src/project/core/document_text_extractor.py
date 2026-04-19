from pathlib import Path

import fitz
from docx import Document


def extract_pdf_text(file_path: str) -> str:
    doc = fitz.open(file_path)
    parts = []
    try:
        for page in doc:
            text = page.get_text("text")
            if text and text.strip():
                parts.append(text.strip())
    finally:
        doc.close()
    return "\n\n".join(parts).strip()


def extract_docx_text(file_path: str) -> str:
    doc = Document(file_path)
    parts = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    return "\n\n".join(parts).strip()


def extract_txt_text(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="ignore").strip()


def extract_document_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_pdf_text(file_path)
    if ext == ".docx":
        return extract_docx_text(file_path)
    if ext == ".txt":
        return extract_txt_text(file_path)

    raise ValueError(f"Неподдерживаемый формат файла: {ext}")