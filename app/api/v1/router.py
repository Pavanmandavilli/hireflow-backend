from fastapi import APIRouter
from app.api.v1.endpoints import health, users, hiring

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(hiring.router, prefix="/hiring", tags=["hiring"])
