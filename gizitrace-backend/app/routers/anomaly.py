from fastapi import APIRouter
from app.config import supabase

router = APIRouter()

@router.get("/check")
async def anomaly_check(school_id: str):
    # Dummy implementation
    return {"message": f"Anomaly check completed for {school_id}", "anomalies_found": 0}
