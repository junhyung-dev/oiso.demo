from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from db.session import get_db

from schemas.post_schema import PostCreate, PostResponse
from services import post_service

router = APIRouter()

#router측에서 service호출시, db session를 넘겨주어야함.
#Annotated, Session이고, Depend를 통해 get_db 실행 -> db_session에 값 전달
db_session = Annotated[Session, Depends(get_db)]


@router.post("/", response_model=PostResponse)
def create_post(post: PostCreate, db: db_session,):
    return post_service.create_post(db, post)