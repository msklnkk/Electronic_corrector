FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION=1.8.3
ENV PATH="/opt/poetry/bin:$PATH"
ENV PYTHONPATH=/app/grpc_checker:/app/src
ENV POETRY_REQUESTS_TIMEOUT=600
ENV PIP_DEFAULT_TIMEOUT=600
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        unzip \
        libpq-dev \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py && \
    python3 install-poetry.py --version ${POETRY_VERSION} && \
    rm install-poetry.py

WORKDIR /app

COPY pyproject.toml /app/
COPY poetry.lock /app/

RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

RUN poetry config virtualenvs.create false && \
    poetry config installer.parallel false && \
    poetry install --with ml --no-root --no-interaction --no-ansi

COPY grpc_checker/ /app/grpc_checker/
COPY src/ /app/src/

RUN mkdir -p /app/rules && \
    cp /app/grpc_checker/rules/manual_rules.json /app/rules/manual_rules.json

RUN chmod +x /app/src/start.sh || true

EXPOSE 50051

CMD ["python", "-m", "grpc_checker.main"]