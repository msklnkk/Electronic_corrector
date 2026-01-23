# src/project/gost_checker/__init__.py
"""
Модуль для проверки документов на соответствие ГОСТ

Основные компоненты:
- GOSTDocumentChecker: Основной класс для проверки документов
- CheckResult: Результат проверки одного правила
- DocumentCheckReport: Отчет о проверке документа
- RuleSeverity: Уровень серьезности нарушения
- RuleType: Тип правила
- PDFReportGenerator: Генератор PDF отчетов
- GOSTRule: Модель правила ГОСТ
- GOSTRuleChecker: Проверщик по правилам
"""

# Импортируем основные классы
from .checker import GOSTDocumentChecker
from .models import CheckResult, DocumentCheckReport, RuleSeverity, RuleType, GOSTRule
from .rule_checker import GOSTRuleChecker, ValidationResult

# Для обратной совместимости создаем алиасы
DocumentChecker = GOSTDocumentChecker
Violation = CheckResult
ViolationSeverity = RuleSeverity

# Экспортируем все необходимые классы
__all__ = [
    # Основные классы для проверки
    "GOSTDocumentChecker",
    "GOSTRuleChecker",
    "ValidationResult",
    
    # Модели данных
    "CheckResult",
    "DocumentCheckReport", 
    "GOSTRule",
    
    # Перечисления
    "RuleSeverity",
    "RuleType",
    
    # Алиасы для обратной совместимости
    "DocumentChecker",
    "Violation", 
    "ViolationSeverity",
]