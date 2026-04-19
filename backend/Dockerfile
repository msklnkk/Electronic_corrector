FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION=1.8.3
ENV PATH="/opt/poetry/bin:$PATH"
ENV PYTHONPATH=/app/src:/app
ENV POETRY_REQUESTS_TIMEOUT=600
ENV PIP_DEFAULT_TIMEOUT=600
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

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

RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu

RUN poetry config virtualenvs.create false && \
    poetry config installer.parallel false && \
    poetry install --with ml --no-root --no-interaction --no-ansi

RUN pip install --no-cache-dir aiokafka==0.10.0

COPY ./src /app/src
COPY ./grpc_checker /app/grpc_checker
COPY ./gost_rules_api.json /app/gost_rules_api.json

ARG CATEGORY_MODEL_PUBLIC_KEY="https://disk.yandex.ru/d/2MRs7GgdwYGgDw"
ARG RULE_MODEL_PUBLIC_KEY="https://disk.yandex.ru/d/RB9OWft642kxyg"

RUN mkdir -p /app/models

RUN CATEGORY_JSON=$(curl --retry 5 --retry-delay 5 --retry-all-errors -fsSL "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=${CATEGORY_MODEL_PUBLIC_KEY}") && \
    CATEGORY_HREF=$(python3 -c "import sys, json; print(json.loads(sys.argv[1])['href'])" "$CATEGORY_JSON") && \
    curl --retry 5 --retry-delay 5 --retry-all-errors -fL "$CATEGORY_HREF" -o /tmp/category_classifier.zip && \
    unzip /tmp/category_classifier.zip -d /app/models && \
    rm -f /tmp/category_classifier.zip

RUN RULE_JSON=$(curl --retry 5 --retry-delay 5 --retry-all-errors -fsSL "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=${RULE_MODEL_PUBLIC_KEY}") && \
    RULE_HREF=$(python3 -c "import sys, json; print(json.loads(sys.argv[1])['href'])" "$RULE_JSON") && \
    curl --retry 5 --retry-delay 5 --retry-all-errors -fL "$RULE_HREF" -o /tmp/rule_classifier.zip && \
    unzip /tmp/rule_classifier.zip -d /app/models && \
    rm -f /tmp/rule_classifier.zip

RUN chmod +x /app/src/start.sh

EXPOSE 8000

CMD ["/app/src/start.sh"]