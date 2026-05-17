from fastapi import APIRouter
from app.config import supabase

router = APIRouter()

@router.get("/check")
async def anomaly_check():
    # Dummy implementation
    return {"message": "Anomaly check completed", "anomalies_found": 0}
