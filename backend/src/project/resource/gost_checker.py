import os
import re
from typing import List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = True

class GostChecker:
    def __init__(self):
        self.rules = self._initialize_gost_rules()
    
    def _initialize_gost_rules(self) -> Dict[str, Any]:
        """Инициализация правил проверки по ГОСТ"""
        return {
            'structure': {
                'required_sections': [
                    'титульный лист', 'содержание', 'оглавление',
                    'введение', 'основная часть', 'заключение',
                    'список литературы', 'библиографический список'
                ],
                'min_pages': 10,
                'max_pages': 50
            },
            'formatting': {
                'font_family': 'Times New Roman',
                'font_size': 14,
                'line_spacing': 1.5,
                'margins': {'left': 30, 'right': 15, 'top': 20, 'bottom': 20},
                'paragraph_indent': 1.25
            },
            'content': {
                'min_words': 1500,
                'max_words': 5000,
                'required_keywords': ['актуальность', 'цель', 'задачи', 'методы']
            }
        }
    
    async def check_document(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Основная функция проверки документа на соответствие ГОСТ"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.docx' and DOCX_AVAILABLE:
            return await self._check_docx_document(file_path, original_filename)
        elif file_extension == '.pdf' and PDFPLUMBER_AVAILABLE:
            return await self._check_pdf_document(file_path, original_filename)
        else:
            return self._create_check_result(
                is_compliant=False,
                score=Decimal('0.0'),
                errors=['Неподдерживаемый формат файла или отсутствуют библиотеки для проверки'],
                warnings=[],
                details={'file_type': file_extension}
            )
    
    async def _check_docx_document(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Проверка DOCX документа"""
        try:
            doc = DocxDocument(file_path)
            
            # Собираем результаты проверок
            structure_results = self._check_structure_docx(doc)
            formatting_results = self._check_formatting_docx(doc)
            content_results = self._check_content_docx(doc, original_filename)
            
            # Объединяем результаты
            all_errors = structure_results['errors'] + formatting_results['errors'] + content_results['errors']
            all_warnings = structure_results['warnings'] + formatting_results['warnings'] + content_results['warnings']
            
            # Рассчитываем оценку
            total_checks = 20  # Общее количество проверок
            error_count = len(all_errors)
            warning_count = len(all_warnings)
            passed_checks = total_checks - error_count - (warning_count // 2)
            score = max(Decimal('0.0'), Decimal(str((passed_checks / total_checks) * 100)))
            
            is_compliant = error_count == 0 and score >= Decimal('80.0')
            
            return self._create_check_result(
                is_compliant=is_compliant,
                score=score,
                errors=all_errors,
                warnings=all_warnings,
                details={
                    'structure': structure_results['details'],
                    'formatting': formatting_results['details'],
                    'content': content_results['details']
                }
            )
            
        except Exception as e:
            return self._create_check_result(
                is_compliant=False,
                score=Decimal('0.0'),
                errors=[f'Ошибка при проверке DOCX документа: {str(e)}'],
                warnings=[],
                details={}
            )
    
    async def _check_pdf_document(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Проверка PDF документа"""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Собираем результаты проверок
                structure_results = self._check_structure_pdf(pdf)
                content_results = self._check_content_pdf(pdf, original_filename)
                
                # Объединяем результаты
                all_errors = structure_results['errors'] + content_results['errors']
                all_warnings = structure_results['warnings'] + content_results['warnings']
                
                # Рассчитываем оценку (для PDF меньше проверок)
                total_checks = 15
                error_count = len(all_errors)
                warning_count = len(all_warnings)
                passed_checks = total_checks - error_count - (warning_count // 2)
                score = max(Decimal('0.0'), Decimal(str((passed_checks / total_checks) * 100)))
                
                is_compliant = error_count == 0 and score >= Decimal('80.0')
                
                return self._create_check_result(
                    is_compliant=is_compliant,
                    score=score,
                    errors=all_errors,
                    warnings=all_warnings,
                    details={
                        'structure': structure_results['details'],
                        'content': content_results['details']
                    }
                )
                
        except Exception as e:
            return self._create_check_result(
                is_compliant=False,
                score=Decimal('0.0'),
                errors=[f'Ошибка при проверке PDF документа: {str(e)}'],
                warnings=[],
                details={}
            )
    
    def _check_structure_docx(self, doc) -> Dict[str, Any]:
        """Проверка структуры DOCX документа"""
        errors = []
        warnings = []
        details = {'sections_found': [], 'sections_missing': []}
        
        # Извлекаем весь текст для анализа структуры
        full_text = " ".join([paragraph.text.lower() for paragraph in doc.paragraphs if paragraph.text.strip()])
        
        # Проверяем наличие обязательных разделов
        required_sections = self.rules['structure']['required_sections']
        found_sections = []
        
        for section in required_sections:
            if section in full_text:
                found_sections.append(section)
            else:
                details['sections_missing'].append(section)
                if section in ['титульный лист', 'содержание', 'введение', 'заключение']:
                    errors.append(f"Отсутствует обязательный раздел: '{section}'")
                else:
                    warnings.append(f"Рекомендуется добавить раздел: '{section}'")
        
        details['sections_found'] = found_sections
        
        # Проверяем количество страниц (примерно)
        estimated_pages = len(full_text) // 1500  # Примерная оценка
        min_pages = self.rules['structure']['min_pages']
        max_pages = self.rules['structure']['max_pages']
        
        if estimated_pages < min_pages:
            warnings.append(f"Мало страниц ({estimated_pages}), рекомендуется не менее {min_pages}")
        if estimated_pages > max_pages:
            warnings.append(f"Много страниц ({estimated_pages}), рекомендуется не более {max_pages}")
        
        details['estimated_pages'] = estimated_pages
        
        return {'errors': errors, 'warnings': warnings, 'details': details}
    
    def _check_formatting_docx(self, doc) -> Dict[str, Any]:
        """Проверка форматирования DOCX документа"""
        errors = []
        warnings = []
        details = {'font_issues': [], 'formatting_issues': []}
        
        required_font = self.rules['formatting']['font_family']
        required_size = self.rules['formatting']['font_size']
        
        # Проверяем шрифты в первых 50 параграфах
        for i, paragraph in enumerate(doc.paragraphs[:50]):
            for run in paragraph.runs:
                if run.font.name and run.font.name != required_font:
                    details['font_issues'].append(f"Неверный шрифт: {run.font.name}")
                    errors.append(f"Шрифт должен быть {required_font}, обнаружен: {run.font.name}")
                    break
                
                if run.font.size and run.font.size.pt != required_size:
                    details['font_issues'].append(f"Неверный размер шрифта: {run.font.size.pt}")
                    warnings.append(f"Размер шрифта должен быть {required_size}pt, обнаружен: {run.font.size.pt}pt")
                    break
        
        # Проверяем отступы (упрощенно)
        for i, paragraph in enumerate(doc.paragraphs[:20]):
            if paragraph.text.strip():
                if paragraph.paragraph_format.first_line_indent is None:
                    details['formatting_issues'].append("Отсутствует красная строка")
                    warnings.append("Рекомендуется использовать абзацные отступы")
                    break
        
        return {'errors': errors, 'warnings': warnings, 'details': details}
    
    def _check_content_docx(self, doc, filename: str) -> Dict[str, Any]:
        """Проверка содержания DOCX документа"""
        errors = []
        warnings = []
        details = {'word_count': 0, 'keywords_found': []}
        
        # Подсчет слов
        word_count = 0
        full_text = ""
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                words = paragraph.text.split()
                word_count += len(words)
                full_text += paragraph.text.lower() + " "
        
        details['word_count'] = word_count
        
        # Проверка объема
        min_words = self.rules['content']['min_words']
        max_words = self.rules['content']['max_words']
        
        if word_count < min_words:
            errors.append(f"Недостаточный объем текста ({word_count} слов), минимум: {min_words}")
        elif word_count > max_words:
            warnings.append(f"Большой объем текста ({word_count} слов), максимум: {max_words}")
        
        # Проверка ключевых слов
        required_keywords = self.rules['content']['required_keywords']
        found_keywords = []
        
        for keyword in required_keywords:
            if keyword in full_text:
                found_keywords.append(keyword)
            else:
                warnings.append(f"Рекомендуется использовать ключевое слово: '{keyword}'")
        
        details['keywords_found'] = found_keywords
        
        # Проверка имени файла
        if not any(word in filename.lower() for word in ['курсовая', 'диплом', 'работа']):
            warnings.append("Рекомендуется указать тип работы в названии файла")
        
        return {'errors': errors, 'warnings': warnings, 'details': details}
    
    def _check_structure_pdf(self, pdf) -> Dict[str, Any]:
        """Проверка структуры PDF документа"""
        errors = []
        warnings = []
        details = {'sections_found': [], 'sections_missing': [], 'page_count': len(pdf.pages)}
        
        # Извлекаем текст со всех страниц
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text.lower() + " "
        
        # Проверяем наличие обязательных разделов
        required_sections = self.rules['structure']['required_sections']
        found_sections = []
        
        for section in required_sections:
            if section in full_text:
                found_sections.append(section)
            else:
                details['sections_missing'].append(section)
                if section in ['титульный лист', 'содержание', 'введение', 'заключение']:
                    errors.append(f"Отсутствует обязательный раздел: '{section}'")
                else:
                    warnings.append(f"Рекомендуется добавить раздел: '{section}'")
        
        details['sections_found'] = found_sections
        
        # Проверяем количество страниц
        page_count = len(pdf.pages)
        min_pages = self.rules['structure']['min_pages']
        max_pages = self.rules['structure']['max_pages']
        
        if page_count < min_pages:
            warnings.append(f"Мало страниц ({page_count}), рекомендуется не менее {min_pages}")
        if page_count > max_pages:
            warnings.append(f"Много страниц ({page_count}), рекомендуется не более {max_pages}")
        
        return {'errors': errors, 'warnings': warnings, 'details': details}
    
    def _check_content_pdf(self, pdf, filename: str) -> Dict[str, Any]:
        """Проверка содержания PDF документа"""
        errors = []
        warnings = []
        details = {'word_count': 0, 'keywords_found': []}
        
        # Извлекаем текст и подсчитываем слова
        full_text = ""
        word_count = 0
        
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text.lower() + " "
                words = text.split()
                word_count += len(words)
        
        details['word_count'] = word_count
        
        # Проверка объема
        min_words = self.rules['content']['min_words']
        max_words = self.rules['content']['max_words']
        
        if word_count < min_words:
            errors.append(f"Недостаточный объем текста ({word_count} слов), минимум: {min_words}")
        elif word_count > max_words:
            warnings.append(f"Большой объем текста ({word_count} слов), максимум: {max_words}")
        
        # Проверка ключевых слов
        required_keywords = self.rules['content']['required_keywords']
        found_keywords = []
        
        for keyword in required_keywords:
            if keyword in full_text:
                found_keywords.append(keyword)
            else:
                warnings.append(f"Рекомендуется использовать ключевое слово: '{keyword}'")
        
        details['keywords_found'] = found_keywords
        
        # Проверка имени файла
        if not any(word in filename.lower() for word in ['курсовая', 'диплом', 'работа']):
            warnings.append("Рекомендуется указать тип работы в названии файла")
        
        return {'errors': errors, 'warnings': warnings, 'details': details}
    
    def _create_check_result(self, is_compliant: bool, score: Decimal, errors: List[str], 
                           warnings: List[str], details: Dict[str, Any]) -> Dict[str, Any]:
        """Создание структурированного результата проверки"""
        return {
            'is_compliant': is_compliant,
            'score': score,
            'errors': errors,
            'warnings': warnings,
            'details': details,
            'checked_at': datetime.now().isoformat(),
            'summary': {
                'total_errors': len(errors),
                'total_warnings': len(warnings),
                'compliance_level': 'Идеален' if is_compliant else 'Требует доработки'
            }
        }