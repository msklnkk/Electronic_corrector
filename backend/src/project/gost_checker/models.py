# backend/src/project/gost_checker/models.py
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from enum import Enum

class RuleSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class RuleType(str, Enum):
    STRUCTURE = "structure"
    FORMATTING = "formatting"
    CONTENT = "content"
    CITATION = "citation"

@dataclass
class GOSTRule:
    # Модель правила ГОСТ
    id: str
    section: str
    title: str
    content: str
    rule_type: RuleType
    field: str
    expected_value: Any
    check_type: str
    severity: RuleSeverity
    description: Optional[str] = None
    unit: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class CheckResult:
    # Результат проверки
    rule_id: str
    section: str
    title: str
    severity: RuleSeverity
    is_passed: bool
    message: str
    expected_value: Any
    actual_value: Any
    details: Optional[Dict] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'rule_id': self.rule_id,
            'section': self.section,
            'title': self.title,
            'severity': self.severity.value if isinstance(self.severity, RuleSeverity) else self.severity,
            'is_passed': self.is_passed,
            'message': self.message,
            # Безопасная конвертация любых типов в строку
            'expected_value': self._safe_serialize(self.expected_value),
            'actual_value': self._safe_serialize(self.actual_value),
            'details': self._safe_serialize(self.details),
            'suggestion': self.suggestion
        }

    @staticmethod
    def _safe_serialize(value: Any) -> Any:
        # Безопасная конвертация любых типов для JSON
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return [CheckResult._safe_serialize(v) for v in value]
        if isinstance(value, dict):
            return {k: CheckResult._safe_serialize(v) for k, v in value.items()}
        if isinstance(value, Enum):
            return value.value
        # Для всех остальных типов конвертируем в строку
        return str(value)

@dataclass
class DocumentCheckReport:
    # Отчет о проверке документа
    document_id: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_issues: int
    warning_issues: int
    results: List[CheckResult]
    timestamp: str
    filename: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'document_id': self.document_id,
            'total_checks': self.total_checks,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'critical_issues': self.critical_issues,
            'warning_issues': self.warning_issues,
            'timestamp': self.timestamp,
            'filename': self.filename,
            'results': [r.to_dict() for r in self.results]
        }
    
    def get_failed_results(self) -> List[CheckResult]:
        # Возвращает только неудачные проверки
        return [r for r in self.results if not r.is_passed]
    
    def get_critical_issues(self) -> List[CheckResult]:
        # Возвращает критические ошибки
        return [r for r in self.results if not r.is_passed and r.severity == RuleSeverity.CRITICAL]
    
    def get_warning_issues(self) -> List[CheckResult]:
        # Возвращает предупреждения
        return [r for r in self.results if not r.is_passed and r.severity == RuleSeverity.WARNING]