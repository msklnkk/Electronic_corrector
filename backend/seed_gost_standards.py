"""
Заполняет таблицу standart записями государственных ГОСТ и выставляет rules_file.

Запуск из каталога backend (с установленным PYTHONPATH=src или из Docker-контейнера API):

    cd backend
    set PYTHONPATH=src
    python seed_gost_standards.py

"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sqlalchemy import select

from project.infrastructure.postgres.database import database
from project.infrastructure.postgres.models import Standart


SEED_STANDARDS: list[dict] = [
    {
        "name": "ГОСТ 7.32-2017. Отчёт о НИР",
        "version": "1.0",
        "description": "Структура и правила оформления отчёта о научно-исследовательской работе",
        "rules_file": "rules/manual_rules.json",
        "is_custom": False,
    },
    {
        "name": "ГОСТ 7.32-2017 (курсовая / ВКР)",
        "version": "1.0",
        "description": "Курсовая, проект, выпускная квалификационная работа",
        "rules_file": "rules/gost_coursework_rules.json",
        "is_custom": False,
    },
]


async def main() -> None:
    async with database.session() as session:
        for row in SEED_STANDARDS:
            existing = await session.scalar(select(Standart).where(Standart.name == row["name"]))
            if existing:
                print(f"Уже есть: {row['name']}")
                continue
            session.add(Standart(**row))
            print(f"Добавлено: {row['name']}")

        legacy = await session.scalar(
            select(Standart).where(Standart.name == "ГОСТ для курсовых работ")
        )
        if legacy and not legacy.rules_file:
            legacy.rules_file = "rules/manual_rules.json"
            print("Обновлен rules_file у «ГОСТ для курсовых работ»")


if __name__ == "__main__":
    asyncio.run(main())
