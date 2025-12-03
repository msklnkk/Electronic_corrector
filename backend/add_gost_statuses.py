# add_gost_statuses.py
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.project.infrastructure.postgres.database import SessionLocal
from src.project.infrastructure.postgres.models import Status

def add_gost_statuses():
    db = SessionLocal()
    try:
        # Статусы которые нужно добавить
        required_statuses = ["Загружен", "Анализируется", "Проверен", "Отправлен на доработку", "Идеален"]
        
        print("Проверяем существующие статусы...")
        
        # Проверяем какие статусы уже есть
        existing_statuses = db.query(Status.status_name).all()
        existing_names = [status[0] for status in existing_statuses]
        
        print(f"Найдено существующих статусов: {existing_names}")
        
        # Добавляем отсутствующие статусы
        added_count = 0
        for status_name in required_statuses:
            if status_name not in existing_names:
                new_status = Status(status_name=status_name)
                db.add(new_status)
                print(f"✅ Добавлен статус: {status_name}")
                added_count += 1
            else:
                print(f"ℹ️  Статус уже существует: {status_name}")
        
        db.commit()
        print(f"✅ Готово! Добавлено {added_count} новых статусов из {len(required_statuses)} требуемых")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_gost_statuses()