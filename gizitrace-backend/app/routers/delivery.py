from fastapi import APIRouter, HTTPException
from app.models.schemas import DeliveryCreate, DeliveryConfirm
from app.config import supabase
from datetime import date
import uuid

router = APIRouter()

@router.post("/create")
async def create_delivery(data: DeliveryCreate):
    today = date.today().isoformat()

    # Cek duplikat — satu vendor satu sekolah satu hari
    existing = supabase.table("deliveries") \
        .select("id") \
        .eq("school_id", data.school_id) \
        .eq("vendor_id", data.vendor_id) \
        .eq("date", today) \
        .execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Delivery untuk sekolah ini hari ini sudah ada")

    result = supabase.table("deliveries").insert({
        "vendor_id": data.vendor_id,
        "school_id": data.school_id,
        "date": today,
        "reported_portions": data.reported_portions,
        "menu_description": data.menu_description,
        "delivery_confirmed": False
    }).execute()

    return {"message": "Delivery berhasil dibuat", "data": result.data}

@router.post("/confirm")
async def confirm_delivery(data: DeliveryConfirm):
    # Cek delivery ada
    delivery = supabase.table("deliveries") \
        .select("id, delivery_confirmed") \
        .eq("id", data.delivery_id) \
        .execute()

    if not delivery.data or len(delivery.data) == 0:
        raise HTTPException(status_code=404, detail="Delivery tidak ditemukan")

    if delivery.data[0]["delivery_confirmed"]:
        raise HTTPException(status_code=400, detail="Delivery sudah dikonfirmasi sebelumnya")

    result = supabase.table("deliveries").update({
        "delivery_confirmed": True,
        "confirmed_by": data.confirmed_by
    }).eq("id", data.delivery_id).execute()

    return {"message": "Delivery berhasil dikonfirmasi", "data": result.data}
