from fastapi import APIRouter, HTTPException
from app.models.schemas import FeedbackSubmit
from app.config import supabase
from datetime import date

router = APIRouter()

@router.post("/submit")
async def submit_feedback(data: FeedbackSubmit):
    today = date.today().isoformat()

    # Cek apakah ada delivery hari ini untuk sekolah ini
    delivery = supabase.table("deliveries") \
        .select("id") \
        .eq("school_id", data.school_id) \
        .eq("date", today) \
        .execute()
        
    # .single() will throw if not exactly 1 row, using list check
    if not delivery.data or len(delivery.data) == 0:
        raise HTTPException(status_code=404, detail="Tidak ada delivery terdaftar hari ini untuk sekolah ini")

    # Insert feedback
    result = supabase.table("feedback").insert({
        "school_id": data.school_id,
        "class_id": data.class_id,
        "delivery_id": delivery.data[0]["id"],
        "date": today,
        "response_full": data.response_full,
        "response_half": data.response_half,
        "response_reject": data.response_reject,
        "total_responses": data.response_full + data.response_half + data.response_reject
    }).execute()

    return {"message": "Feedback berhasil disimpan", "data": result.data}

@router.get("/today/{school_id}")
async def get_today_feedback(school_id: str):
    today = date.today().isoformat()

    result = supabase.table("feedback") \
        .select("*, classes(name, grade)") \
        .eq("school_id", school_id) \
        .eq("date", today) \
        .execute()

    if not result.data:
        return {"message": "Belum ada feedback hari ini", "data": []}

    # Hitung total agregat
    total_full = sum(r["response_full"] for r in result.data)
    total_half = sum(r["response_half"] for r in result.data)
    total_reject = sum(r["response_reject"] for r in result.data)
    total = total_full + total_half + total_reject

    return {
        "date": today,
        "breakdown_per_class": result.data,
        "aggregate": {
            "total_responses": total,
            "response_full": total_full,
            "response_half": total_half,
            "response_reject": total_reject,
            "acceptance_rate": round((total_full / total * 100), 2) if total > 0 else 0
        }
    }
