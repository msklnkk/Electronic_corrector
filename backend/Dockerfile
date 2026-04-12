FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive

RUN echo "deb http://mirror.yandex.ru/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    echo 'Acquire::Retries "10";' > /etc/apt/apt.conf.d/99retries && \
    echo 'Acquire::http::Timeout "60";' >> /etc/apt/apt.conf.d/99retries

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl libsm6 libxext6 ffmpeg libfontconfig1 libxrender1 \
        libgl1-mesa-dri libglx-mesa0 postgresql-client \
        tesseract-ocr-rus tesseract-ocr-eng tesseract-ocr poppler-utils \
        g++ build-essential && \
    rm -rf /var/lib/apt/lists/*


ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION=1.8.3
ENV PATH="/opt/poetry/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org -o install-poetry.py && \
    python3 install-poetry.py --version $POETRY_VERSION && \
    rm install-poetry.py

WORKDIR /app

COPY pyproject.toml ./
COPY alembic.ini ./
COPY migration /app/migration


RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

RUN pip install --no-cache-dir \
    torch==2.2.2 \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    protobuf==3.20.3 \
    sentencepiece==0.2.0 \
    tiktoken==0.6.0 \
    accelerate==0.30.1 \
    pdf2image==1.17.0 \
    pytesseract==0.3.13 \
    pillow==10.4.0 \
    scikit-learn==1.3.2 \
    numpy==1.24.3 \
    nltk==3.8.1

RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"

COPY ./src /app/src
RUN chmod +x /app/src/start.sh

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["/app/src/start.sh"]