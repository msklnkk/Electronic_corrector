import os
import tempfile
from typing import Dict, Any

def save_uploaded_file(upload_file, destination_dir: str = None) -> str:
    """Сохранение загруженного файла во временную директорию"""
    if destination_dir is None:
        destination_dir = tempfile.gettempdir()
    
    file_path = os.path.join(destination_dir, upload_file.filename)
    
    with open(file_path, 'wb') as buffer:
        content = upload_file.file.read()
        buffer.write(content)
    
    return file_path

def cleanup_temp_file(file_path: str):
    """Удаление временного файла"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Ошибка при удалении файла {file_path}: {e}")

def map_document_type(document_type: str) -> str:
    """Маппинг типа документа"""
    type_map = {
        'курсовая': 'COURSE_WORK',
        'бакалаврская': 'BACHELOR_THESIS',
        'магистерская': 'MASTER_THESIS',
        'дипломная': 'SPECIALIST_THESIS',
        'course': 'COURSE_WORK',
        'bachelor': 'BACHELOR_THESIS',
        'master': 'MASTER_THESIS',
        'specialist': 'SPECIALIST_THESIS'
    }
    return type_map.get(document_type.lower(), 'COURSE_WORK')