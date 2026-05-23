from fastapi import APIRouter, HTTPException
from app.models.schemas import FeedbackSubmit
from app.config import supabase
from datetime import date

router = APIRouter()

@router.post("/submit")
async def submit_feedback(data: FeedbackSubmit):
    today = date.today().isoformat()

    # Cek delivery hari ini
    delivery = supabase.table("deliveries") \
        .select("id") \
        .eq("school_id", data.school_id) \
        .eq("date", today) \
        .single() \
        .execute()

    if not delivery.data:
        raise HTTPException(
            status_code=404, 
            detail="Tidak ada delivery terdaftar hari ini"
        )

    # Cek apakah feedback untuk kelas ini hari ini sudah ada
    existing = supabase.table("feedback") \
        .select("id, response_full, response_half, response_reject, total_responses") \
        .eq("school_id", data.school_id) \
        .eq("class_id", data.class_id) \
        .eq("date", today) \
        .execute()

    if existing.data:
        # Sudah ada → UPDATE, tambahkan ke count
        current = existing.data[0]
        new_full    = current["response_full"]    + data.response_full
        new_half    = current["response_half"]    + data.response_half
        new_reject  = current["response_reject"]  + data.response_reject
        new_total   = current["total_responses"]  + 1

        result = supabase.table("feedback").update({
            "response_full":    new_full,
            "response_half":    new_half,
            "response_reject":  new_reject,
            "total_responses":  new_total
        }).eq("id", current["id"]).execute()

        return {
            "message": "Feedback berhasil ditambahkan",
            "action": "updated",
            "total_responses": new_total
        }
    else:
        # Belum ada → INSERT baru
        result = supabase.table("feedback").insert({
            "school_id":       data.school_id,
            "class_id":        data.class_id,
            "delivery_id":     delivery.data["id"],
            "date":            today,
            "response_full":   data.response_full,
            "response_half":   data.response_half,
            "response_reject": data.response_reject,
            "total_responses": 1
        }).execute()

        return {
            "message": "Feedback berhasil disimpan",
            "action": "inserted",
            "total_responses": 1
        }

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
