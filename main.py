import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import create_document, get_documents
from schemas import Appointment

app = FastAPI(title="Hair Salon API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hair Salon Backend is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ------------------- Booking Endpoints -------------------

class BookingRequest(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: str
    service: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    notes: Optional[str] = None
    stylist: Optional[str] = None

@app.post("/api/appointments")
def create_booking(payload: BookingRequest):
    try:
        # Validate with Appointment schema for DB
        appointment = Appointment(**payload.model_dump())
        inserted_id = create_document("appointment", appointment)
        return {"success": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/appointments")
def list_bookings(service: Optional[str] = None, date: Optional[str] = None):
    try:
        filter_query = {}
        if service:
            filter_query["service"] = service
        if date:
            filter_query["date"] = date
        docs = get_documents("appointment", filter_query)
        # Convert ObjectId to string and return minimal fields
        result = []
        for d in docs:
            d["_id"] = str(d.get("_id"))
            result.append(d)
        return {"items": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
