from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import Literal, List, Optional

from corrector.application.database import get_session
from corrector.application.database.tables import Review, User
from corrector.application.http_api.controllers.user import UserDTO

router = APIRouter(
    prefix="/reviews", 
    tags=["reviews"]
    )

SessionDep = Annotated[Session, Depends(get_session)]

class ReviewDb(BaseModel):
    user: UserDTO
    mark: int
    review_text: str = Field(description="Отзыв", max_length=1000)
    created_at: date

class ReviewCr(BaseModel):
    user_id: int
    mark: int
    review_text: str = Field(description="Отзыв", max_length=1000)
    created_at: date


@router.get("/reviews", response_model=List[ReviewDb])
async def read_reviews(session: SessionDep):
    """Запрос: получение списка всех отзывов"""
    query = select(Review).options(
        joinedload(Review.user)
    )
    reviews = session.scalars(query).all()
    return reviews

@router.get("/user/{user_id}", response_model=List[ReviewDb])
async def read_reviews_by_user(user_id: int, session: SessionDep):
    """Запрос: получение всех отзывов определенного пользователя"""
    query = select(Review).filter(Review.user_id == user_id).options(
        joinedload(Review.user)
    )
    reviews = session.scalars(query).all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this user")
    return reviews

@router.get("/filter", response_model=List[ReviewDb])
async def filter_reviews_by_mark(mark: int, session: SessionDep):
    """Запрос: фильтрация отзывов по оценке (положительные/отрицательные/нейтральные)"""
    if mark > 3:
        query = select(Review).filter(Review.mark > 3).options(
            joinedload(Review.user),  # Загружаем пользователя
        )
    elif mark < 3:
        query = select(Review).filter(Review.mark < 3).options(
            joinedload(Review.user),  # Загружаем пользователя
        )
    else:
        query = select(Review).filter(Review.mark == 3).options(
            joinedload(Review.user),  # Загружаем пользователя
        )
    reviews = session.scalars(query).all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found with this mark")
    return reviews

@router.post("/", response_model=ReviewCr)
async def create_review(review: ReviewCr, session: SessionDep):
    """Запрос: создание нового отзыва"""
    user = session.get(User, review.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db_review = Review(
        user_id=review.user_id,
        mark=review.mark,
        review_text=review.review_text,
        created_at=review.created_at
    )
    
    session.add(db_review)
    session.commit()
    session.refresh(db_review)
    
    return db_review