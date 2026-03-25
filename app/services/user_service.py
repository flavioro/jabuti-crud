import logging
from uuid import UUID

from redis import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.cache_service import CacheService

LOGGER = logging.getLogger(__name__)


class DuplicateEmailError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserService:
    def __init__(self, db: Session, redis_client: Redis | None, ttl_seconds: int) -> None:
        self.repository = UserRepository(db)
        self.cache = CacheService(redis_client, ttl_seconds)

    def list_users(self, *, limit: int, offset: int) -> UserListResponse:
        cache_key = self.cache.list_key(limit, offset)
        cached = self.cache.get_json(cache_key)
        if cached is not None:
            return UserListResponse.model_validate(cached)

        users, total = self.repository.list_users(limit=limit, offset=offset)
        response = UserListResponse(
            items=[UserResponse.model_validate(user) for user in users],
            total=total,
            limit=limit,
            offset=offset,
        )
        self.cache.set_json(cache_key, response.model_dump(mode="json"))
        return response

    def get_user(self, user_id: UUID) -> UserResponse:
        cache_key = self.cache.detail_key(user_id)
        cached = self.cache.get_json(cache_key)
        if cached is not None:
            return UserResponse.model_validate(cached)

        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        response = UserResponse.model_validate(user)
        self.cache.set_json(cache_key, response.model_dump(mode="json"))
        return response

    def create_user(self, payload: UserCreate) -> UserResponse:
        user = User(nome=payload.nome, email=str(payload.email), idade=payload.idade)
        try:
            created = self.repository.create(user=user)
        except IntegrityError as exc:
            self.repository.db.rollback()
            LOGGER.warning("duplicate_email_on_create email=%s", payload.email)
            raise DuplicateEmailError from exc
        self.cache.invalidate_users_cache()
        return UserResponse.model_validate(created)

    def update_user(self, user_id: UUID, payload: UserUpdate) -> UserResponse:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        data = payload.model_dump(exclude_unset=True)
        for field_name, field_value in data.items():
            if field_name == "email" and field_value is not None:
                setattr(user, field_name, str(field_value))
            else:
                setattr(user, field_name, field_value)

        try:
            updated = self.repository.update(user)
        except IntegrityError as exc:
            self.repository.db.rollback()
            LOGGER.warning("duplicate_email_on_update user_id=%s", user_id)
            raise DuplicateEmailError from exc
        self.cache.invalidate_users_cache(user_id)
        return UserResponse.model_validate(updated)

    def delete_user(self, user_id: UUID) -> None:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError
        self.repository.delete(user)
        self.cache.invalidate_users_cache(user_id)
