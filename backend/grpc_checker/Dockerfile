# backend/grpc_checker/Dockerfile

FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive

# Используем тот же зеркальный репозиторий Yandex, что и в основном Dockerfile
RUN echo "deb http://mirror.yandex.ru/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    echo 'Acquire::Retries "10";' > /etc/apt/apt.conf.d/99retries && \
    echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/99retries

# Устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq-dev \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# === УСТАНОВКА POETRY ===
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION=1.8.3

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py && \
    python3 install-poetry.py --version $POETRY_VERSION && \
    rm install-poetry.py

ENV PATH="/opt/poetry/bin:$PATH"

WORKDIR /app

# Копируем файлы для установки зависимостей
COPY pyproject.toml poetry.lock* ./

# Копируем папку grpc_checker
COPY grpc_checker/ ./grpc_checker/

# Копируем правила
COPY grpc_checker/rules/manual_rules.json ./rules/manual_rules.json

# Устанавливаем зависимости (используем общий pyproject.toml)
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Копируем основной код проекта (чтобы можно было импортировать project.gost_checker)
COPY src/ /app/src/

# Делаем start.sh исполняемым
RUN chmod +x /app/src/start.sh || true

# Настройка окружения
ENV PYTHONPATH=/app/grpc_checker:/app/src

# Порт gRPC
EXPOSE 50051

# Запуск gRPC сервера
CMD ["python", "-m", "grpc_checker.main"]