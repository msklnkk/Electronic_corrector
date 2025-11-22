FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl libsm6 libxext6 ffmpeg libfontconfig1 libxrender1 \
        libgl1-mesa-dri libglx-mesa0 postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# === УСТАНОВКА POETRY ===
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION=1.8.3

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py && \
    python3 install-poetry.py --version $POETRY_VERSION && \
    rm install-poetry.py

ENV PATH="/opt/poetry/bin:$PATH"

WORKDIR /app

COPY pyproject.toml .
COPY alembic.ini .
COPY migration /app/migration

RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

COPY ./src /app/src
RUN chmod +x /app/src/start.sh

ENV PYTHONPATH=/app/src

EXPOSE 8000
CMD ["/app/src/start.sh"]
