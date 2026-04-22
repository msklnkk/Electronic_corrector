import base64
import sys
from pathlib import Path


def file_to_base64(filepath: str) -> str:
    path = Path(filepath)

    if not path.exists():
        print(f"Ошибка: файл '{filepath}' не найден")
        sys.exit(1)

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    print(f"Файл: {path.name}")
    print(f"Размер: {path.stat().st_size} байт")
    print(f"\nBase64:\n{encoded}")

    # Сохраняем в отдельный файл рядом с исходным
    output_path = path.with_suffix(".b64.txt")
    output_path.write_text(encoded, encoding="utf-8")
    print(f"\nСохранено в: {output_path}")

    return encoded


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python to_base64.py <путь_к_файлу>")
        print("Пример:        python to_base64.py my_document.docx")
        sys.exit(1)

    file_to_base64(sys.argv[1])
