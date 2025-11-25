from typing import Annotated
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status

from project.schemas.auth import TokenData
from project.core.config import settings
from project.core.exceptions import CredentialsException
from project.resource.auth import oauth2_scheme


from project.infrastructure.postgres.database import PostgresDatabase
from project.schemas.user import UserSchema

from project.infrastructure.postgres.repository.user_repo import UserRepository
from project.infrastructure.postgres.repository.document_repository import DocumentRepository
from project.infrastructure.postgres.repository.standard_repo import StandardRepository
from project.infrastructure.postgres.repository.check_repo import CheckRepository
from project.infrastructure.postgres.repository.report_repo import ReportRepository
from project.infrastructure.postgres.repository.review_repo import ReviewRepository
from project.infrastructure.postgres.repository.status_repo import StatusRepository
from project.infrastructure.postgres.repository.mistake_type_repo import MistakeTypeRepository
from project.infrastructure.postgres.repository.mistake_repo import MistakeRepository


database = PostgresDatabase()
user_repo = UserRepository()
document_repo = DocumentRepository()
standard_repo = StandardRepository()
check_repo = CheckRepository()
report_repo = ReportRepository()
review_repo = ReviewRepository()
status_repo = StatusRepository()
mistake_type_repo = MistakeTypeRepository()
mistake_repo = MistakeRepository()


AUTH_EXCEPTION_MESSAGE = "Невозможно проверить данные для авторизации"
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    try:
        payload = jwt.decode(
            token=token,
            key=settings.SECRET_AUTH_KEY.get_secret_value(),
            algorithms=[settings.AUTH_ALGORITHM],
        )
        email: str = payload.get("sub")
        if email is None:
            raise CredentialsException(detail=AUTH_EXCEPTION_MESSAGE)
        token_data = TokenData(username=email)
    except JWTError:
        raise CredentialsException(detail=AUTH_EXCEPTION_MESSAGE)
    async with database.session() as session:
        user = await user_repo.get_user_by_email(
            session=session,
            email=token_data.username,
        )
    if user is None:
        raise CredentialsException(detail=AUTH_EXCEPTION_MESSAGE)
    return user

async def check_for_admin_access(
    user: UserSchema = Depends(get_current_user)
) -> UserSchema:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только админ имеет права добавлять/изменять/удалять данные"
        )
    return user