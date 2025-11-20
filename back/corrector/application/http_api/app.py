from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from corrector.application.http_api import controllers


def create_app(
        version: str,
        is_debug: bool = False,
        swagger_on: bool = False,
        title: str = 'noname'
) -> FastAPI:
    """ Собирает основное приложение """
    app = FastAPI(
        title=title,
        debug=is_debug,
        version=version,
        docs_url='/docs' if swagger_on else None,
        redoc_url='/redoc' if swagger_on else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Разрешить запросы из этих источников
        allow_credentials=True,  # Разрешить отправку куки (при необходимости)
        allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
        allow_headers=["*"],  # Разрешить все заголовки
    )
    app.include_router(controllers.status_router)
    app.include_router(controllers.document_router)
    app.include_router(controllers.mistake_type_router)
    app.include_router(controllers.mistake_router)
    app.include_router(controllers.user_router)
    app.include_router(controllers.review_router)
    app.include_router(controllers.auth_router)
    return app
