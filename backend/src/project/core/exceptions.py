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
    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Пользователь с id {id} не найден"
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
