from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import UserAlreadyExists, UserNameAlreadyExists, UserNotFound, UserTelegramAlreadyExists
from project.resource.auth import get_password_hash
from project.schemas.user import UserCreate, UserSchema

from project.api.depends import database, user_repo, get_current_user, check_for_admin_access

user_routes = APIRouter()


@user_routes.get(
    "/all_users",
    response_model=list[UserSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_all_users() -> list[UserSchema]:
    async with database.session() as session:
        all_users = await user_repo.get_all_users(session=session)

    return all_users

@user_routes.post(
    "/add_user",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_for_admin_access)]
)
async def add_user(
    user_dto: UserCreate,
) -> UserSchema:
    try:
        async with database.session() as session:
            user_dto.password = get_password_hash(password=user_dto.password)
            new_user = await user_repo.create_user(session=session, user=user_dto)
    except UserAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)
    except UserNameAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)
    except UserTelegramAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_user

@user_routes.put(
    "/update_user/{user_id}",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)]
)
async def update_user(
    user_id: int,
    user_dto: UserCreate,
) -> UserSchema:
    try:
        async with database.session() as session:

            # --- Проверка уникальности логина ---
            if user_dto.user_name:
                exists_login = await user_repo.get_user_by_login(session, user_dto.user_name)
                if exists_login and exists_login.user_id != user_id:
                    raise UserNameAlreadyExists(login=user_dto.user_name)

            # --- Проверка уникальности Telegram username ---
            if user_dto.tg_username:
                exists_tg = await user_repo.get_user_by_tg_username(session, user_dto.tg_username)
                if exists_tg and exists_tg.user_id != user_id:
                    from project.core.exceptions import UserTelegramAlreadyExists
                    raise UserTelegramAlreadyExists(tg_username=user_dto.tg_username)

            user_dto.password = get_password_hash(password=user_dto.password)
            updated_user = await user_repo.update_user(
                session=session,
                user_id=user_id,
                user=user_dto,
            )
    except UserNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    return updated_user

@user_routes.delete(
    "/delete_user/{user_id}",
    status_code = status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_for_admin_access)]
)
async def delete_user(
        user_id: int,
) -> None:
    """Запрос: удалить пользователя"""
    try:
        async with database.session() as session:
            user = await user_repo.delete_user(session=session, user_id=user_id)
    except UserNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    return user

@user_routes.get(
    "/me",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_info(
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    """
    Получить данные текущего авторизованного пользователя
    """
    return current_user