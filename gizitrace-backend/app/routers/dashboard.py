from fastapi import APIRouter, HTTPException
from app.config import supabase
from datetime import date, timedelta
from datetime import datetime

router = APIRouter()

@router.get("/school/{school_id}")
async def get_school_dashboard(school_id: str):
    today = date.today().isoformat()
    
    # 1. Ambil data sekolah dari table schools
    school_result = supabase.table("schools").select("*").eq("id", school_id).execute()
    if not school_result.data:
        raise HTTPException(status_code=404, detail="School not found")
        
    school_data = school_result.data[0]
    
    # 2. Ambil feedback hari ini dari table feedback WHERE school_id + date = today
    # dengan join ke classes (nama kelas)
    feedback_today_result = supabase.table("feedback").select("*, classes(name)").eq("school_id", school_id).eq("date", today).execute()
    feedback_today = feedback_today_result.data
    
    # 3. Hitung agregat: total_responses, response_full, response_half, response_reject, acceptance_rate
    total_responses = 0
    response_full = 0
    response_half = 0
    response_reject = 0
    
    for fb in feedback_today:
        response_full += fb.get("response_full", 0)
        response_half += fb.get("response_half", 0)
        response_reject += fb.get("response_reject", 0)
    
    total_responses = response_full + response_half + response_reject
    acceptance_rate = (response_full / total_responses * 100) if total_responses > 0 else 0
    
    # 4. Ambil riwayat feedback 7 hari terakhir (untuk grafik mingguan)
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    history_result = supabase.table("feedback").select("*").eq("school_id", school_id).gte("date", seven_days_ago).lte("date", today).execute()
    
    history_by_date = {}
    for fb in history_result.data:
        d = fb["date"]
        if d not in history_by_date:
            history_by_date[d] = {"response_full": 0, "response_half": 0, "response_reject": 0}
        history_by_date[d]["response_full"] += fb.get("response_full", 0)
        history_by_date[d]["response_half"] += fb.get("response_half", 0)
        history_by_date[d]["response_reject"] += fb.get("response_reject", 0)
        
    # Format history into a sorted list
    history = []
    for d, v in history_by_date.items():
        v["total_responses"] = v["response_full"] + v["response_half"] + v["response_reject"]
        history.append({"date": d, **v})
    history = sorted(history, key=lambda x: x["date"])
    
    # 5. Ambil delivery hari ini dari table deliveries WHERE school_id + date = today
    delivery_result = supabase.table("deliveries").select("*").eq("school_id", school_id).eq("date", today).execute()
    delivery_today = delivery_result.data[0] if delivery_result.data else None
    
    return {
        "school": school_data,
        "aggregate": {
            "total_responses": total_responses,
            "response_full": response_full,
            "response_half": response_half,
            "response_reject": response_reject,
            "acceptance_rate": acceptance_rate
        },
        "feedback_today": feedback_today,
        "history": history,
        "delivery_today": delivery_today
    }

@router.get("/gov")
async def get_gov_dashboard():
    today = date.today().isoformat()
    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    
    # 1. Ambil semua sekolah dari table schools (termasuk total_students)
    schools_result = supabase.table("schools")\
        .select("id, name, district, city, total_students")\
        .execute()
    schools = schools_result.data
    
    # 2. Ambil feedback hari ini (untuk total_responses per sekolah di tampilan tabel)
    feedback_today_result = supabase.table("feedback").select("*").eq("date", today).execute()
    
    school_today_stats = {}
    for fb in feedback_today_result.data:
        sid = fb["school_id"]
        if sid not in school_today_stats:
            school_today_stats[sid] = {"full": 0, "half": 0, "reject": 0, "total": 0}
        
        full = fb.get("response_full", 0)
        half = fb.get("response_half", 0)
        reject = fb.get("response_reject", 0)
        
        school_today_stats[sid]["full"] += full
        school_today_stats[sid]["half"] += half
        school_today_stats[sid]["reject"] += reject
        school_today_stats[sid]["total"] += (full + half + reject)
    
    # 3. Ambil feedback 7 hari terakhir untuk kalkulasi acceptance_rate per sekolah
    feedback_7d_result = supabase.table("feedback")\
        .select("school_id, response_full, total_responses")\
        .gte("date", seven_days_ago)\
        .execute()
    
    school_7d_stats = {}
    for fb in feedback_7d_result.data:
        sid = fb["school_id"]
        if sid not in school_7d_stats:
            school_7d_stats[sid] = {"full": 0, "total": 0}
        school_7d_stats[sid]["full"] += fb.get("response_full", 0)
        school_7d_stats[sid]["total"] += fb.get("total_responses", 0)
        
    schools_data = []
    
    for s in schools:
        sid = s["id"]
        today_stats = school_today_stats.get(sid, {"full": 0, "half": 0, "reject": 0, "total": 0})
        stats_7d = school_7d_stats.get(sid, {"full": 0, "total": 0})
        
        # acceptance_rate per sekolah = rata-rata 7 hari (0-1 fraction)
        acc_rate = round(stats_7d["full"] / stats_7d["total"], 3) if stats_7d["total"] > 0 else 0
        
        schools_data.append({
            "school_id": sid,
            "name": s.get("name"),
            "district": s.get("district"),
            "city": s.get("city"),
            "total_students": s.get("total_students"),
            "total_responses": today_stats["total"],
            "acceptance_rate": acc_rate
        })
    
    # 4. Kalkulasi aggregate_total acceptance_rate dari 7 hari terakhir (semua sekolah)
    feedback_agg_result = supabase.table("feedback")\
        .select("response_full, total_responses")\
        .gte("date", seven_days_ago)\
        .execute()
    
    if feedback_agg_result.data:
        total_full = sum(f.get("response_full", 0) for f in feedback_agg_result.data)
        total_resp = sum(f.get("total_responses", 0) for f in feedback_agg_result.data)
        acceptance_rate = round(total_full / total_resp, 3) if total_resp > 0 else 0
    else:
        acceptance_rate = 0
    
    # Hitung total_responses hari ini untuk aggregate_total
    total_today_full = sum(s["full"] for s in school_today_stats.values())
    total_today_half = sum(s["half"] for s in school_today_stats.values())
    total_today_reject = sum(s["reject"] for s in school_today_stats.values())
    total_today_responses = sum(s["total"] for s in school_today_stats.values())
    
    # 5. Ambil semua anomalies WHERE is_resolved = false
    anomalies_result = supabase.table("anomalies").select("*, schools(name)").eq("is_resolved", False).execute()
    anomalies = anomalies_result.data
    
    return {
        "schools": schools_data,
        "anomalies_active": anomalies,
        "aggregate_total": {
            "total_responses": total_today_responses,
            "response_full": total_today_full,
            "response_half": total_today_half,
            "response_reject": total_today_reject,
            "acceptance_rate": acceptance_rate  # rata-rata 7 hari terakhir (0-1 fraction)
        }
    }
