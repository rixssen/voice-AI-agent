# Voice Agent for Household Service Booking

A production-ready **voice-controlled booking system** for household repairs and maintenance services. Built with FastAPI, SQLAlchemy, and integrated with voice processing capabilities via Groq.

## Overview

This project demonstrates a modern backend architecture for voice-first applications, handling complex workflows like service booking, cancellation, and date-based filtering—all accessible through natural language voice commands.

### Key Features

- **FastAPI Backend**: High-performance REST API with dependency injection and structured response models
- **Voice Integration**: Seamless voice-to-intent processing via Groq
- **Database Persistence**: SQLAlchemy ORM with clean data models (RepairBooking, etc.)
- **Smart Cancellation Logic**: Date-range filtering, client-name matching, booking status validation
- **Production-Ready**: Type hints, Pydantic schemas, error handling

## Architecture

```
Voice Input
    ↓
[Groq Voice Processing]
    ↓
[LLM Intent Recognition]
    ↓
[API Orchestration] → /book_repair/ or /cancel_repair/
    ↓
[SQLAlchemy ORM] → repairs.db
    ↓
[Structured Response] → Text-to-Speech
```

### Core Endpoints

#### **POST `/book_repair/`**
Creates a new repair booking with client details and service specifications.

**Request Body:**
```json
{
  "client_name": "John Doe",
  "issue_description": "Leaky faucet in kitchen",
  "technician_type": "plumber",
  "visit_time": "2026-05-16T14:00:00"
}
```

**Response:**
```json
{
  "booking_id": 1,
  "status": "confirmed",
  "client_name": "John Doe",
  "visit_time": "2026-05-16T14:00:00"
}
```

#### **POST `/cancel_repair/`**
Cancels a repair booking within a specified date range.

**Request Body:**
```json
{
  "client_name": "John Doe",
  "start_dt": "2026-05-15T00:00:00",
  "end_dt": "2026-05-17T23:59:59"
}
```

**Response:**
```json
{
  "status": "cancelled",
  "canceled_bookings": 1,
  "message": "Repair booking cancelled successfully"
}
```

## Project Structure

```
voice-agent/
├── backend.py              # FastAPI application & endpoints
├── database.py             # SQLAlchemy models & session management
├── test.py                 # Unit & integration tests
├── repairs.db              # SQLite database
├── requirements.txt        # Python dependencies
├── .gitignore             # Git exclusions
├── README.md              # This file
└── pyproject.toml         # Project metadata (optional)
```

## Setup & Installation

### Prerequisites
- Python 3.9+
- pip or conda

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/voice-agent.git
   cd voice-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (if using API keys)
   ```bash
   cp .env.example .env
   # Edit .env with your Groq API key and other credentials
   ```

5. **Initialize the database**
   ```bash
   python database.py  # Creates repairs.db with schema
   ```

6. **Run the application**
   ```bash
   uvicorn backend:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Testing

Run the test suite:
```bash
pytest test.py -v
```

For coverage:
```bash
pytest test.py --cov=. --cov-report=html
```

## Technical Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI |
| **Server** | Uvicorn |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | SQLite (portable) / PostgreSQL (production) |
| **Voice Processing** | Groq |
| **Validation** | Pydantic v2 |
| **Testing** | pytest |

## Design Decisions

### Why FastAPI?
- **Type Safety**: Full Python type hints enable IDE autocomplete and runtime validation
- **Performance**: Among the fastest Python web frameworks (async support)
- **Developer Experience**: Auto-generated OpenAPI documentation, built-in validation

### Why SQLAlchemy ORM?
- **Database Agnostic**: Switch from SQLite → PostgreSQL with minimal code changes
- **Query Composability**: Complex filters (date ranges, client matching) are clean and testable
- **Migration Support**: Alembic integration for schema evolution

### Cancellation Logic
The `/cancel_repair/` endpoint implements smart filtering:
- **Client name matching**: Filters by exact client_name
- **Date range filtering**: Only targets bookings within start_dt → end_dt
- **Status validation**: Ignores already-cancelled bookings (`canceled == False`)

This prevents accidental double-cancellations and enables granular user control.

## Future Enhancements

- [ ] **Authentication & Authorization**: JWT-based user roles (customers, technicians, admins)
- [ ] **Real-time Updates**: WebSocket integration for live booking status
- [ ] **Payment Integration**: Stripe or Razorpay for online payments
- [ ] **Notifications**: Email/SMS alerts for booking confirmations & reminders
- [ ] **Analytics Dashboard**: Booking trends, technician performance metrics
- [ ] **Multi-language Voice Support**: Extended language coverage beyond English

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the **MIT License**—see the [LICENSE](LICENSE) file for details.

## Author

**Rix** — AI/ML Engineer | Portfolio Project  
[GitHub](https://github.com/yourusername) | [LinkedIn](https://linkedin.com/in/yourprofile)

---

## Troubleshooting

### Database Lock Error
```
sqlite3.OperationalError: database is locked
```
**Solution**: Ensure only one process accesses the database. Close any other instances and retry.

### Port Already in Use
```
Address already in use: ('0.0.0.0', 8000)
```
**Solution**: Change the port or kill the process using it:
```bash
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Missing Dependencies
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution**: Ensure the virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

**Last Updated**: May 2026  
**Status**: Production-Ready ✓
