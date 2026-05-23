from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.config import supabase
from app.services.recommendation import get_menu_recommendations

router = APIRouter()

@router.post("/analyze-photo")
async def analyze_photo(
    delivery_id: str = Form(...),
    school_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Dummy implementation integrating with OpenCV service later
    return {"message": "Photo analyzed", "waste_percent": 15.5, "filename": file.filename}

@router.get("/recommend-menu")
async def recommend_menu(school_id: str):
    try:
        recommendations = get_menu_recommendations(school_id)
        return {
            "school_id": school_id,
            "recommendations": recommendations,
            "total": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
