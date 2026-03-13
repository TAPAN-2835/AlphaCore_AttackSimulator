# Breach — Phishing Simulation Platform Backend

A production-quality **FastAPI** backend for the Breach security awareness platform, covering phishing campaign management, real-time event tracking, credential harvest simulation, and risk analytics.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 15 (async via asyncpg) |
| ORM / Migrations | SQLAlchemy 2 (async) + Alembic |
| Auth | JWT (HS256) + bcrypt |
| Background Jobs | FastAPI BackgroundTasks |
| Cache (optional) | Redis 7 |

---

## Project Structure

```
backend/
├── main.py                  # App factory, router registration
├── config.py                # Settings (pydantic-settings / .env)
├── database.py              # Async engine + session
│
├── auth/                    # JWT auth, user model, role guards
├── campaigns/               # Campaign CRUD, CSV target upload
├── simulation/              # Phishing link tracking, credential harvest, file download
├── events/                  # Central event logger + recent-events API
├── analytics/               # Risk engine + dashboard chart APIs
├── admin/                   # Overview stats + user management
├── ml/                      # ML model stub (drop-in interface)
│
├── alembic/                 # Database migrations
├── docker-compose.yml       # PostgreSQL + Redis
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Prerequisites

```bash
# Python 3.11+
python3 --version

# Docker (for PostgreSQL + Redis)
docker --version
```

### 2. Environment

```bash
cd backend
cp .env.example .env
# Edit .env — set a real SECRET_KEY in production
```

### 3. Start Database

```bash
docker-compose up -d
```

### 4. Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Run Migrations (optional — server auto-creates tables on startup for hackathon)

```bash
alembic upgrade head
```

### 6. Start Server

```bash
uvicorn main:app --reload --port 8000
```

> Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Overview

### Auth
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | Public | Create user account |
| POST | `/auth/login` | Public | Returns JWT + role |
| GET | `/auth/me` | Bearer | Current user profile |

### Campaigns
| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/campaigns/create` | Admin | Create phishing campaign |
| GET | `/campaigns/` | Analyst | List all campaigns |
| GET | `/campaigns/{id}` | Analyst | Campaign detail + targets |
| POST | `/campaigns/{id}/start` | Admin | Set campaign to running |
| POST | `/campaigns/upload-users` | Admin | Upload CSV of targets |
| DELETE | `/campaigns/{id}` | Admin | Delete campaign |

### Simulation Engine
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/sim/{token}` | Public | Track link click → serve fake login page |
| POST | `/sim/credential-submit` | Public | Log credential attempt (password **never** stored) |
| GET | `/sim/download/{token}` | Public | Return harmless drill ZIP |

### Analytics
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/analytics/overview` | Analyst | Click/credential/report rates + high-risk depts |
| GET | `/analytics/user/{id}` | Analyst | Per-user risk score + event breakdown |
| GET | `/analytics/click-rate` | Analyst | Click rate by department |
| GET | `/analytics/credential-rate` | Analyst | Credential rate by department |
| GET | `/analytics/campaign-trend` | Analyst | Historical event counts per campaign |

### Admin
| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/admin/dashboard` | Admin | KPI summary card data |
| GET | `/admin/recent-events` | Analyst | Latest N events (enriched) |
| GET | `/admin/users` | Admin | All users with risk levels |
| PUT | `/admin/users/{id}/role` | Admin | Change user role |

---

## Risk Score Formula

```
score = (clicks × 20) + (credential_attempts × 40) + (downloads × 30) − (reported × 15)
```

| Score | Level |
|---|---|
| 0 – 29 | LOW |
| 30 – 59 | MEDIUM |
| 60 – 79 | HIGH |
| 80 – 100 | CRITICAL |

The ML team can override `ml/risk_model.py → RiskModel.predict()` with a trained model.

---

## Security Design

- **Passwords**: bcrypt-hashed, never returned in API responses.
- **Phishing credentials**: Only the *existence* of an attempt is logged — the submitted username/password is **never stored**.
- **Simulation tokens**: UUID-based, expire after `TOKEN_EXPIRY_HOURS` (default 72 h), single-use.
- **Role enforcement**: All admin/analyst routes protected by JWT role guard at the FastAPI dependency layer.
- **Input validation**: All request bodies validated through Pydantic v2 models.

---

## Smoke Test (curl)

```bash
# 1. Register admin
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Admin","email":"admin@breach.io","password":"Test1234!","role":"admin"}' | python3 -m json.tool

# 2. Login & save token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@breach.io","password":"Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Dashboard
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/dashboard | python3 -m json.tool

# 4. Create campaign
curl -s -X POST http://localhost:8000/campaigns/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Q1 Finance Test","attack_type":"phishing","target_group":"finance"}' | python3 -m json.tool

# 5. Analytics overview
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/analytics/overview | python3 -m json.tool
```
