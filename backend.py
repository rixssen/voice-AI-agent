from database import init_db, RepairBooking, get_db
import datetime as dt
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
import uvicorn

# Initialize the database table
init_db()

# --- Pydantic Models ---
class BookingRequest(BaseModel):
    client_name: str
    issue_description: str
    technician_type: str  # e.g., "Plumber" or "Electrician"
    visit_time: dt.datetime

class BookingResponse(BaseModel):
    id: int
    client_name: str
    issue_description: str
    technician_type: str
    visit_time: dt.datetime
    canceled: bool

    class Config:
        from_attributes = True

class CancelResponse(BaseModel):
    canceled_count: int

app = FastAPI()

# --- Endpoints ---

@app.post('/book_repair/', response_model=BookingResponse)
def book_repair(request: BookingRequest, db: Session = Depends(get_db)):
    new_booking = RepairBooking(
        client_name=request.client_name,
        issue_description=request.issue_description,
        technician_type=request.technician_type,
        visit_time=request.visit_time,
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking

@app.post('/cancel_repair/', response_model=CancelResponse)
def cancel_repair(client_name: str, date: dt.date, db: Session = Depends(get_db)):
    start_dt = dt.datetime.combine(date, dt.time.min)
    end_dt = dt.datetime.combine(date, dt.time.max)
    
    results = db.execute(
        select(RepairBooking)
        .where(RepairBooking.client_name == client_name)
        .where(RepairBooking.visit_time >= start_dt)
        .where(RepairBooking.visit_time <= end_dt)
        .where(RepairBooking.canceled == False)
    )
    
    bookings = results.scalars().all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No matching booking found")

    for booking in bookings:
        booking.canceled = True
    
    db.commit()
    return CancelResponse(canceled_count=len(bookings))

@app.get('/view_schedule/')
def view_schedule(date: dt.date, db: Session = Depends(get_db)):
    start_dt = dt.datetime.combine(date, dt.time.min)
    end_dt = dt.datetime.combine(date, dt.time.max)

    results = db.execute(
        select(RepairBooking)
        .where(RepairBooking.canceled == False)
        .where(RepairBooking.visit_time >= start_dt)
        .where(RepairBooking.visit_time <= end_dt)
        .order_by(RepairBooking.visit_time.asc())
    )
    
    return results.scalars().all()

if __name__ == "__main__":
    # Make sure your file is named backend_1.py
    uvicorn.run("backend:app", host="127.0.0.1", port=4444, reload=True)