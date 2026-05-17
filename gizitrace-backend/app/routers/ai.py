from fastapi import APIRouter
from app.config import supabase

router = APIRouter()

@router.post("/analyze-photo")
async def analyze_photo(delivery_id: str, photo_url: str):
    # Dummy implementation integrating with OpenCV service later
    return {"message": "Photo analyzed", "waste_percent": 15.5}

@router.get("/recommend-menu")
async def recommend_menu(school_id: str):
    # Dummy implementation integrating with Recommendation service
    return {"message": "Menu recommended", "recommendation": "Nasi Goreng"}
