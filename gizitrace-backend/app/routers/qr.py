from fastapi import APIRouter
from app.config import supabase

router = APIRouter()

@router.get("/validate/{token}")
async def validate_qr(token: str):
    # Dummy implementation
    return {"message": "QR token validated", "token": token}
