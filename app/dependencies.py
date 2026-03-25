from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db, get_redis
from app.services.user_service import UserService


DbSession = Annotated[Session, Depends(get_db)]


def get_user_service(db: DbSession, redis_client=Depends(get_redis)) -> UserService:
    settings = get_settings()
    return UserService(db=db, redis_client=redis_client, ttl_seconds=settings.redis_ttl_seconds)
