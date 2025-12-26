import os
import re
from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal
from datetime import datetime
import asyncio
from dataclasses import dataclass
from enum import Enum

try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, Inches
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pdfplumber
    from pdfplumber.page import Page
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

class ErrorSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class PageError:
    page_number: int
    error_type: str
    description: str
    severity: ErrorSeverity
    position: Optional[Tuple[float, float]] = None  # x, y coordinates
    context: Optional[str] = None

class EnhancedGostChecker:
    def __init__(self):
        self.rules = self._initialize_gost_rules()
        self.page_errors: Dict[int, List[PageError]] = {}
        
    def _initialize_gost_rules(self) -> Dict[str, Any]:
        """Инициализация правил проверки по ГОСТ с учетом страниц"""
        return {
            'structure': {
                'required_sections': [
                    {'name': 'титульный лист', 'expected_page': 1, 'critical': True},
                    {'name': 'оглавление', 'expected_page': 2, 'critical': True},
                    {'name': 'введение', 'expected_page_range': (3, 5), 'critical': True},
                    {'name': 'заключение', 'critical': True},
                    {'name': 'список литературы', 'critical': True}
                ],
                'page_rules': {
                    'min_pages': 20,
                    'max_pages': 60,
                    'first_page_number': 1,
                    'margin_left': 30,  # mm
                    'margin_right': 15,
                    'margin_top': 20,
                    'margin_bottom': 20
                }
            },
            'formatting': {
                'font': {
                    'family': 'Times New Roman',
                    'size_main': 14,
                    'size_heading': 16,
                    'line_spacing': 1.5
                },
                'paragraph': {
                    'indent_first_line': 1.25,
                    'alignment': 'justify',
                    'spacing_after': 0
                }
            },
            'content': {
                'min_words_per_page': 250,
                'max_words_per_page': 450,
                'required_on_first_page': [
                    'МИНИСТЕРСТВО',
                    'УНИВЕРСИТЕТ',
                    'КАФЕДРА',
                    'КУРСОВАЯ РАБОТА'
                ]
            }
        }
    
    async def check_document_with_pages(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Проверка документа с детализацией по страницам"""
        self.page_errors.clear()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.docx' and DOCX_AVAILABLE:
            return await self._check_docx_with_pages(file_path, filename)
        elif file_ext == '.pdf' and PDFPLUMBER_AVAILABLE:
            return await self._check_pdf_with_pages(file_path, filename)
        else:
            return self._create_error_result("Неподдерживаемый формат файла")
    
    async def _check_pdf_with_pages(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Детальная проверка PDF по страницам"""
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                
                # Проверка структуры по страницам
                structure_results = await self._analyze_pdf_structure(pdf, filename)
                
                # Проверка форматирования на каждой странице
                for page_num, page in enumerate(pdf.pages, 1):
                    await self._check_pdf_page_formatting(page, page_num)
                
                # Проверка содержания
                content_results = await self._analyze_pdf_content(pdf, filename)
                
                # Объединяем все ошибки
                all_errors = self._collect_all_errors()
                
                # Рассчитываем оценку с учетом постраничных ошибок
                score = self._calculate_score_with_pages(total_pages)
                
                return self._create_detailed_result(
                    score=score,
                    total_pages=total_pages,
                    page_errors=self.page_errors,
                    structure_results=structure_results,
                    content_results=content_results
                )
                
        except Exception as e:
            return self._create_error_result(f"Ошибка проверки PDF: {str(e)}")
    
    async def _analyze_pdf_structure(self, pdf, filename: str) -> Dict[str, Any]:
        """Анализ структуры PDF документа"""
        results = {
            'sections_found': [],
            'sections_missing': [],
            'page_issues': []
        }
        
        full_text_by_page = {}
        
        # Собираем текст по страницам
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            full_text_by_page[page_num] = text.lower()
            
            # Проверка полей страницы
            self._check_page_margins(page, page_num)
            
            # Проверка нумерации
            if page_num == 1 and not self._is_title_page(text):
                self._add_page_error(
                    page_num, 
                    "Структура",
                    "Первая страница должна быть титульным листом",
                    ErrorSeverity.CRITICAL
                )
        
        # Проверяем обязательные разделы
        for section in self.rules['structure']['required_sections']:
            found = False
            for page_num, text in full_text_by_page.items():
                if section['name'] in text:
                    found = True
                    results['sections_found'].append({
                        'name': section['name'],
                        'page': page_num,
                        'expected_page': section.get('expected_page')
                    })
                    break
            
            if not found and section.get('critical', False):
                results['sections_missing'].append(section['name'])
                self._add_page_error(
                    1,  # Общая ошибка документа
                    "Структура",
                    f"Отсутствует обязательный раздел: {section['name']}",
                    ErrorSeverity.CRITICAL
                )
        
        return results
    
    async def _check_pdf_page_formatting(self, page: Page, page_num: int):
        """Проверка форматирования отдельной страницы PDF"""
        text = page.extract_text() or ""
        
        # Проверка плотности текста (не должно быть слишком пусто)
        word_count = len(text.split())
        min_words = self.rules['content']['min_words_per_page']
        max_words = self.rules['content']['max_words_per_page']
        
        if page_num > 2:  # Не проверяем титул и оглавление
            if word_count < min_words:
                self._add_page_error(
                    page_num,
                    "Форматирование",
                    f"Слишком мало текста на странице: {word_count} слов (минимум {min_words})",
                    ErrorSeverity.WARNING
                )
            elif word_count > max_words:
                self._add_page_error(
                    page_num,
                    "Форматирование",
                    f"Слишком много текста на странице: {word_count} слов (максимум {max_words})",
                    ErrorSeverity.WARNING
                )
        
        # Проверка выравнивания (по наличию рваных правых краев)
        lines = text.split('\n')
        line_lengths = [len(line.strip()) for line in lines if line.strip()]
        
        if line_lengths:
            avg_length = sum(line_lengths) / len(line_lengths)
            # Если есть большие различия в длине строк - возможно не выравнивание по ширине
            if max(line_lengths) - min(line_lengths) > avg_length * 0.5:
                self._add_page_error(
                    page_num,
                    "Форматирование",
                    "Возможно отсутствие выравнивания текста по ширине",
                    ErrorSeverity.WARNING
                )
    
    def _check_page_margins(self, page: Page, page_num: int):
        """Проверка полей страницы"""
        bbox = page.bbox
        width = bbox[2] - bbox[0]  # ширина в пунктах
        height = bbox[3] - bbox[1]  # высота в пунктах
        
        # Конвертируем мм в пункты (1 мм = 2.83465 пунктов)
        expected_margin_left = self.rules['structure']['page_rules']['margin_left'] * 2.83465
        expected_margin_right = self.rules['structure']['page_rules']['margin_right'] * 2.83465
        
        # Получаем текст и его bounding box
        words = page.extract_words()
        if words:
            # Находим самый левый и самый правый текст
            leftmost = min(word['x0'] for word in words)
            rightmost = max(word['x1'] for word in words)
            
            # Проверяем левое поле
            if leftmost < expected_margin_left * 0.8:  # Допуск 20%
                self._add_page_error(
                    page_num,
                    "Поля страницы",
                    f"Левое поле слишком узкое: {leftmost/2.83465:.1f} мм (должно быть {self.rules['structure']['page_rules']['margin_left']} мм)",
                    ErrorSeverity.CRITICAL
                )
            
            # Проверяем правое поле
            if width - rightmost < expected_margin_right * 0.8:
                self._add_page_error(
                    page_num,
                    "Поля страницы",
                    f"Правое поле слишком узкое: {(width - rightmost)/2.83465:.1f} мм (должно быть {self.rules['structure']['page_rules']['margin_right']} мм)",
                    ErrorSeverity.CRITICAL
                )
    
    def _is_title_page(self, text: str) -> bool:
        """Проверка, является ли страница титульным листом"""
        text_lower = text.lower()
        
        # Проверяем обязательные элементы титульного листа
        required_elements = self.rules['content']['required_on_first_page']
        found_elements = sum(1 for elem in required_elements if elem.lower() in text_lower)
        
        # Должно быть хотя бы 3 из обязательных элементов
        return found_elements >= 3
    
    def _add_page_error(self, page_num: int, error_type: str, 
                       description: str, severity: ErrorSeverity,
                       position: Optional[Tuple[float, float]] = None,
                       context: Optional[str] = None):
        """Добавление ошибки с привязкой к странице"""
        if page_num not in self.page_errors:
            self.page_errors[page_num] = []
        
        self.page_errors[page_num].append(PageError(
            page_number=page_num,
            error_type=error_type,
            description=description,
            severity=severity,
            position=position,
            context=context
        ))
    
    async def _analyze_pdf_content(self, pdf, filename: str) -> Dict[str, Any]:
        """Анализ содержания PDF"""
        results = {
            'total_words': 0,
            'keywords_found': [],
            'recommendations': []
        }
        
        # Анализ по страницам
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            words = text.split()
            results['total_words'] += len(words)
            
            # Проверка ключевых слов на каждой странице
            if page_num <= 5:  # Проверяем только в начале документа
                self._check_keywords_on_page(text, page_num)
        
        return results
    
    def _check_keywords_on_page(self, text: str, page_num: int):
        """Проверка ключевых слов на странице"""
        text_lower = text.lower()
        required_keywords = ['актуальность', 'цель', 'задача', 'метод', 'результат']
        
        for keyword in required_keywords:
            if keyword in text_lower and page_num <= 3:
                # Ключевые слова должны быть во введении (первые 2-3 страницы)
                pass
            elif keyword in text_lower and page_num > 3:
                self._add_page_error(
                    page_num,
                    "Содержание",
                    f"Ключевое слово '{keyword}' не должно встречаться на странице {page_num}",
                    ErrorSeverity.WARNING
                )
    
    def _collect_all_errors(self) -> List[Dict]:
        """Сбор всех ошибок в плоский список"""
        all_errors = []
        for page_num, errors in self.page_errors.items():
            for error in errors:
                all_errors.append({
                    'page': page_num,
                    'type': error.error_type,
                    'description': error.description,
                    'severity': error.severity.value,
                    'position': error.position,
                    'context': error.context
                })
        return all_errors
    
    def _calculate_score_with_pages(self, total_pages: int) -> Decimal:
        """Расчет оценки с учетом постраничных ошибок"""
        if not self.page_errors:
            return Decimal('100.0')
        
        total_errors = sum(len(errors) for errors in self.page_errors.values())
        critical_errors = sum(
            1 for errors in self.page_errors.values() 
            for error in errors 
            if error.severity == ErrorSeverity.CRITICAL
        )
        
        # Базовый штраф
        base_penalty = min(total_errors * 5, 50)  # Максимум 50% штрафа
        
        # Дополнительный штраф за критические ошибки
        critical_penalty = critical_errors * 10
        
        # Штраф за ошибки на первых страницах (более важных)
        first_pages_penalty = 0
        for page_num in range(1, min(4, total_pages + 1)):
            if page_num in self.page_errors:
                first_pages_penalty += len(self.page_errors[page_num]) * 3
        
        total_penalty = min(base_penalty + critical_penalty + first_pages_penalty, 100)
        
        return Decimal(str(100 - total_penalty))
    
    def _create_detailed_result(self, score: Decimal, total_pages: int,
                              page_errors: Dict[int, List[PageError]],
                              structure_results: Dict, content_results: Dict) -> Dict[str, Any]:
        """Создание детализированного результата"""
        
        # Группируем ошибки по типам для статистики
        error_stats = {
            'critical': 0,
            'warning': 0,
            'info': 0
        }
        
        for errors in page_errors.values():
            for error in errors:
                error_stats[error.severity.value] += 1
        
        return {
            'is_compliant': error_stats['critical'] == 0 and score >= Decimal('70.0'),
            'score': score,
            'total_pages': total_pages,
            'page_errors': self._serialize_page_errors(page_errors),
            'error_statistics': error_stats,
            'structure': structure_results,
            'content': content_results,
            'summary': {
                'total_errors': sum(error_stats.values()),
                'critical_errors': error_stats['critical'],
                'pages_with_errors': len(page_errors),
                'compliance_level': 'Соответствует' if score >= 70 else 'Требует доработки',
                'recommended_actions': self._generate_recommendations(page_errors)
            },
            'checked_at': datetime.now().isoformat()
        }
    
    def _serialize_page_errors(self, page_errors: Dict[int, List[PageError]]) -> Dict[int, List[Dict]]:
        """Сериализация ошибок страниц"""
        result = {}
        for page_num, errors in page_errors.items():
            result[page_num] = [
                {
                    'type': error.error_type,
                    'description': error.description,
                    'severity': error.severity.value,
                    'position': error.position,
                    'context': error.context
                }
                for error in errors
            ]
        return result
    
    def _generate_recommendations(self, page_errors: Dict[int, List[PageError]]) -> List[str]:
        """Генерация рекомендаций по исправлению"""
        recommendations = []
        
        # Анализируем наиболее частые ошибки
        error_types = {}
        for errors in page_errors.values():
            for error in errors:
                if error.error_type not in error_types:
                    error_types[error.error_type] = 0
                error_types[error.error_type] += 1
        
        # Формируем рекомендации
        if 'Поля страницы' in error_types:
            recommendations.append("Отрегулируйте поля страницы согласно ГОСТ: левое 30мм, правое 15мм")
        
        if 'Структура' in error_types:
            recommendations.append("Проверьте наличие всех обязательных разделов: титульный лист, оглавление, введение, заключение, список литературы")
        
        if 'Форматирование' in error_types:
            recommendations.append("Используйте выравнивание текста по ширине и соблюдайте единый стиль форматирования")
        
        if not recommendations:
            recommendations.append("Документ в целом соответствует требованиям, обратите внимание на отдельные замечания")
        
        return recommendations
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создание результата с ошибкой"""
        return {
            'is_compliant': False,
            'score': Decimal('0.0'),
            'total_pages': 0,
            'page_errors': {},
            'error_statistics': {'critical': 1, 'warning': 0, 'info': 0},
            'structure': {'error': error_message},
            'content': {},
            'summary': {
                'total_errors': 1,
                'critical_errors': 1,
                'pages_with_errors': 0,
                'compliance_level': 'Ошибка проверки',
                'recommended_actions': ['Исправьте ошибку и попробуйте снова']
            },
            'checked_at': datetime.now().isoformat()
        }

# Сохраняем обратную совместимость
class GostChecker(EnhancedGostChecker):
    """Совместимый класс для существующего кода"""
    async def check_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Совместимый метод для существующего API"""
        result = await self.check_document_with_pages(file_path, filename)
        
        # Конвертируем в старый формат
        errors = []
        warnings = []
        
        for page_num, page_errors in result['page_errors'].items():
            for error in page_errors:
                error_text = f"Страница {page_num}: {error['description']}"
                if error['severity'] == 'critical':
                    errors.append(error_text)
                else:
                    warnings.append(error_text)
        
        return {
            'is_compliant': result['is_compliant'],
            'score': result['score'],
            'errors': errors,
            'warnings': warnings,
            'details': {
                'structure': result['structure'],
                'content': result['content'],
                'page_errors': result['page_errors']
            },
            'checked_at': result['checked_at'],
            'summary': result['summary']
        }