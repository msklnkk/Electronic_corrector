FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl libsm6 libxext6 ffmpeg libfontconfig1 libxrender1 \
        libgl1-mesa-dri libglx-mesa0 postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# === УСТАНОВКА POETRY ===
# Указываем вручную, куда устанавливать Poetry
ENV POETRY_HOME="/opt/poetry"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Добавляем Poetry в PATH
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Проверим, что всё работает
RUN poetry --version

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
