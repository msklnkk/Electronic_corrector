from corrector.application import http_api
from corrector.application.http_api import create_app


class Settings:
    http_api = http_api.Settings()

app = create_app(
    is_debug=Settings.http_api.APP_IS_DEBUG,
    version=Settings.http_api.APP_VERSION,
    swagger_on=Settings.http_api.APP_SWAGGER_ON,
    title=Settings.http_api.APP_TITLE
)
