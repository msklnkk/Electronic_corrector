# backend/src/main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from project.api.auth_routes import auth_routes
from project.api.user_routes import user_routes
from project.api.document_routes import document_routes
from project.api.standard_routes import standard_routes
from project.api.check_routes import check_routes
# from project.api.report_routes import report_routes
# from project.api.review_routes import review_routes
from project.api.status_routes import status_routes
from project.api.mistake_type_routes import mistake_type_routes
from project.api.mistake_routes import mistake_routes
from project.api.gost_check_routes import router as gost_check_router
from project.api.rule_extract_routes import router as rule_extract_router
from project.api.semantic_check_routes import router as semantic_check_router
from project.core.config import settings

from project.grpc.client import GostCheckerClient
from project.infrastructure.kafka.config import get_kafka_bootstrap_servers
from project.infrastructure.kafka.producer import KafkaProducerService

logger = logging.getLogger(__name__)

grpc_client: Optional[GostCheckerClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global grpc_client

    logger.info("Запуск FastAPI приложения...")

    try:
        grpc_client = GostCheckerClient(target="grpc_checker:50051")
        await grpc_client.connect()
        logger.info("gRPC клиент успешно подключен к grpc_checker:50051")
    except Exception as e:
        logger.error(f"Не удалось подключиться к gRPC сервису: {e}")
        grpc_client = None

    try:
        kafka_producer = KafkaProducerService(
            bootstrap_servers=get_kafka_bootstrap_servers()
        )
        await kafka_producer.start()
        app.state.kafka_producer = kafka_producer
        logger.info("Kafka producer успешно запущен")
    except Exception as e:
        logger.error(f"Не удалось запустить Kafka producer: {e}")
        app.state.kafka_producer = None

    yield

    logger.info("Завершение FastAPI приложения...")

    if grpc_client:
        await grpc_client.close()
        logger.info("gRPC клиент закрыт")

    kafka_producer = getattr(app.state, "kafka_producer", None)
    if kafka_producer:
        await kafka_producer.stop()
        logger.info("Kafka producer закрыт")


def create_app() -> FastAPI:
    app_options = {}

    if settings.ENV.lower() == "prod":
        app_options = {
            "docs_url": None,
            "redoc_url": None,
        }

    if settings.LOG_LEVEL in ["DEBUG", "INFO"]:
        app_options["debug"] = True

    app = FastAPI(
        root_path=settings.ROOT_PATH,
        lifespan=lifespan,
        **app_options
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_routes, tags=["Auth"])
    app.include_router(user_routes, tags=["User"])
    app.include_router(document_routes, tags=["Documents"])
    app.include_router(standard_routes, tags=["Standards"])
    app.include_router(check_routes, tags=["Check"])
    # app.include_router(report_routes, tags=["Reports"])
    # app.include_router(review_routes, tags=["Review"])
    app.include_router(status_routes, tags=["Status"])
    app.include_router(mistake_type_routes, tags=["Mistake Type"])
    app.include_router(mistake_routes, tags=["Mistake"])
    app.include_router(gost_check_router, tags=["GOST Check"])
    app.include_router(rule_extract_router, tags=["Rules"])
    app.include_router(semantic_check_router, tags=["Semantic Check"])

    return app


app = create_app()


async def run() -> None:
    config = uvicorn.Config(
        app="main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config=config)
    await server.serve()


if __name__ == "__main__":
    logger.debug(f"Postgres URL: {settings.postgres_url}")
    asyncio.run(run())