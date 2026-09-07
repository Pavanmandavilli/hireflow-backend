from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.dependencies.auth import get_user_service
from app.dependencies.auth import require_auth

router = APIRouter()


@router.get("/", response_model=list[UserResponse], summary="List all users")
async def list_users(
    service: UserService = Depends(get_user_service), current_user: dict = Depends(require_auth)
):
    return await service.list_users()


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service), current_user: dict = Depends(require_auth)
):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(payload)


@router.put("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service), current_user: dict = Depends(require_auth)
):
    user = await service.update_user(user_id, payload)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service), current_user: dict = Depends(require_auth)
):
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/secure", summary="Protected endpoint (requires JWT)")
async def secure_route(current_user: dict = Depends(require_auth)):
    return {"message": "Access granted", "user": current_user}

