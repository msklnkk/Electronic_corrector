from typing import Final
from fastapi import HTTPException, status


class DatabaseError(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Произошла ошибка в базе данных: {message}"
    def __init__(self, message: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(message=message)
        super().__init__(self.message)
class CredentialsException(HTTPException):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )



class UserNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Пользователь с id '{id}' не найден"
    message: str

    def __init__(self, _id: int | str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)


class UserAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Пользователь с почтой '{mail}' уже существует"

    def __init__(self, mail: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(mail=mail)
        super().__init__(self.message)



class UserNameAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Пользователь с логином '{login}' уже существует"

    def __init__(self, login: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(login=login)
        super().__init__(self.message)


class UserTelegramAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = (
        "Пользователь с Telegram username '{tg_username}' уже существует"
    )

    def __init__(self, tg_username: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(tg_username=tg_username)
        super().__init__(self.message)


class DocumentNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Документ с id '{id}' не найден"

    def __init__(self, _id: int | str):
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)


class StandardNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Стандарт с id '{id}' не найден"
    message: str

    def __init__(self, _id: int | str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)


class StandardAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Стандарт '{name}' версии '{version}' уже существует"
    message: str

    def __init__(self, name: str, version: str | None) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(
            name=name,
            version=version if version is not None else "—"
        )
        super().__init__(self.message)


class CheckNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Проверка с id '{id}' не найдена"
    message: str

    def __init__(self, _id: int | str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)


class CheckAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[
        str] = "Проверка для документа '{document_id}' и стандарта '{standart_id}' уже существует"

    def __init__(self, document_id: int, standart_id: int) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(document_id=document_id, standart_id=standart_id)
        super().__init__(self.message)


class ReportNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Отчет с id '{id}' не найден"
    message: str

    def __init__(self, _id: int | str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)

class ReportAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Отчет для проверки '{check_id}' уже существует (или нарушение целостности)"

    def __init__(self, check_id: int) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(check_id=check_id)
        super().__init__(self.message)


class ReviewNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Отзыв с id '{id}' не найден"
    message: str

    def __init__(self, _id: int | str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)

class ReviewAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Отзыв для пользователя '{user_id}' уже существует (или нарушение целостности)"

    def __init__(self, user_id: int) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(user_id=user_id)
        super().__init__(self.message)


class StatusNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Статус с id '{id}' не найден"
    message: str

    def __init__(self, _id: int | str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)


class StatusAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Статус с именем '{name}' уже существует"

    def __init__(self, name: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(name=name)
        super().__init__(self.message)



class MistakeTypeNotFound(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Тип ошибки с id '{id}' не найден"
    message: str

    def __init__(self, _id: int | str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(id=_id)
        super().__init__(self.message)


class MistakeTypeAlreadyExists(BaseException):
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Тип ошибки с именем '{name}' уже существует"

    def __init__(self, name: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(name=name)
        super().__init__(self.message)