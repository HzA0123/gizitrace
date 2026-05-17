from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import feedback, delivery, qr, ai, anomaly, dashboard

app = FastAPI(
    title="GiziTrace Backend API",
    description="Backend services for GiziTrace MVP",
    version="1.0.0",
)

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with prefix
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(delivery.router, prefix="/api/v1/delivery", tags=["Delivery"])
app.include_router(qr.router, prefix="/api/v1/qr", tags=["QR"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["Anomaly"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
def root():
    return {"message": "Welcome to GiziTrace API v1"}
