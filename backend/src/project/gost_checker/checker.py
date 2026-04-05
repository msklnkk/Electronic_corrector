# backend/src/project/gost_checker/checker.py
from typing import Dict, List, Optional
import json
from datetime import datetime
from .models import DocumentCheckReport, CheckResult, RuleSeverity
from .parser import extract_document_data
from .rule_checker import GOSTRuleChecker, ValidationResult

class GOSTDocumentChecker:
    def __init__(self, rules_file: str = None):
        # Инициализирует проверщик документов
        try:
            self.rule_checker = GOSTRuleChecker(rules_file)
            print(f"Проверщик ГОСТ инициализирован. Загружено правил: {len(self.rule_checker.get_all_rules())}")
        except Exception as e:
            print(f"Ошибка инициализации проверщика: {e}")
            raise

    async def check_document(
            self,
            file_path: Optional[str] = None,
            file_content: Optional[bytes] = None,
            filename: Optional[str] = None,
            document_id: Optional[str] = None,
            original_filename: Optional[str] = None
    ) -> DocumentCheckReport:
        # Основной метод проверки документа.
        #
        # Поддерживает два режима:
        # - file_path + original_filename (для текущего FastAPI)
        # - file_content + filename (для gRPC)
        print(f"Начинаю проверку документа {document_id or 'без ID'}...")

        # Выбор способа получения данных документа
        if file_content is not None:
            if filename is None and original_filename is None:
                raise ValueError("При передаче file_content обязательно укажите filename или original_filename")
            doc_filename = original_filename or filename
            document_data = await extract_document_data(
                file_content=file_content,
                filename=doc_filename
            )
        elif file_path is not None:
            document_data = await extract_document_data(file_path=file_path)
        else:
            raise ValueError("Должен быть передан либо file_path, либо file_content + filename")

        all_results: List[CheckResult] = []

        try:
            # Проверяем все правила
            validation_results: List[ValidationResult] = self.rule_checker.check_all_rules(document_data)

            # Конвертируем ValidationResult в CheckResult
            for result in validation_results:
                check_result = CheckResult(
                    rule_id=result.rule_id,
                    section=result.rule_title.split('-')[0] if '-' in result.rule_title else result.rule_title,
                    title=result.rule_title,
                    severity=RuleSeverity(result.severity.value),
                    is_passed=result.is_passed,
                    message=result.message,
                    expected_value=result.expected,
                    actual_value=result.actual,
                    details={"suggestion": result.suggestion} if result.suggestion else None,
                    suggestion=result.suggestion
                )
                all_results.append(check_result)

        except Exception as e:
            print(f"Ошибка при проверке документа: {e}")
            # Создаем результат с системной ошибкой
            error_result = CheckResult(
                rule_id="system_error",
                section="system",
                title="Ошибка проверки",
                severity=RuleSeverity.CRITICAL,
                is_passed=False,
                message=f"Системная ошибка при проверке: {str(e)}",
                expected_value=None,
                actual_value=None,
                details={"error": str(e)},
                suggestion="Обратитесь к администратору системы"
            )
            all_results.append(error_result)

        # Подсчитываем статистику
        total = len(all_results)
        passed = sum(1 for r in all_results if r.is_passed)
        failed = total - passed

        failed_results = [r for r in all_results if not r.is_passed]
        critical_issues = sum(1 for r in failed_results if r.severity == RuleSeverity.CRITICAL)
        warning_issues = sum(1 for r in failed_results if r.severity == RuleSeverity.WARNING)

        print(f"Проверка завершена. Всего проверок: {total}, пройдено: {passed}, не пройдено: {failed}")

        # Создаем финальный отчет
        report = DocumentCheckReport(
            document_id=document_id or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            filename=original_filename or filename,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            critical_issues=critical_issues,
            warning_issues=warning_issues,
            results=all_results,
            timestamp=datetime.now().isoformat()
        )

        return report

    def get_available_rules(self) -> List[Dict]:
        # Возвращает список доступных правил
        return self.rule_checker.export_rules_for_frontend()
    
    def generate_json_report(self, report: DocumentCheckReport) -> Dict:
        # Генерирует JSON отчет
        return report.to_dict()
    
    def generate_summary_report(self, report: DocumentCheckReport) -> Dict:
        # Генерирует краткий отчет
        return {
            'document_id': report.document_id,
            'timestamp': report.timestamp,
            'total_checks': report.total_checks,
            'passed_checks': report.passed_checks,
            'failed_checks': report.failed_checks,
            'critical_issues': report.critical_issues,
            'warning_issues': report.warning_issues,
            'success_rate': round((report.passed_checks / report.total_checks * 100), 2) if report.total_checks > 0 else 0,
            'has_critical_issues': report.critical_issues > 0
        }
    
    def check_specific_section(self, document_data: Dict, section: str) -> List[CheckResult]:
        # Проверяет конкретный раздел документа
        all_rules = self.rule_checker.get_all_rules()
        section_rules = [rule for rule in all_rules.values() if rule['section'] == section]
        
        results = []
        for rule in section_rules:
            # Применяем правило к данным документа
            result = self._apply_single_rule(rule, document_data)
            if result:
                results.append(result)
        
        return results
    
    def _apply_single_rule(self, rule: Dict, document_data: Dict) -> Optional[CheckResult]:
        # Применяет одно правило к данным документа
        field = rule.get('field')
        if not field:
            return None
        
        # Получаем значение из документа
        actual_value = document_data.get(field)
        expected_value = rule.get('expected_value')
        check_type = rule.get('check_type')
        
        # Здесь должна быть логика проверки в зависимости от check_type
        # Пока возвращаем заглушку
        is_passed = False
        message = f"Проверка поля '{field}' не реализована для типа '{check_type}'"
        
        return CheckResult(
            rule_id=rule['id'],
            section=rule['section'],
            title=rule['title'],
            severity=RuleSeverity(rule['severity']),
            is_passed=is_passed,
            message=message,
            expected_value=expected_value,
            actual_value=actual_value
        )
    
    def get_rules_summary(self) -> Dict:
        # Возвращает статистику по правилам
        return self.rule_checker.get_rules_summary()
    
    def save_report_to_json(self, report: DocumentCheckReport, filepath: str):
        # Сохраняет отчет в JSON файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.generate_json_report(report), f, ensure_ascii=False, indent=2)
    
    def load_report_from_json(self, filepath: str) -> DocumentCheckReport:
        # Загружает отчет из JSON файла
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Конвертируем обратно в объекты
        results = []
        for result_data in data['results']:
            result = CheckResult(
                rule_id=result_data['rule_id'],
                section=result_data['section'],
                title=result_data['title'],
                severity=RuleSeverity(result_data['severity']),
                is_passed=result_data['is_passed'],
                message=result_data['message'],
                expected_value=result_data['expected_value'],
                actual_value=result_data['actual_value'],
                details=result_data.get('details'),
                suggestion=result_data.get('suggestion')
            )
            results.append(result)
        
        return DocumentCheckReport(
            document_id=data['document_id'],
            total_checks=data['total_checks'],
            passed_checks=data['passed_checks'],
            failed_checks=data['failed_checks'],
            critical_issues=data['critical_issues'],
            warning_issues=data['warning_issues'],
            results=results,
            timestamp=data['timestamp']
        )