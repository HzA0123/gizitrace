from fastapi import APIRouter
from app.config import supabase
from datetime import date

router = APIRouter()

@router.get("/check")
async def anomaly_check(school_id: str):
    today = date.today().isoformat()
    anomalies_found = []
    
    # Ambil delivery hari ini untuk school_id
    delivery_result = supabase.table("deliveries").select("*").eq("school_id", school_id).eq("date", today).execute()
    delivery_today = delivery_result.data[0] if delivery_result.data else None
    
    # Ambil total_responses dari feedback hari ini
    feedback_result = supabase.table("feedback").select("response_full, response_half, response_reject").eq("school_id", school_id).eq("date", today).execute()
    
    total_responses = 0
    for fb in feedback_result.data:
        total_responses += fb.get("response_full", 0)
        total_responses += fb.get("response_half", 0)
        total_responses += fb.get("response_reject", 0)
        
    # Ambil total_students dari table schools
    school_result = supabase.table("schools").select("total_students").eq("id", school_id).execute()
    total_students = school_result.data[0].get("total_students", 0) if school_result.data else 0
    
    # Fungsi pembantu untuk insert anomaly jika belum ada
    def insert_anomaly_if_not_exists(anomaly_type, description, severity):
        existing = supabase.table("anomalies") \
            .select("id") \
            .eq("school_id", school_id) \
            .eq("date", today) \
            .eq("type", anomaly_type) \
            .execute()
            
        if not existing.data:
            supabase.table("anomalies").insert({
                "school_id": school_id,
                "date": today,
                "type": anomaly_type,
                "description": description,
                "severity": severity,
                "is_resolved": False
            }).execute()
            anomalies_found.append({"type": anomaly_type, "severity": severity, "description": description})

    # Rule 1 - Ghost Delivery (severity: high)
    if total_responses < (total_students * 0.30) and delivery_today:
        insert_anomaly_if_not_exists(
            "ghost_delivery", 
            f"Delivery dilaporkan tapi feedback sangat rendah ({total_responses}/{total_students} siswa)", 
            "high"
        )
        
    # Rule 2 - Scan Spike (severity: medium)
    if total_responses > (total_students * 1.20):
        insert_anomaly_if_not_exists(
            "scan_spike", 
            f"Jumlah scan feedback melebihi total siswa ({total_responses}/{total_students} siswa)", 
            "medium"
        )
        
    # Rule 3 - No Delivery (severity: high)
    if not delivery_today or not delivery_today.get("delivery_confirmed"):
        insert_anomaly_if_not_exists(
            "no_delivery", 
            "Tidak ada konfirmasi pengiriman makanan hari ini", 
            "high"
        )
        
    return {
        "message": f"Anomaly check completed for {school_id}", 
        "anomalies_found": anomalies_found
    }
