from __future__ import annotations

from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.models.user_model import User
from app.logging.logger import get_logger
from app.cache.decorators import cache

logger = get_logger("user-service")


class UserService:
    """
    Orchestration layer: API → Service → Repository → Database
    """

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def list_users(self) -> list[UserResponse]:
        users = await self.repo.get_all()
        return [UserResponse.model_validate(u) for u in users]

    @cache(ttl=60)
    async def get_user(self, user_id: int) -> UserResponse | None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def create_user(self, payload: UserCreate) -> UserResponse:
        logger.info(f"Creating user email={payload.email}")
        user = await self.repo.create(payload)
        logger.info(f"User created id={user.id}")
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, payload: UserUpdate) -> UserResponse | None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            return None
        updated = await self.repo.update(user, payload)
        return UserResponse.model_validate(updated)

    async def delete_user(self, user_id: int) -> bool:
        user = await self.repo.get_by_id(user_id)
        if not user:
            return False
        await self.repo.delete(user)
        logger.info(f"User deleted id={user_id}")
        return True
