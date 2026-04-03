# backend/grpc_checker/main.py
import asyncio
import sys
from pathlib import Path

BASE_DIR = Path("/app")                     # корень контейнера
GRPC_DIR = BASE_DIR / "grpc_checker"

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(GRPC_DIR))           # чтобы видеть services

print(f"DEBUG: PYTHONPATH = {sys.path}")
print(f"DEBUG: Current working dir = {Path.cwd()}")
print(f"DEBUG: Trying to import from {GRPC_DIR / 'services'}")

from services.gost_checker_servicer import serve_grpc


if __name__ == "__main__":
    print("Запуск gRPC Checker Service...")
    asyncio.run(serve_grpc())