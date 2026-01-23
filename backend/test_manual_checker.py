import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.project.gost_checker.checker import GOSTDocumentChecker

def main():
    print("тестирование ручной проверки на базе")
    print("=" * 60)
    
    try:
        checker = GOSTDocumentChecker()
        
        rules = checker.get_available_rules()
        print(f" Загружено {len(rules)} правил")
        
        # Пример данных документа для проверки
        document_data = {
            "required_elements": [
                "Титульный лист",
                "Содержание",
                "Введение", 
                "Основная часть",
                "Заключение",
                "Список литературы"  # Ошибка: должно быть "список использованных источников"
            ],
            "font_settings": {
                "font_family": "Arial",  # Ошибка: должно быть Times New Roman
                "font_size": 12,         # Ошибка: должно быть 14
                "line_spacing": 1.5
            },
            "page_margins": {
                "left": 25,
                "right": 15,
                "top": 20,
                "bottom": 20
            },
            "paragraph_indent": 1.25,
            "introduction_text": "В данной работе рассматривается проблема автоматизации проверки документов. Цель работы - разработать систему проверки соответствия ГОСТам."
        }
        
        # Проверяем документ
        print("\n Проверка документа:")
        print("-" * 40)
        
        report = checker.check_document(document_data, "test_document_001")
        
        # Выводим результаты
        print(f"Всего проверок: {report.total_checks}")
        print(f"Пройдено: {report.passed_checks}")
        print(f"Не пройдено: {report.failed_checks}")
        print(f"Критические ошибки: {report.critical_issues}")
        print(f"Предупреждения: {report.warning_issues}")
        
        print("\nРезультаты:")
        print("-" * 40)
        
        for result in report.results:
            if not result.is_passed:
                status = "КРИТИЧЕСКАЯ" if result.severity == "critical" else "ПРЕДУПРЕЖДЕНИЕ"
                print(f"\n{status} - {result.title}")
                print(f"   Раздел: {result.section}")
                print(f"   Сообщение: {result.message}")
                if result.suggestion:
                    print(f"   Предложение: {result.suggestion}")
        
        json_report = checker.generate_json_report(report)
        with open("document_check_report.json", "w", encoding="utf-8") as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        print(f"\nОтчет сохранен в document_check_report.json")
        
        summary = checker.generate_summary_report(report)
        print("\nКраткий отчет:")
        print(f"  Успешность: {summary['success_rate']}%")
        print(f"  Критические ошибки: {'Есть' if summary['has_critical_issues'] else 'Нет'}")
        print(f"  Время проверки: {summary['timestamp']}")
        
        print("\n Правила для API:")
        print("-" * 40)
        
        rules_export = checker.get_available_rules()
        with open("gost_rules_api.json", "w", encoding="utf-8") as f:
            json.dump(rules_export, f, ensure_ascii=False, indent=2)
        
        print(f"Экспортировано {len(rules_export)} правил в gost_rules_api.json")
        
        # Статистика по правилам
        print("\nСтатистика по правилам:")
        print("-" * 40)
        
        rules_summary = checker.get_rules_summary()
        print(f"Всего правил: {rules_summary['total_rules']}")
        print(f"Структурные правила: {rules_summary['structure_rules']}")
        print(f"Правила форматирования: {rules_summary['formatting_rules']}")
        print(f"Критические правила: {rules_summary['critical_rules']}")
        print(f"Предупреждения: {rules_summary['warning_rules']}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()