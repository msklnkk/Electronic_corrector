from typing import Dict
import json

class PDFReportGenerator:
    """Упрощенный генератор отчетов для интеграции с существующей системой"""
    
    @staticmethod
    def generate_report_data(json_report: Dict) -> Dict:
        """Подготовка данных для отчета (вместо генерации PDF)"""
        summary = json_report.get('summary', {})
        violations = json_report.get('violations', [])
        
        report_data = {
            'title': 'Отчет о проверке документа на соответствие ГОСТ',
            'summary': summary,
            'violations': violations,
            'recommendations': PDFReportGenerator._generate_recommendations(violations),
            'timestamp': json_report.get('timestamp')
        }
        
        return report_data
    
    @staticmethod
    def _generate_recommendations(violations: list) -> list:
        """Генерация рекомендаций на основе найденных нарушений"""
        recommendations = []
        
        for violation in violations:
            if violation.get('suggestion'):
                recommendations.append({
                    'section': violation.get('section'),
                    'suggestion': violation.get('suggestion'),
                    'severity': violation.get('severity')
                })
        
        # Общие рекомендации
        general_recommendations = [
            "Проверьте шрифт документа - он должен быть Times New Roman",
            "Убедитесь, что размер шрифта составляет 14 пт",
            "Проверьте межстрочный интервал - он должен быть 1.5",
            "Убедитесь, что поля документа соответствуют требованиям ГОСТ"
        ]
        
        for rec in general_recommendations:
            recommendations.append({
                'section': 'Общие',
                'suggestion': rec,
                'severity': 'info'
            })
        
        return recommendations