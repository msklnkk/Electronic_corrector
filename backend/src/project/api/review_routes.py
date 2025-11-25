from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import status

from project.core.exceptions import ReviewNotFound, ReviewAlreadyExists
from project.schemas.review import ReviewCreate, ReviewSchema

from project.api.depends import database, review_repo, get_current_user, check_for_admin_access
from project.schemas.user import UserSchema

review_routes = APIRouter()

@review_routes.get(
    "/all_reviews",
    response_model=list[ReviewSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_all_reviews() -> list[ReviewSchema]:
    async with database.session() as session:
        all_reviews = await review_repo.get_all_reviews(session=session)
    return all_reviews

@review_routes.get(
    "/review/{review_id}",
    response_model=ReviewSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_review_by_id(review_id: int) -> ReviewSchema:
    async with database.session() as session:
        review = await review_repo.get_review_by_id(session=session, review_id=review_id)
    return review

@review_routes.get(
    "/reviews/user/{user_id}",
    response_model=list[ReviewSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_reviews_by_user_id(user_id: int) -> list[ReviewSchema]:
    async with database.session() as session:
        reviews = await review_repo.get_reviews_by_user_id(session=session, user_id=user_id)
        return [ReviewSchema.model_validate(obj=review) for review in reviews]

@review_routes.post(
    "/add_review",
    response_model=ReviewSchema,
    status_code=status.HTTP_201_CREATED
)
async def add_review(
    review_dto: ReviewCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> ReviewSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            new_review = await review_repo.create_review(session=session, review=review_dto)
    except ReviewAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return new_review

@review_routes.put(
    "/update_review/{review_id}",
    response_model=ReviewSchema,
    status_code=status.HTTP_200_OK,
)
async def update_review(
    review_id: int,
    review_dto: ReviewCreate,
    current_user: UserSchema = Depends(get_current_user),
) -> ReviewSchema:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            updated_review = await review_repo.update_review(
                session=session,
                review_id=review_id,
                review=review_dto,
            )
    except ReviewNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)
    except ReviewAlreadyExists as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.message)

    return updated_review

@review_routes.delete(
    "/delete_review/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_review(
    review_id: int,
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    check_for_admin_access(user=current_user)
    try:
        async with database.session() as session:
            await review_repo.delete_review(session=session, review_id=review_id)
    except ReviewNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message)