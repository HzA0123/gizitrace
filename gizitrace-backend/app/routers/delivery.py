from fastapi import APIRouter
from app.models.schemas import DeliveryCreate
from app.config import supabase

router = APIRouter()

@router.post("/create")
async def create_delivery(data: DeliveryCreate):
    # Dummy implementation
    return {"message": "Delivery created successfully"}

@router.post("/confirm")
async def confirm_delivery(delivery_id: str):
    # Dummy implementation
    return {"message": "Delivery confirmed"}
