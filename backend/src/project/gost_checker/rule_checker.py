import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

class CheckType(Enum):
    EQUALS = "equals"
    CONTAINS = "contains"
    LIST_PRESENCE = "list_presence"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    RANGE = "range"
    OBJECT_CONTAINS = "object_contains"
    OBJECT_EQUALS = "object_equals"

class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    rule_id: str
    rule_title: str
    is_passed: bool
    message: str
    severity: Severity
    expected: Any
    actual: Any
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Конвертирует результат в словарь"""
        result = asdict(self)
        result['severity'] = result['severity'].value
        return result

class GOSTRuleChecker:
    def __init__(self, rules_file: str = None):
        # Если путь не передан, ищем файл рядом с rule_checker.py
        if rules_file is None:
            rules_file = Path(__file__).parent / "manual_rules.json"

        # Проверка существования файла
        if not Path(rules_file).exists():
            raise FileNotFoundError(
                f"Файл правил не найден. Ожидался путь: {rules_file}"
            )

        print(f"Загружаю правила из: {rules_file}")

        with open(rules_file, 'r', encoding='utf-8') as f:
            self.rules_data = json.load(f)

        self.rules = {}
        self._load_rules()
    def _load_rules(self):
        """Загружает все правила из файла"""
        print("Загружаю правила...")
        
        # Загружаем структурные правила
        structure_rules = self.rules_data.get('rules', {}).get('structure', {})
        for rule_id, rule in structure_rules.items():
            self.rules[rule_id] = rule
            print(f"  Загружено структурное правило: {rule_id}")
        
        # Загружаем правила форматирования
        formatting_rules = self.rules_data.get('rules', {}).get('formatting', {})
        for rule_id, rule in formatting_rules.items():
            self.rules[rule_id] = rule
            print(f"  Загружено правило форматирования: {rule_id}")
        
        print(f"Всего загружено правил: {len(self.rules)}")
    
    def check_document_structure(self, document_elements: List[str]) -> List[ValidationResult]:
        """Проверяет структуру документа"""
        results = []
        
        # Проверка обязательных элементов (5.1)
        rule = self.rules.get('5.1_required_elements')
        if rule:
            print(f"Проверяю правило: {rule['title']}")
            result = self._check_list_presence(
                rule_id='5.1_required_elements',
                rule_title=rule['title'],
                expected_list=rule['expected_value'],
                actual_list=document_elements,
                severity=rule['severity']
            )
            results.append(result)
        
        return results
    
    def check_formatting(self, document_format: Dict) -> List[ValidationResult]:
        """Проверяет форматирование документа"""
        results = []
        
        # Проверка шрифта (6.1.1_font)
        font_rule = self.rules.get('6.1.1_font')
        if font_rule and 'font_settings' in document_format:
            print(f"Проверяю правило: {font_rule['title']}")
            result = self._check_object_equals(
                rule_id='6.1.1_font',
                rule_title=font_rule['title'],
                expected=font_rule['expected_value'],
                actual=document_format['font_settings'],
                severity=font_rule['severity']
            )
            results.append(result)
        elif font_rule:
            # Если правила нет в документе, создаем ошибку
            result = ValidationResult(
                rule_id='6.1.1_font',
                rule_title=font_rule['title'],
                is_passed=False,
                message="В документе отсутствуют настройки шрифта",
                severity=Severity(font_rule['severity']),
                expected=font_rule['expected_value'],
                actual=None,
                suggestion="Добавьте настройки шрифта в документ"
            )
            results.append(result)
        
        # Проверка полей (6.1.1_margins)
        margins_rule = self.rules.get('6.1.1_margins')
        if margins_rule and 'page_margins' in document_format:
            print(f"Проверяю правило: {margins_rule['title']}")
            result = self._check_object_equals(
                rule_id='6.1.1_margins',
                rule_title=margins_rule['title'],
                expected=margins_rule['expected_value'],
                actual=document_format['page_margins'],
                severity=margins_rule['severity']
            )
            results.append(result)
        elif margins_rule:
            result = ValidationResult(
                rule_id='6.1.1_margins',
                rule_title=margins_rule['title'],
                is_passed=False,
                message="В документе отсутствуют настройки полей",
                severity=Severity(margins_rule['severity']),
                expected=margins_rule['expected_value'],
                actual=None,
                suggestion="Добавьте настройки полей страницы в документ"
            )
            results.append(result)
        
        # Проверка абзацного отступа (6.1.2_paragraph)
        indent_rule = self.rules.get('6.1.2_paragraph')
        if indent_rule and 'paragraph_indent' in document_format:
            print(f"Проверяю правило: {indent_rule['title']}")
            result = self._check_equals(
                rule_id='6.1.2_paragraph',
                rule_title=indent_rule['title'],
                expected=indent_rule['expected_value'],
                actual=document_format['paragraph_indent'],
                severity=indent_rule['severity']
            )
            results.append(result)
        elif indent_rule:
            result = ValidationResult(
                rule_id='6.1.2_paragraph',
                rule_title=indent_rule['title'],
                is_passed=False,
                message="В документе отсутствует настройка абзацного отступа",
                severity=Severity(indent_rule['severity']),
                expected=indent_rule['expected_value'],
                actual=None,
                suggestion="Установите абзацный отступ равным 1.25 см"
            )
            results.append(result)
        
        return results
    
    def _check_equals(self, rule_id: str, rule_title: str, expected: Any, 
                     actual: Any, severity: str) -> ValidationResult:
        """Проверка на равенство"""
        is_passed = expected == actual
        
        if is_passed:
            message = f"Соответствует требованию: {expected}"
        else:
            message = f"Не соответствует: ожидалось {expected}, получено {actual}"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=expected,
            actual=actual
        )
    
    def _check_list_presence(self, rule_id: str, rule_title: str, 
                           expected_list: List[str], actual_list: List[str],
                           severity: str) -> ValidationResult:
        """Проверка наличия элементов списка"""
        missing_elements = []
        
        for expected in expected_list:
            found = False
            for actual in actual_list:
                if expected.lower() in actual.lower():
                    found = True
                    break
            if not found:
                missing_elements.append(expected)
        
        is_passed = len(missing_elements) == 0
        
        if is_passed:
            message = "Все обязательные элементы присутствуют"
        else:
            message = f"Отсутствуют элементы: {', '.join(missing_elements)}"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=expected_list,
            actual=actual_list,
            suggestion=f"Добавьте недостающие элементы: {', '.join(missing_elements)}" if missing_elements else None
        )
    
    def _check_object_equals(self, rule_id: str, rule_title: str, 
                           expected: Dict, actual: Dict, severity: str) -> ValidationResult:
        """Проверка объектов на равенство"""
        mismatches = []
        
        for key, expected_value in expected.items():
            if key in actual:
                if expected_value != actual[key]:
                    mismatches.append(f"{key}: ожидалось {expected_value}, получено {actual[key]}")
            else:
                mismatches.append(f"{key}: отсутствует в документе")
        
        is_passed = len(mismatches) == 0
        
        if is_passed:
            message = "Все параметры соответствуют требованиям"
        else:
            message = f"Несоответствия: {'; '.join(mismatches)}"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=expected,
            actual=actual
        )
    
    def _check_object_contains(self, rule_id: str, rule_title: str,
                             expected: Dict, actual: Dict, severity: str) -> ValidationResult:
        """Проверка, что объект содержит ожидаемые свойства"""
        missing_props = []
        
        for key, expected_value in expected.items():
            if key not in actual:
                missing_props.append(key)
            elif expected_value != actual[key]:
                missing_props.append(f"{key} (неверное значение)")
        
        is_passed = len(missing_props) == 0
        
        if is_passed:
            message = "Содержит все требуемые свойства"
        else:
            message = f"Отсутствуют или неверны свойства: {', '.join(missing_props)}"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=expected,
            actual=actual
        )
    
    def _check_range(self, rule_id: str, rule_title: str, 
                    min_value: float, max_value: float, actual: float, severity: str) -> ValidationResult:
        """Проверка значения в диапазоне"""
        is_passed = min_value <= actual <= max_value
        
        if is_passed:
            message = f"Значение {actual} находится в допустимом диапазоне [{min_value}, {max_value}]"
        else:
            if actual < min_value:
                message = f"Значение {actual} меньше минимально допустимого {min_value}"
            else:
                message = f"Значение {actual} больше максимально допустимого {max_value}"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=f"Диапазон [{min_value}, {max_value}]",
            actual=actual
        )
    
    def _check_min_value(self, rule_id: str, rule_title: str, 
                        min_value: float, actual: float, severity: str) -> ValidationResult:
        """Проверка минимального значения"""
        is_passed = actual >= min_value
        
        if is_passed:
            message = f"Значение {actual} не меньше минимально допустимого {min_value}"
        else:
            message = f"Значение {actual} меньше минимально допустимого {min_value}"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=f"Минимум {min_value}",
            actual=actual
        )
    
    def _check_max_value(self, rule_id: str, rule_title: str, 
                        max_value: float, actual: float, severity: str) -> ValidationResult:
        """Проверка максимального значения"""
        is_passed = actual <= max_value
        
        if is_passed:
            message = f"Значение {actual} не больше максимально допустимого {max_value}"
        else:
            message = f"Значение {actual} больше максимально допустимого {max_value}"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=f"Максимум {max_value}",
            actual=actual
        )
    
    def _check_contains(self, rule_id: str, rule_title: str, 
                       expected: str, actual: str, severity: str) -> ValidationResult:
        """Проверка наличия подстроки"""
        is_passed = expected.lower() in actual.lower()
        
        if is_passed:
            message = f"Текст содержит требуемое: '{expected}'"
        else:
            message = f"Текст не содержит требуемое: '{expected}'"
        
        return ValidationResult(
            rule_id=rule_id,
            rule_title=rule_title,
            is_passed=is_passed,
            message=message,
            severity=Severity(severity),
            expected=expected,
            actual=actual[:100] + "..." if len(actual) > 100 else actual
        )
    
    def check_introduction(self, introduction_text: str) -> ValidationResult:
        """Проверка содержания введения"""
        rule = self.rules.get('5.6_introduction')
        if not rule:
            return None
        
        content_lower = introduction_text.lower()
        expected_items = rule['expected_value']
        missing_items = []
        
        for item in expected_items:
            if item not in content_lower:
                # Проверяем синонимы
                synonyms = {
                    'состояние разработок по теме': ['состояние исследований', 'обзор литературы', 'анализ существующих'],
                    'обоснование актуальности': ['актуальность темы', 'актуальность работы'],
                    'обоснование новизны': ['новизна исследования', 'новизна работы'],
                    'связь с другими работами': ['связь с исследованиями', 'взаимосвязь с работами'],
                    'цель работы': ['цель исследования', 'цель данной работы'],
                    'задачи работы': ['задачи исследования', 'задачи данной работы']
                }
                
                found = False
                if item in synonyms:
                    for synonym in synonyms[item]:
                        if synonym in content_lower:
                            found = True
                            break
                
                if not found:
                    missing_items.append(item)
        
        is_passed = len(missing_items) == 0
        
        if is_passed:
            message = "Введение содержит все обязательные элементы"
        else:
            message = f"В введении отсутствуют: {', '.join(missing_items)}"
        
        return ValidationResult(
            rule_id='5.6_introduction',
            rule_title=rule['title'],
            is_passed=is_passed,
            message=message,
            severity=Severity(rule['severity']),
            expected=expected_items,
            actual=introduction_text[:200] + "..." if len(introduction_text) > 200 else introduction_text,
            suggestion=f"Добавьте в введение: {', '.join(missing_items)}" if missing_items else None
        )
    
    def check_all_rules(self, document_data: Dict) -> List[ValidationResult]:
        """Проверяет документ по всем правилам"""
        results = []
        
        # Проверяем структуру
        if 'required_elements' in document_data:
            results.extend(self.check_document_structure(document_data['required_elements']))
        
        # Проверяем форматирование
        results.extend(self.check_formatting(document_data))
        
        # Проверяем введение
        if 'introduction_text' in document_data:
            intro_result = self.check_introduction(document_data['introduction_text'])
            if intro_result:
                results.append(intro_result)
        
        return results
    
    def get_all_rules(self) -> Dict:
        """Возвращает все правила"""
        return self.rules
    
    def get_rule_by_section(self, section: str) -> Dict:
        """Возвращает правила по номеру раздела"""
        matching_rules = {}
        for rule_id, rule in self.rules.items():
            if rule['section'] == section:
                matching_rules[rule_id] = rule
        
        return matching_rules
    
    def get_rule_by_id(self, rule_id: str) -> Dict:
        """Возвращает правило по ID"""
        return self.rules.get(rule_id)
    
    def export_rules_for_frontend(self) -> List[Dict]:
        """Экспортирует правила для фронтенда"""
        frontend_rules = []
        
        for rule_id, rule in self.rules.items():
            frontend_rule = {
                'id': rule_id,
                'section': rule['section'],
                'title': rule['title'],
                'description': rule.get('description', ''),
                'type': rule['rule_type'],
                'severity': rule['severity'],
                'check_type': rule['check_type'],
                'expected_value': rule['expected_value']
            }
            frontend_rules.append(frontend_rule)
        
        return frontend_rules
    
    def get_rules_summary(self) -> Dict:
        """Возвращает статистику по правилам"""
        total = len(self.rules)
        structure_count = sum(1 for rule in self.rules.values() if rule['rule_type'] == 'structure')
        formatting_count = sum(1 for rule in self.rules.values() if rule['rule_type'] == 'formatting')
        
        critical_count = sum(1 for rule in self.rules.values() if rule['severity'] == 'critical')
        warning_count = sum(1 for rule in self.rules.values() if rule['severity'] == 'warning')
        
        return {
            'total_rules': total,
            'structure_rules': structure_count,
            'formatting_rules': formatting_count,
            'critical_rules': critical_count,
            'warning_rules': warning_count,
            'rules_by_section': self._get_rules_by_section()
        }
    
    def _get_rules_by_section(self) -> Dict:
        """Группирует правила по разделам"""
        sections = {}
        for rule_id, rule in self.rules.items():
            section = rule['section']
            if section not in sections:
                sections[section] = []
            sections[section].append({
                'id': rule_id,
                'title': rule['title'],
                'type': rule['rule_type'],
                'severity': rule['severity']
            })
        
        return sections