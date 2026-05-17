from fastapi import APIRouter, HTTPException
from app.config import supabase

router = APIRouter()

@router.get("/validate/{token}")
async def validate_qr(token: str):
    result = supabase.table("schools") \
        .select("id, name, district, city") \
        .eq("qr_token", token) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="QR token tidak valid atau sekolah tidak ditemukan")

    # Ambil daftar kelas sekolah ini
    classes = supabase.table("classes") \
        .select("id, name, grade") \
        .eq("school_id", result.data["id"]) \
        .order("grade") \
        .execute()

    return {
        "school": result.data,
        "classes": classes.data
    }
