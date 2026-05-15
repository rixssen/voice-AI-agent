# Architecture & Design Document

## System Overview

The Voice Agent for Household Service Booking is a **microservice-oriented backend** designed for voice-first interactions. The system follows a clean layered architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────┐
│         Voice Processing Layer                  │
│      (Groq / Speech-to-Text / LLM)             │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│       FastAPI Application Layer                 │
│  (/book_repair/, /cancel_repair/ endpoints)    │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Business Logic Layer                       │
│   (Booking creation, validation, cancellation) │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Data Access Layer (SQLAlchemy ORM)        │
│   (RepairBooking model, query composition)     │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│          Database Layer (SQLite)                │
│              (repairs.db)                       │
└─────────────────────────────────────────────────┘
```

## Component Details

### 1. Voice Processing Layer
**File**: `backend.py` (integration points)

The voice agent receives audio input, transcribes it via Groq, and uses an LLM to extract structured intent:

```
Input: "Cancel my plumbing repair scheduled for tomorrow"
  ↓
[Groq STT] → "cancel my plumbing repair scheduled for tomorrow"
  ↓
[LLM Intent Recognition] → {
    "action": "cancel_repair",
    "client_name": "...",
    "date_range": {...}
}
  ↓
[API Call] → POST /cancel_repair/
```

**Considerations**:
- **Latency**: Voice processing adds 500ms-2s. Consider caching common intents.
- **Accuracy**: LLM may misinterpret ambiguous voice input. Implement fallback confirmation prompts.
- **Cost**: Groq API charges per request. Optimize token usage.

### 2. FastAPI Application Layer

#### Endpoint: `/book_repair/` (POST)

**Purpose**: Create a new repair booking

**Request Schema** (`BookingRequest`):
```python
class BookingRequest(BaseModel):
    client_name: str
    issue_description: str
    technician_type: str  # e.g., "plumber", "electrician"
    visit_time: datetime
```

**Response Schema** (`BookingResponse`):
```python
class BookingResponse(BaseModel):
    booking_id: int
    status: str  # "confirmed", "pending", etc.
    client_name: str
    visit_time: datetime
```

**Flow**:
1. FastAPI validates request via Pydantic
2. Creates `RepairBooking` ORM instance
3. Commits to database
4. Returns structured response

**Error Handling**:
- Invalid datetime format → 422 Unprocessable Entity
- Database constraint violation → 400 Bad Request
- Database connection error → 500 Internal Server Error

---

#### Endpoint: `/cancel_repair/` (POST)

**Purpose**: Cancel existing repair booking(s) within a date range

**Request Schema** (`CancelRequest`):
```python
class CancelRequest(BaseModel):
    client_name: str
    start_dt: datetime
    end_dt: datetime
```

**Response Schema** (`CancelResponse`):
```python
class CancelResponse(BaseModel):
    status: str  # "cancelled"
    canceled_bookings: int
    message: str
```

**Query Logic** (SQLAlchemy):
```python
results = db.execute(
    select(RepairBooking)
    .where(RepairBooking.client_name == client_name)
    .where(RepairBooking.visit_time >= start_dt)
    .where(RepairBooking.visit_time <= end_dt)
    .where(RepairBooking.canceled == False)
)
```

**Why This Approach?**
- **Composable Filters**: Each `.where()` is independently testable
- **Database Delegation**: Filtering happens at the SQL layer (efficient)
- **Explicit State**: `canceled == False` prevents double-cancellations

---

### 3. Data Access Layer (SQLAlchemy)

#### RepairBooking Model

```python
class RepairBooking(Base):
    __tablename__ = "repair_bookings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str]
    issue_description: Mapped[str]
    technician_type: Mapped[str]
    visit_time: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    canceled: Mapped[bool] = mapped_column(default=False)
```

**Design Decisions**:
- **Soft Delete**: `canceled` flag instead of physical deletion (audit trail)
- **Timestamps**: `created_at` for analytics and debugging
- **No Foreign Keys** (for now): Assumes single technician pool. Scale with user_id FK if needed.

**Future Indexing**:
```python
__table_args__ = (
    Index("idx_client_name", "client_name"),
    Index("idx_visit_time", "visit_time"),
    Index("idx_canceled", "canceled"),
)
```

### 4. Database Layer

**Technology**: SQLite (development) / PostgreSQL (production)

**Rationale**:
- **SQLite**: Zero-config, file-based, perfect for prototyping and portfolio projects
- **PostgreSQL**: ACID compliance, concurrent connections, suitable for multi-tenant systems

**Migration Path**:
SQLAlchemy's database-agnostic ORM means switching databases requires only connection string changes:

```python
# Development
DATABASE_URL = "sqlite:///./repairs.db"

# Production
DATABASE_URL = "postgresql://user:pass@localhost/voice_agent_db"
```

## Request/Response Flow: Example

### Scenario: Cancel a Plumbing Repair

**1. Voice Input**
```
User: "Cancel my plumbing repair tomorrow"
```

**2. Groq Processing**
```
STT Output: "cancel my plumbing repair tomorrow"
LLM Intent: {
  "action": "cancel_repair",
  "client_name": "John Doe",
  "date_range": {
    "start": "2026-05-16T00:00:00",
    "end": "2026-05-16T23:59:59"
  }
}
```

**3. API Request**
```http
POST /cancel_repair/ HTTP/1.1
Content-Type: application/json

{
  "client_name": "John Doe",
  "start_dt": "2026-05-16T00:00:00",
  "end_dt": "2026-05-16T23:59:59"
}
```

**4. Backend Processing**
```
- Validate schema (Pydantic)
- Query database: SELECT * FROM repair_bookings WHERE ...
- Mark matching bookings as canceled=True
- Commit transaction
- Return cancellation count
```

**5. API Response**
```json
{
  "status": "cancelled",
  "canceled_bookings": 1,
  "message": "1 repair booking cancelled successfully"
}
```

**6. Voice Response**
```
TTS Output: "Your plumbing repair scheduled for tomorrow has been cancelled."
```

## Error Handling Strategy

### Client Errors (4xx)

**400 Bad Request**
- Invalid date format in request body
- Missing required fields
- Logically invalid state (e.g., end_dt < start_dt)

**422 Unprocessable Entity**
- Pydantic validation failure
- Type mismatch (e.g., string provided for datetime field)

**404 Not Found**
- No bookings found matching criteria (future: implement explicit 404 vs empty array)

### Server Errors (5xx)

**500 Internal Server Error**
- Database connection lost
- Unexpected exception in business logic
- File system issues (for SQLite)

**503 Service Unavailable**
- Database under maintenance
- Groq API rate-limited or down

### Mitigation Strategies

```python
@app.post("/cancel_repair/")
async def cancel_repair(request: CancelRequest, db: Session = Depends(get_db)):
    try:
        # Business logic
        pass
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Performance Considerations

### Database Query Optimization

**Current**: Linear scan on every cancellation request
```python
# O(n) scan through all bookings
results = db.execute(
    select(RepairBooking).where(...)
)
```

**Future**: Add composite index for faster queries
```sql
CREATE INDEX idx_client_visit ON repair_bookings(client_name, visit_time) 
WHERE canceled = FALSE;
```

**Estimated Impact**: 100-1000x faster queries on large datasets

### API Response Caching

For frequently requested data (e.g., available time slots):
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_available_slots(date: str):
    # Cached for 1 hour
    pass
```

### Connection Pooling

SQLAlchemy's default pooling is adequate for small deployments. For production:
```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True  # Verify connection before use
)
```

## Security Considerations

### Input Validation

Pydantic handles basic type validation. For additional safety:

```python
from pydantic import validator

class BookingRequest(BaseModel):
    client_name: str
    
    @validator('client_name')
    def validate_client_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError('Name must be 2-100 characters')
        if not v.isalpha() or ' ' not in v:  # Require first & last name
            raise ValueError('Invalid name format')
        return v.strip()
```

### SQL Injection Prevention

SQLAlchemy ORM automatically parameterizes queries, preventing SQL injection:
```python
# Safe: parameterized query
db.execute(
    select(RepairBooking).where(RepairBooking.client_name == client_name)
)

# Dangerous: string interpolation (NEVER DO THIS)
db.execute(f"SELECT * FROM repair_bookings WHERE client_name = '{client_name}'")
```

### Rate Limiting

For production, implement rate limits on voice agent requests:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

@app.post("/book_repair/")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def book_repair(...):
    pass
```

### Authentication (Future)

Add JWT-based authentication:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/book_repair/")
async def book_repair(
    request: BookingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify JWT token
    pass
```

## Testing Strategy

### Unit Tests
- Model validation: Does RepairBooking reject invalid data?
- Schema validation: Do Pydantic models catch malformed requests?

### Integration Tests
- Database operations: Does booking persist and retrieve correctly?
- Endpoint behavior: Does `/cancel_repair/` correctly filter by date range?

### End-to-End Tests
- Full flow: Voice input → API call → Database update → Response

**Example Test**:
```python
def test_cancel_repair_by_date_range():
    # Setup
    client = TestClient(app)
    db = SessionLocal()
    
    # Create a booking for tomorrow
    booking = RepairBooking(
        client_name="John Doe",
        issue_description="Broken pipe",
        technician_type="plumber",
        visit_time=datetime.now() + timedelta(days=1)
    )
    db.add(booking)
    db.commit()
    
    # Cancel it
    response = client.post(
        "/cancel_repair/",
        json={
            "client_name": "John Doe",
            "start_dt": str(datetime.now()),
            "end_dt": str(datetime.now() + timedelta(days=2))
        }
    )
    
    # Verify
    assert response.status_code == 200
    assert response.json()["canceled_bookings"] == 1
```

## Deployment Architecture

### Development
```
Local Machine → FastAPI dev server (uvicorn) → SQLite (repairs.db)
```

### Production (Recommended)
```
Load Balancer → Gunicorn Workers (4-8) → 
    ↓
FastAPI App
    ↓
Connection Pool → PostgreSQL (cloud DB)
    ↓
Backup / Replication
```

**Containerization** (Docker):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring & Logging

### Structured Logging
```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Usage
logger.info("Booking created", extra={"booking_id": 123, "client": "John Doe"})
```

### Key Metrics
- Request latency (p50, p95, p99)
- Database query duration
- API error rate by endpoint
- Voice processing success rate

## Conclusion

This architecture balances simplicity (for rapid prototyping) with scalability (clear paths to production). The separation of concerns enables independent testing, maintenance, and future enhancements.

---

**Last Updated**: May 2026
