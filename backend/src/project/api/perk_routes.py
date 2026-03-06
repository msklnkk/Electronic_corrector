from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
import PyPDF2
import io
import re
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import pipeline
import torch

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    docx = None

router = APIRouter(tags=["AI"])
logger = logging.getLogger(__name__)

# Увеличил количество потоков
executor = ThreadPoolExecutor(max_workers=10)  # Больше потоков

REQUIRED_HEADINGS = ["Введение", "Заключение", "Список используемых источников", "Содержание"]

class TypoFound(BaseModel):
    original: str
    corrected: str
    page: int
    confidence: float

class PDFCheckResponse(BaseModel):
    filename: str
    total_pages: int
    found_headings: List[str]
    missing_headings: List[str]
    has_all_required: bool
    typos_found: List[TypoFound] = []
    stats: dict = {}

# PERK модель
perk_model = None

def init_perk():
    global perk_model
    try:
        print("Загружаем PERK (без ограничений)...")
        perk_model = pipeline(
            "text2text-generation",
            model="IlyaGusev/rut5_base_grammar_corrector",
            device=-1,  # CPU
            # Убрал max_length - модель сама решит
            # Убрал truncation - не обрезаем текст
        )
        print("PERK готов к работе!")
    except Exception as e:
        print(f"Ошибка загрузки PERK: {e}")
        perk_model = None

init_perk()

def find_typos_with_perk_ai(text: str) -> List[dict]:
    """ЧИСТЫЙ ИИ: PERK сам находит и исправляет ошибки"""
    if not perk_model or len(text.strip()) < 10:  # Минимальный порог уменьшил
        return []
    
    typos = []
    try:
        # Разбиваем на предложения, но берем ВСЕ
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            if len(sentence.strip()) < 5:  # Даже короткие предложения проверяем
                continue
            
            # PERK исправляет предложение
            corrected = perk_model(
                sentence.strip(),
                num_return_sequences=1,
                do_sample=False,
                temperature=0.1
            )[0]['generated_text']
            
            # Если предложение изменилось - ищем конкретные слова
            if corrected != sentence:
                orig_words = re.findall(r'\b[а-яА-ЯёЁ]{3,}\b', sentence)  # Слова от 3 букв
                corr_words = re.findall(r'\b[а-яА-ЯёЁ]{3,}\b', corrected)
                
                for orig, corr in zip(orig_words, corr_words):
                    if orig != corr:
                        # Уверенность на основе схожести
                        confidence = 1.0 - (sum(1 for a,b in zip(orig, corr) if a!=b) / len(orig))
                        
                        typos.append({
                            "original": orig,
                            "corrected": corr,
                            "confidence": max(0.5, confidence)  # Минимум уверенности снизил
                        })
        
        return typos  # Без ограничений на количество
        
    except Exception as e:
        logger.error(f"Ошибка PERK: {e}")
        return []

def process_page(text: str, page_num: int) -> List[TypoFound]:
    """Обработка одной страницы"""
    if len(text.strip()) < 20:
        return []
    
    typos = find_typos_with_perk_ai(text)
    
    return [
        TypoFound(
            original=t["original"],
            corrected=t["corrected"],
            page=page_num + 1,
            confidence=t["confidence"]
        ) for t in typos
    ]

def extract_docx_text(content: bytes) -> tuple[str, int]:
    if not DOCX_AVAILABLE:
        return "", 0
    try:
        doc = docx.Document(io.BytesIO(content))
        # Сохраняем все параграфы
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        text = "\n".join(paragraphs)
        # Считаем примерное количество страниц (1800 символов = страница)
        approx_pages = max(1, len(text) // 1800)
        return text, approx_pages
    except:
        return "", 0

@router.post("/pdf/ai-check", response_model=PDFCheckResponse)
async def ai_pdf_check(file: UploadFile = File(...)):
    if perk_model is None:
        raise HTTPException(status_code=503, detail="PERK ИИ не загружен")
    
    filename = file.filename.lower()
    if not (filename.endswith('.pdf') or filename.endswith('.docx')):
        raise HTTPException(status_code=400, detail="Только PDF или DOCX")

    try:
        content = await file.read()
        loop = asyncio.get_event_loop()
        
        if filename.endswith('.docx'):
            # DOCX обработка
            full_text, total_pages = extract_docx_text(content)
            
            if len(full_text) > 0:
                # Разбиваем на страницы по 2000 символов
                page_size = 2000
                num_pages = (len(full_text) + page_size - 1) // page_size
                pages = [full_text[i*page_size:(i+1)*page_size] for i in range(num_pages)]
                
                # Запускаем параллельную обработку ВСЕХ страниц
                tasks = []
                for i, page_text in enumerate(pages):
                    task = loop.run_in_executor(executor, process_page, page_text, i)
                    tasks.append(task)
                
                # Собираем ВСЕ результаты
                results = await asyncio.gather(*tasks)
                all_typos = [typo for result in results for typo in result]
                full_text_for_headings = full_text
            else:
                all_typos = []
                full_text_for_headings = ""
                total_pages = 0
        else:
            # PDF обработка - ВСЕ страницы
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            total_pages = len(pdf_reader.pages)
            
            full_text_for_headings = ""
            pages_text = []
            
            # Собираем текст со ВСЕХ страниц
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text() or ""
                full_text_for_headings += page_text + "\n"
                pages_text.append((page_text, page_num))
            
            # Запускаем параллельную обработку ВСЕХ страниц
            tasks = []
            for page_text, page_num in pages_text:
                if len(page_text.strip()) > 0:  # Проверяем все непустые страницы
                    task = loop.run_in_executor(executor, process_page, page_text, page_num)
                    tasks.append(task)
            
            # Собираем ВСЕ результаты
            results = await asyncio.gather(*tasks)
            all_typos = [typo for result in results for typo in result]
        
        # Поиск заголовков
        found_headings = []
        for heading in REQUIRED_HEADINGS:
            if re.search(rf'\b{re.escape(heading)}\b', full_text_for_headings, re.IGNORECASE):
                found_headings.append(heading)
        
        missing_headings = [h for h in REQUIRED_HEADINGS if h not in found_headings]
        
        # Убираем дубликаты, но сохраняем все уникальные ошибки
        seen = set()
        unique_typos = []
        for typo in all_typos:
            key = f"{typo.original}_{typo.corrected}"
            if key not in seen:
                seen.add(key)
                unique_typos.append(typo)
        
        stats = {
            "total_pages_checked": total_pages,
            "total_typos_before_deduplication": len(all_typos),
            "unique_typos": len(unique_typos),
            "ai_model": "PERK (без ограничений)",
            "type": "чистый ИИ",
            "confidence_avg": sum(t.confidence for t in unique_typos) / len(unique_typos) if unique_typos else 0
        }
        
        return PDFCheckResponse(
            filename=file.filename,
            total_pages=total_pages,
            found_headings=found_headings,
            missing_headings=missing_headings,
            has_all_required=len(found_headings) == 4,
            typos_found=unique_typos,  # Все уникальные ошибки
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    return {
        "status": "PERK БЕЗ ОГРАНИЧЕНИЙ",
        "model_loaded": perk_model is not None,
        "max_pages": "не ограничено",
        "max_errors": "не ограничено",
        "docx_support": DOCX_AVAILABLE,
        "parallel_workers": 10,
        "ai_type": "Чистый ИИ без ограничений"
    }

@router.on_event("shutdown")
async def shutdown():
    executor.shutdown(wait=True)