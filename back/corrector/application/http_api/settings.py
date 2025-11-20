from pydantic import Extra
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_IS_DEBUG: bool = False
    APP_VERSION: str = '0.0.1'
    APP_SWAGGER_ON: bool = False
    APP_TITLE: str = 'noname'
    APP_LOGGING_LEVEL: str = 'INFO'

    # SECURITY 

    # openssl rand -hex 32
    APP_SECRET_KEY: str = 'e7cfd4c219d61a5613efb294034e29683cdf6f12a2d1b9cd315691f5355b99f7'
    # один день
    APP_TOKEN_EXPIRE_MINUTES: int = 1440
    
    @property
    def LOGGING_CONFIG(self):
        return {
            'loggers': {
                'gunicorn': {
                    'handlers': ['default'],
                    'level': self.APP_LOGGING_LEVEL,
                    'propagate': False
                },
                'uvicorn': {
                    'handlers': ['default'],
                    'level': self.APP_LOGGING_LEVEL,
                    'propagate': False
                },
            }
        }

    class Config:
        extra = Extra.ignore
        env_file = '.env'
        env_file_encoding = 'utf-8'
    
    