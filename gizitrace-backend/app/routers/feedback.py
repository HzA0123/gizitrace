from fastapi import APIRouter
from app.models.schemas import FeedbackSubmit
from app.config import supabase

router = APIRouter()

@router.post("/submit")
async def submit_feedback(data: FeedbackSubmit):
    # Dummy implementation
    return {"message": "Feedback submitted successfully"}

@router.get("/today")
async def get_today_feedback(school_id: str):
    # Dummy implementation
    return {"message": "Today's feedback retrieved"}
