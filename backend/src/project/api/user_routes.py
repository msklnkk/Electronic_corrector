# backend/src/project/api/user_routes.py
import hashlib
import hmac
import base64
from fastapi import UploadFile, File

from fastapi import APIRouter, Depends, HTTPException, status

from project.core.exceptions import UserAlreadyExists, UserNameAlreadyExists, UserNotFound, UserTelegramAlreadyExists
from project.resource.auth import get_password_hash, verify_password
from project.schemas.user import UserCreate, UserSchema, UserUpdate, UserUpdateSelf, ChangePasswordRequest

from project.api.depends import database, user_repo, get_current_user, check_for_admin_access
from project.services.telegram import TG_BOT_TOKEN, is_user_subscribed

user_routes = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_MB = 2


@user_routes.get(
    "/users",
    response_model=list[UserSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_for_admin_access)],
)
async def get_all_users() -> list[UserSchema]:
    async with database.session() as session:
        all_users = await user_repo.get_all_users(session=session)

    return all_users

@user_routes.post(
    "/users",
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

@user_routes.get(
    "/users/{id}",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def get_user(
    id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    if current_user.user_id != id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    try:
        async with database.session() as session:
            user = await user_repo.get_user_by_id(session=session, user_id=id)
    except UserNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    return user

@user_routes.put(
    "/users/{id}",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    id: int,
    user_dto: UserUpdate,
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    if current_user.user_id != id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    # Обычный пользователь не может менять роль и флаг админа
    if not current_user.is_admin:
        user_dto.role = None
        user_dto.is_admin = None
        user_dto.is_tg_subscribed = None

    try:
        async with database.session() as session:
            if user_dto.password:
                user_dto.password = get_password_hash(password=user_dto.password)
            updated_user = await user_repo.update_user(
                session=session,
                user_id=id,
                user=user_dto,
            )
    except UserNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except UserNameAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)
    except UserTelegramAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)
    return updated_user

@user_routes.delete(
    "/users/{id}",
    status_code = status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_for_admin_access)]
)
async def delete_user(
        id: int,
) -> None:
    try:
        async with database.session() as session:
            user = await user_repo.delete_user(session=session, user_id=id)
    except UserNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)

    return user


@user_routes.post(
    "/users/{id}/password",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    id: int,
    data: ChangePasswordRequest,
    current_user: UserSchema = Depends(get_current_user),
):
    if current_user.user_id != id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Текущий пароль введён неверно")

    update_dto = UserUpdateSelf(password=get_password_hash(data.new_password))

    async with database.session() as session:
        await user_repo.update_user(session=session, user_id=id, user=update_dto)

    return {"detail": "Пароль успешно изменён"}

#
# @user_routes.post("/telegram-auth")
# async def telegram_auth(
#     data: dict,
#     current_user: UserSchema = Depends(get_current_user),
# ):
#     received_hash = data.pop("hash", None)
#     if not received_hash:
#         raise HTTPException(400, "No hash")
#
#     # Формируем строку для проверки подписи
#     data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()) if str(v) != "")
#     secret_key = hashlib.sha256(TG_BOT_TOKEN.encode()).digest()
#     calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
#
#     if calculated_hash != received_hash:
#         raise HTTPException(403, "Invalid hash")
#
#     telegram_id = int(data["id"])
#     tg_username = f"@{data.get('username')}" if data.get("username") else None
#
#     async with database.session() as session:
#         # Проверка на чужой аккаунт
#         existing = await user_repo.get_user_by_telegram_id(session, telegram_id)
#         if existing and existing.user_id != current_user.user_id:
#             raise HTTPException(403, "Этот Telegram уже привязан к другому аккаунту")
#
#         # Обновляем пользователя
#         update_dto = UserCreate(**current_user.model_dump())
#         update_dto.telegram_id = telegram_id
#         update_dto.tg_username = tg_username
#         await user_repo.update_user(session, current_user.user_id, update_dto)
#
#         # Проверяем подписку
#         subscribed = await is_user_subscribed(telegram_id)
#         if current_user.is_tg_subscribed != subscribed:
#             await user_repo.update_tg_subscription(session, current_user.user_id, subscribed)
#
#     return {"success": True}
#
#
# @user_routes.post("/check-tg-subscription")
# async def check_tg_subscription(
#     current_user: UserSchema = Depends(get_current_user),
# ):
#     if not current_user.telegram_id:
#         raise HTTPException(
#             status_code=400,
#             detail="Telegram-аккаунт не привязан"
#         )
#
#     # Проверка через Telegram Bot API
#     subscribed = await is_user_subscribed(current_user.telegram_id)
#
#     # Если статус изменился — обновляем в базе
#     if current_user.is_tg_subscribed != subscribed:
#         async with database.session() as session:
#             await user_repo.update_tg_subscription(
#                 session=session,
#                 user_id=current_user.user_id,
#                 subscribed=subscribed
#             )
#             await session.commit()
#
#     return {
#         "subscribed": subscribed,
#         "message": "Подписка подтверждена!" if subscribed else "Вы не подписаны на канал"
#     }
#

@user_routes.post(
    "/users/{id}/avatar",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def upload_avatar(
    id: int,
    file: UploadFile = File(...),
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    if current_user.user_id != id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Допустимые форматы: JPEG, PNG, WebP, GIF",
        )

    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Размер файла не должен превышать {MAX_SIZE_MB} МБ",
        )

    b64 = base64.b64encode(content).decode("utf-8")
    avatar_data = f"data:{file.content_type};base64,{b64}"

    update_dto = UserUpdateSelf(avatar_data=avatar_data)
    async with database.session() as session:
        updated_user = await user_repo.update_user(
            session=session,
            user_id=id,
            user=update_dto,
        )
    return updated_user