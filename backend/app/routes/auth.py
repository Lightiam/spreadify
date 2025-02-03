from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
async def read_users_me():
    return {
        "id": "anonymous",
        "username": "Anonymous"
    }
