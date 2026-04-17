FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION=1.8.3
ENV PATH="/opt/poetry/bin:$PATH"
ENV PYTHONPATH=/app/src:/app

RUN echo "deb http://mirror.yandex.ru/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    echo 'Acquire::Retries "10";' > /etc/apt/apt.conf.d/99retries && \
    echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/99retries

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        unzip \
        libsm6 \
        libxext6 \
        ffmpeg \
        libfontconfig1 \
        libxrender1 \
        libgl1-mesa-dri \
        libglx-mesa0 \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py && \
    python3 install-poetry.py --version ${POETRY_VERSION} && \
    rm install-poetry.py

WORKDIR /app

COPY pyproject.toml /app/
COPY poetry.lock /app/
COPY alembic.ini /app/
COPY migration /app/migration

RUN poetry config virtualenvs.create false && \
    poetry config installer.parallel false && \
    poetry install --with ml --no-root --no-interaction --no-ansi

RUN pip install aiokafka==0.10.0

COPY ./src /app/src
COPY ./grpc_checker /app/grpc_checker

ARG CATEGORY_MODEL_PUBLIC_KEY="https://disk.yandex.ru/d/2MRs7GgdwYGgDw"
ARG RULE_MODEL_PUBLIC_KEY="https://disk.yandex.ru/d/RB9OWft642kxyg"

RUN mkdir -p /app/models && \
    curl -s "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=${CATEGORY_MODEL_PUBLIC_KEY}" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['href'])" \
    | xargs -I {} curl -L "{}" -o /tmp/category_classifier.zip && \
    unzip /tmp/category_classifier.zip -d /app/models && \
    rm /tmp/category_classifier.zip && \
    curl -s "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=${RULE_MODEL_PUBLIC_KEY}" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['href'])" \
    | xargs -I {} curl -L "{}" -o /tmp/rule_classifier.zip && \
    unzip /tmp/rule_classifier.zip -d /app/models && \
    rm /tmp/rule_classifier.zip

RUN chmod +x /app/src/start.sh

EXPOSE 8000

CMD ["/app/src/start.sh"]