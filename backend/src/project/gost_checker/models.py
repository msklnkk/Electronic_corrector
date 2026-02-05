from dataclasses import dataclass, asdict, field
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
    """Модель правила ГОСТ"""
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
    """Результат проверки"""
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
        result = asdict(self)
        result['severity'] = result['severity'].value
        return result

@dataclass
class DocumentCheckReport:
    """Отчет о проверке документа"""
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
        result = asdict(self)
        # Конвертируем все результаты
        result['results'] = [r.to_dict() for r in self.results]
        result['filename'] = self.filename
        return result
    
    def get_failed_results(self) -> List[CheckResult]:
        """Возвращает только неудачные проверки"""
        return [r for r in self.results if not r.is_passed]
    
    def get_critical_issues(self) -> List[CheckResult]:
        """Возвращает критические ошибки"""
        return [r for r in self.results if not r.is_passed and r.severity == RuleSeverity.CRITICAL]
    
    def get_warning_issues(self) -> List[CheckResult]:
        """Возвращает предупреждения"""
        return [r for r in self.results if not r.is_passed and r.severity == RuleSeverity.WARNING]