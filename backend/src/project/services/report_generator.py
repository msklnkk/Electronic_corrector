import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

class ReportGenerator:
    def generate_report(self, check_result: dict, document: Documents, output_path: str):
        """Генерирует PDF отчет с ошибками постранично"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок
        story.append(Paragraph(f"Отчет проверки: {document.filename}", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Ошибки по страницам
        if check_result.get('errors_by_page'):
            for page_num, errors in check_result['errors_by_page'].items():
                story.append(Paragraph(f"Страница {page_num}:", styles['Heading2']))
                for error in errors:
                    story.append(Paragraph(f"• {error}", styles['Normal']))
                story.append(Spacer(1, 6))
        
        doc.build(story)
