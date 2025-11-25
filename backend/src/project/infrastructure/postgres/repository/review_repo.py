from typing import Type, List
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, true
from sqlalchemy.exc import IntegrityError, InterfaceError
from project.schemas.review import ReviewCreate, ReviewSchema
from project.infrastructure.postgres.models import Review
from project.core.exceptions import ReviewNotFound, ReviewAlreadyExists


class ReviewRepository:
    _collection: Type[Review] = Review

    async def check_connection(self, session: AsyncSession) -> bool:
        query = select(true())
        try:
            return await session.scalar(query)
        except (Exception, InterfaceError):
            return False

    async def get_all_reviews(self, session: AsyncSession) -> List[ReviewSchema]:
        query = select(self._collection)
        reviews = await session.scalars(query)
        return [ReviewSchema.model_validate(obj=review) for review in reviews.all()]

    async def get_review_by_id(self, session: AsyncSession, review_id: int) -> ReviewSchema:
        query = select(self._collection).where(self._collection.review_id == review_id)
        review = await session.scalar(query)
        if not review:
            raise ReviewNotFound(_id=review_id)
        return ReviewSchema.model_validate(obj=review)

    async def get_reviews_by_user_id(self, session: AsyncSession, user_id: int) -> Sequence[Review]:
        query = select(self._collection).where(self._collection.user_id == user_id)
        reviews = await session.scalars(query)
        return reviews.all()

    async def create_review(self, session: AsyncSession, review: ReviewCreate) -> ReviewSchema:
        query = (
            insert(self._collection)
            .values(review.model_dump())
            .returning(self._collection)
        )
        try:
            created_review = await session.scalar(query)
        except IntegrityError:
            raise ReviewAlreadyExists(user_id=review.user_id)
        return ReviewSchema.model_validate(obj=created_review)

    async def update_review(self, session: AsyncSession, review_id: int, review: ReviewCreate) -> ReviewSchema:
        existing_review = await session.scalar(
            select(self._collection).where(self._collection.review_id == review_id)
        )
        if not existing_review:
            raise ReviewNotFound(_id=review_id)
        query = (
            update(self._collection)
            .where(self._collection.review_id == review_id)
            .values(review.model_dump())
            .returning(self._collection)
        )
        updated_review = await session.scalar(query)
        return ReviewSchema.model_validate(obj=updated_review)

    async def delete_review(self, session: AsyncSession, review_id: int) -> None:
        query = delete(self._collection).where(self._collection.review_id == review_id)
        result = await session.execute(query)
        if not result.rowcount:
            raise ReviewNotFound(_id=review_id)