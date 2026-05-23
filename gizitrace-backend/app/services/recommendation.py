import pandas as pd
from app.config import supabase

def get_menu_recommendations(school_id: str, top_n: int = 5) -> list:
    """
    Weighted scoring menu recommendation berdasarkan historis feedback.
    Score = (acceptance_rate × 0.50) + ((1 - waste_percent) × 0.30) + (frequency × 0.20)
    """
    
    # Ambil historis menu dari table menu_history
    result = supabase.table("menu_history") \
        .select("menu_name, acceptance_rate, avg_waste_percent, total_feedback") \
        .eq("school_id", school_id) \
        .execute()

    if not result.data or len(result.data) == 0:
        return get_fallback_recommendations()

    # Agregasi per menu (bisa muncul berkali-kali di historis)
    df = pd.DataFrame(result.data)
    
    grouped = df.groupby("menu_name").agg(
        avg_acceptance=("acceptance_rate", "mean"),
        avg_waste=("avg_waste_percent", "mean"),
        frequency=("menu_name", "count"),
        total_feedback=("total_feedback", "sum")
    ).reset_index()

    # Normalize frequency ke 0-1
    max_freq = grouped["frequency"].max()
    grouped["freq_normalized"] = grouped["frequency"] / max_freq if max_freq > 0 else 0

    # Hitung weighted score
    grouped["score"] = (
        (grouped["avg_acceptance"] * 0.50) +
        ((1 - grouped["avg_waste"] / 100) * 0.30) +
        (grouped["freq_normalized"] * 0.20)
    )

    # Sort descending, ambil top N
    top_menus = grouped.sort_values("score", ascending=False).head(top_n)

    return [
        {
            "menu_name": row["menu_name"],
            "score": round(float(row["score"]), 3),
            "acceptance_rate": round(float(row["avg_acceptance"]) * 100, 1),
            "avg_waste_percent": round(float(row["avg_waste"]), 1),
            "frequency_served": int(row["frequency"]),
            "total_feedback": int(row["total_feedback"])
        }
        for _, row in top_menus.iterrows()
    ]


def get_fallback_recommendations() -> list:
    """
    Fallback jika belum ada data historis — seed menu populer nasional
    """
    return [
        {"menu_name": "Nasi + Ayam Geprek + Lalapan + Susu", "score": None, "note": "Menu populer nasional"},
        {"menu_name": "Nasi + Ayam Bumbu Kecap + Sayur Bayam + Susu", "score": None, "note": "Menu populer nasional"},
        {"menu_name": "Nasi + Telur Balado + Sup Wortel + Susu", "score": None, "note": "Menu populer nasional"},
        {"menu_name": "Nasi + Ayam Goreng + Capcay + Susu", "score": None, "note": "Menu populer nasional"},
        {"menu_name": "Nasi + Rendang + Sayur Nangka + Susu", "score": None, "note": "Menu populer nasional"},
    ]
