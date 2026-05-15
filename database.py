from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime as dt
from sqlalchemy.orm import Session

# 1. Define the Database URL (Keeping the name or changing to repairs.db)
DATABASE_URL = "sqlite:///./repairs.db"

# 2. Create the engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 3. Session setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class
Base = declarative_base()

# 5. Repair Booking Model
class RepairBooking(Base):
    __tablename__ = "repair_bookings"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True)
    # What needs fixing? (e.g., "Leaking pipe", "Socket sparking")
    issue_description = Column(String, nullable=True) 
    # Who is needed? (e.g., "Plumber", "Electrician")
    technician_type = Column(String, index=True)
    # When should they arrive?
    visit_time = Column(DateTime, index=True)
    canceled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

# 6. Create the tables
def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    print("Updating/Creating Home Services database...")
    init_db()
    print("Success! 'repairs.db' is ready for Plumbers and Electricians.")