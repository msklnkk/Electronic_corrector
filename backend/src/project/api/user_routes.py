import hashlib
import hmac

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import UserAlreadyExists, UserNameAlreadyExists, UserNotFound, UserTelegramAlreadyExists
from project.resource.auth import get_password_hash
from project.schemas.user import UserCreate, UserSchema

from project.api.depends import database, user_repo, get_current_user, check_for_admin_access
from project.services.telegram import TG_BOT_TOKEN, is_user_subscribed

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
            if user_dto.username:
                exists_login = await user_repo.get_user_by_login(session, user_dto.username)
                if exists_login and exists_login.user_id != user_id:
                    raise UserNameAlreadyExists(login=user_dto.username)

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


@user_routes.post("/telegram-auth")
async def telegram_auth(
    data: dict,
    current_user: UserSchema = Depends(get_current_user),
):
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(400, "No hash")

    # Формируем строку для проверки подписи
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()) if str(v) != "")
    secret_key = hashlib.sha256(TG_BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != received_hash:
        raise HTTPException(403, "Invalid hash")

    telegram_id = int(data["id"])
    tg_username = f"@{data.get('username')}" if data.get("username") else None

    async with database.session() as session:
        # Проверка на чужой аккаунт
        existing = await user_repo.get_user_by_telegram_id(session, telegram_id)
        if existing and existing.user_id != current_user.user_id:
            raise HTTPException(403, "Этот Telegram уже привязан к другому аккаунту")

        # Обновляем пользователя
        update_dto = UserCreate(**current_user.model_dump())
        update_dto.telegram_id = telegram_id
        update_dto.tg_username = tg_username
        await user_repo.update_user(session, current_user.user_id, update_dto)

        # Проверяем подписку
        subscribed = await is_user_subscribed(telegram_id)
        if current_user.is_tg_subscribed != subscribed:
            await user_repo.update_tg_subscription(session, current_user.user_id, subscribed)

    return {"success": True}


@user_routes.post("/check-tg-subscription")
async def check_tg_subscription(
    current_user: UserSchema = Depends(get_current_user),
):
    if not current_user.telegram_id:
        raise HTTPException(
            status_code=400,
            detail="Telegram-аккаунт не привязан"
        )

    # Реальная проверка через Telegram Bot API
    subscribed = await is_user_subscribed(current_user.telegram_id)

    # Если статус изменился — обновляем в базе
    if current_user.is_tg_subscribed != subscribed:
        async with database.session() as session:
            await user_repo.update_tg_subscription(
                session=session,
                user_id=current_user.user_id,
                subscribed=subscribed
            )
            await session.commit()

    return {
        "subscribed": subscribed,
        "message": "Подписка подтверждена!" if subscribed else "Вы не подписаны на канал"
    }