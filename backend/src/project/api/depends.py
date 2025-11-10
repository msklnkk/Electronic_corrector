from typing import Annotated
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from project.schemas.auth import TokenData
from project.core.config import settings
from project.core.exceptions import CredentialsException
from project.resource.auth import oauth2_scheme


from project.infrastructure.postgres.database import PostgresDatabase


database = PostgresDatabase()



# AUTH_EXCEPTION_MESSAGE = "Невозможно проверить данные для авторизации"
# async def get_current_client(
#     token: Annotated[str, Depends(oauth2_scheme)],
# ):
#     try:
#         payload = jwt.decode(
#             token=token,
#             key=settings.SECRET_AUTH_KEY.get_secret_value(),
#             algorithms=[settings.AUTH_ALGORITHM],
#         )
#         email: str = payload.get("sub")
#         if email is None:
#             raise CredentialsException(detail=AUTH_EXCEPTION_MESSAGE)
#         token_data = TokenData(username=email)
#     except JWTError:
#         raise CredentialsException(detail=AUTH_EXCEPTION_MESSAGE)
#     async with database.session() as session:
#         client = await client_repo.get_user_by_mail(
#             session=session,
#             mail=token_data.username,
#         )
#     if client is None:
#         raise CredentialsException(detail=AUTH_EXCEPTION_MESSAGE)
#     return client
#
# def check_for_admin_access(client: ClientSchema) -> None:
#     if not client.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Только админ имеет права добавлять/изменять/удалять данные"
#         )
