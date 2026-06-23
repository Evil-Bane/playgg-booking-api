# PlayGG — Cafe Booking API

Backend for **PlayGG's** gaming-cafe booking platform: browse cafes, check seat
availability per time slot, and book or cancel seats — with solid validation and
clear, consistent error handling.

> **Live API:** **https://playgg-booking-api.onrender.com** &nbsp;·&nbsp; **Interactive docs:** [`/docs`](https://playgg-booking-api.onrender.com/docs) (Swagger UI) and [`/redoc`](https://playgg-booking-api.onrender.com/redoc)
>
> **Demo login for the protected endpoints:** username `admin` · password `admin` (via `POST /login`).
>
> _Hosted on Render's free tier — the first request after idle may take ~30–60s to wake the service._

Built with **FastAPI + SQLAlchemy + PostgreSQL**. Runs locally on **SQLite with
zero configuration**.

---

## Contents
- [Features](#features)
- [Tech stack & why](#tech-stack--why)
- [Project structure](#project-structure)
- [Quick start (local)](#quick-start-local)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Business logic & rules](#business-logic--rules)
- [Testing](#testing)
- [Deployment](#deployment)
- [Design decisions & trade-offs](#design-decisions--trade-offs)
- [What I'd add with more time](#what-id-add-with-more-time)

---

## Features

**Core**
- List cafes, filter by city, fetch a single cafe
- Create a booking with full validation
- List all bookings for a cafe
- Cancel a booking
- Capacity rule — a booking fails if requested seats exceed seats left for that slot
- No double-booking — a user can't hold two active bookings for the same cafe/date/slot
- Consistent, meaningful error messages on every failure path

**Bonus (all implemented)**
- 🔐 **JWT auth** — `POST /login`; `POST /bookings` and `DELETE /bookings/:id` are protected
- 📄 **Pagination** on `GET /cafes` (`?page=`, `?limit=`)
- 🗓️ **Availability** — `GET /cafes/:id/availability?date=…` returns open seats per slot
- ✅ **Unit tests** for the booking logic (13 tests, pytest)

---

## Tech stack & why

| Layer | Choice | Reason |
|---|---|---|
| Language | **Python 3.13** | — |
| Framework | **FastAPI** | RESTful by design, async-ready, and auto-generates Swagger/OpenAPI docs at `/docs` |
| Validation | **Pydantic v2** | Declarative request/response validation with clear error messages |
| ORM | **SQLAlchemy 2.0** | Typed models, foreign keys, indexes, transactions |
| Database | **PostgreSQL** (prod) / **SQLite** (local) | Relational fits transactional booking; one env var switches between them |
| Auth | **PyJWT + bcrypt** | Stateless JWT; bcrypt-hashed passwords |
| Tests | **pytest** | Fast, isolated unit tests on the business logic |

**Why Python (the brief suggested Node/Express):** the role's JD lists *"Node.js
or any backend language (Python, Java, etc.)"*, so Python is in scope. FastAPI in
particular maps cleanly onto the evaluation criteria — Pydantic gives first-class
validation, and the auto-generated OpenAPI docs make the API trivial to test and
review.

**Why a relational DB (the brief offered MongoDB *or* MySQL):** booking is
inherently transactional. A **partial unique index** enforces "no double-booking"
at the database level, and **row-level locking** prevents two concurrent requests
from overselling the same slot — both natural in SQL. SQLite is used locally so
the project runs with no database setup at all.

---

## Project structure

```
playgg-booking-api/
├── app/
│   ├── main.py                # FastAPI app, router wiring, startup (create tables + seed)
│   ├── config.py              # env-driven settings (DATABASE_URL, JWT, slot window)
│   ├── database.py            # engine, session factory, declarative Base
│   ├── seed.py                # sample cafes + demo admin (idempotent)
│   ├── models/                # SQLAlchemy models
│   │   ├── cafe.py
│   │   ├── booking.py         # incl. partial unique index for no-double-booking
│   │   └── user.py
│   ├── schemas/               # Pydantic request/response models
│   │   ├── cafe.py
│   │   ├── booking.py
│   │   └── auth.py
│   ├── services/
│   │   └── booking_service.py # ← core business logic (unit-tested in isolation)
│   ├── routers/               # HTTP layer
│   │   ├── cafes.py
│   │   ├── bookings.py
│   │   └── auth.py
│   └── core/
│       ├── errors.py          # custom exception + consistent JSON error envelope
│       └── security.py        # bcrypt hashing + JWT issue/verify
├── tests/
│   └── test_bookings.py       # 13 unit tests
├── requirements.txt
├── Dockerfile
├── render.yaml                # one-click Render blueprint (web service + Postgres)
├── Procfile
├── .env.example
└── postman_collection.json
```

The HTTP layer (`routers`) is kept thin; all rules live in `services/booking_service.py`,
which is why the logic can be unit-tested without a running server.

---

## Quick start (local)

**Prerequisites:** Python 3.11+ (developed on 3.13). No database needed — it uses
SQLite out of the box.

```bash
# 1. Clone
git clone https://github.com/Evil-Bane/playgg-booking-api.git
cd playgg-booking-api

# 2. Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
uvicorn app.main:app --reload
```

The API is now at **http://127.0.0.1:8000**. On first start it creates the tables
and seeds 6 sample cafes plus a demo admin user.

- Swagger UI: **http://127.0.0.1:8000/docs**
- ReDoc: **http://127.0.0.1:8000/redoc**

---

## Configuration

All settings have safe defaults (see [.env.example](.env.example)); copy it to
`.env` to override.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./playgg.db` | Set to a Postgres URL in production |
| `JWT_SECRET` | `change-me-in-production` | Secret used to sign JWTs |
| `JWT_EXPIRE_MINUTES` | `60` | Token lifetime |
| `ADMIN_USERNAME` | `admin` | Seeded demo user |
| `ADMIN_PASSWORD` | `admin` | Seeded demo password |
| `OPENING_HOUR` / `CLOSING_HOUR` | `10` / `22` | Window used to generate hourly slots |

---

## API reference

Base URL: `http://127.0.0.1:8000`

| Method | Endpoint | Auth | Description |
|---|---|:---:|---|
| `GET` | `/cafes` | — | List cafes. Query: `city`, `page`, `limit` |
| `GET` | `/cafes/{id}` | — | Get a single cafe |
| `GET` | `/cafes/{id}/availability?date=YYYY-MM-DD` | — | Open seats per slot for a date |
| `POST` | `/cafes` | 🔐 | Add a cafe (admin convenience) |
| `POST` | `/bookings` | 🔐 | Create a booking |
| `GET` | `/bookings/{cafe_id}` | — | All bookings for a cafe |
| `DELETE` | `/bookings/{id}` | 🔐 | Cancel a booking |
| `POST` | `/login` | — | Exchange credentials for a JWT |
| `GET` | `/health` | — | Health check |

### Auth flow

```bash
# 1. Log in (demo admin) -> returns a JWT
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
# { "access_token": "eyJ...", "token_type": "bearer" }

# 2. Use the token on protected routes
TOKEN="eyJ..."
```

### Cafes

```bash
# List all
curl http://127.0.0.1:8000/cafes

# Filter by city (case-insensitive)
curl "http://127.0.0.1:8000/cafes?city=Jaipur"

# Paginate
curl "http://127.0.0.1:8000/cafes?page=1&limit=2"
```

```jsonc
// GET /cafes  ->  200
{
  "items": [
    { "id": 1, "name": "Nexus Arena", "location": "MI Road", "city": "Jaipur",
      "price_per_hour": 120.0, "total_seats": 20 }
  ],
  "total": 6, "page": 1, "limit": 10, "pages": 1
}
```

### Availability

```bash
curl "http://127.0.0.1:8000/cafes/1/availability?date=2026-12-25"
```

```jsonc
// 200
{
  "cafe_id": 1,
  "date": "2026-12-25",
  "slots": [
    { "time_slot": "10:00-11:00", "total_seats": 20, "booked_seats": 0, "available_seats": 20 },
    { "time_slot": "18:00-19:00", "total_seats": 20, "booked_seats": 5, "available_seats": 15 }
    // ...one entry per hourly slot
  ]
}
```

### Bookings

```bash
# Create (protected) — time_slot is an hourly window "HH:00-HH:00"
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cafe_id":1,"user_name":"alice","date":"2026-12-25","time_slot":"18:00-19:00","seats_booked":4}'

# List bookings for a cafe
curl http://127.0.0.1:8000/bookings/1

# Cancel (protected) — soft cancel, frees the seats
curl -X DELETE http://127.0.0.1:8000/bookings/1 -H "Authorization: Bearer $TOKEN"
```

```jsonc
// POST /bookings  ->  201
{
  "id": 1, "cafe_id": 1, "user_name": "alice", "date": "2026-12-25",
  "time_slot": "18:00-19:00", "seats_booked": 4, "status": "confirmed"
}
```

### Error format

Every error returns the same envelope and an HTTP status that matches the failure:

```jsonc
{ "error": { "code": "not_enough_seats",
             "message": "Only 15 seat(s) left for 18:00-19:00 on 2026-12-25; you requested 20." } }
```

| Status | Example `code` | When |
|---|---|---|
| `401` | `unauthorized`, `invalid_credentials`, `token_expired` | Missing/invalid token, bad login |
| `404` | `cafe_not_found`, `booking_not_found` | Unknown id |
| `409` | `double_booking`, `not_enough_seats`, `exceeds_total_seats`, `already_cancelled` | Conflicts with current state |
| `422` | `validation_error`, `invalid_slot`, `past_date` | Malformed or out-of-range input |

---

## Business logic & rules

- **A slot** is `(cafe, date, time_slot)`. Time slots are 1-hour windows within the
  cafe's operating hours (default `10:00`–`22:00`), e.g. `"18:00-19:00"`.
- **Capacity:** a booking succeeds only if
  `sum(seats_booked of active bookings for that slot) + requested ≤ cafe.total_seats`.
  Many users can share a slot up to capacity.
- **No double-booking:** the *same* user cannot hold two **active** bookings for the
  same slot. (Different users sharing a slot is expected — that's how capacity works.)
  Enforced both in the service layer and by a **partial unique index** in the DB.
- **Cancellation** is a **soft delete** (`status = "cancelled"`): the seats are
  released and the user may book the slot again, while history is preserved.
- **Concurrency:** booking runs in a transaction that row-locks the cafe (on
  Postgres) so two simultaneous requests can't oversell the same slot.

---

## Testing

```bash
pytest
```

13 unit tests cover the booking rules in isolation (in-memory SQLite, no server
needed): successful booking, capacity exceeded, request bigger than the cafe,
double-booking, multiple users sharing a slot, cancellation freeing seats,
rebooking after cancel, past dates, invalid slots, unknown cafe/booking, and the
availability calculation.

For manual/exploratory testing use **Swagger UI** at `/docs` or the included
**[Postman collection](postman_collection.json)** (its *Login* request auto-saves
the token for the protected calls).

---

## Deployment

### Render (recommended) — via the included blueprint

1. Push this repo to GitHub.
2. In Render: **New + → Blueprint**, point it at the repo. [`render.yaml`](render.yaml)
   provisions a free web service **and** a free Postgres database, wiring
   `DATABASE_URL` automatically and generating a `JWT_SECRET`.
3. Set `ADMIN_PASSWORD` in the dashboard, deploy, and visit `/docs`.

### Docker

```bash
docker build -t playgg-api .
docker run -p 8000:8000 -e DATABASE_URL="postgresql://…" playgg-api
```

> The app reads `$PORT` (Render/Railway set it automatically) and rewrites a
> legacy `postgres://` URL to `postgresql://` so managed-Postgres URLs work as-is.

---

## Design decisions & trade-offs

- **Layered architecture** (models / schemas / services / routers). Keeping the
  rules in a service layer makes them unit-testable without HTTP and keeps routers thin.
- **Postgres + SQLite split.** SQLite for a frictionless local run; Postgres for
  production durability. SQLAlchemy means the same code targets both.
- **`create_all()` on startup instead of migrations.** Fine for an assignment and
  keeps setup to one command. For a real deployment I'd add **Alembic** migrations.
- **Fixed global slot window.** The brief's `Cafe` entity has no opening/closing
  hours, so slots come from a configurable global window rather than per-cafe hours
  — a deliberate trade-off to stay faithful to the given schema. Per-cafe hours
  would be a small, natural extension.
- **`GET /bookings/{cafe_id}` path.** Implemented exactly as the brief specifies,
  even though a more RESTful form would be `GET /cafes/{id}/bookings`.
- **Soft cancellation** over hard delete — releases seats while preserving history
  for auditing.
- **Note on SQLite + free hosting:** Render's free filesystem is ephemeral, so for
  the hosted demo a (free) Postgres instance is used; data survives restarts.

---

## What I'd add with more time

- Alembic migrations and a `docker-compose` with Postgres for local parity
- User registration + roles (cafe-owner vs customer) instead of a single seeded admin
- Per-cafe operating hours and configurable slot lengths
- A booking-update endpoint and richer pagination metadata (next/prev links)
- Rate limiting on auth, and a CI workflow running the test suite on every push
