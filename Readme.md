# Microservices Assignment — Software Design 2026

A simplified distributed system demonstrating resiliency patterns:
**Circuit Breaker**, **Graceful Degradation**, and **Strict Timeouts**.

---

## Architecture

```
Client
  │
  ▼
API Gateway        (port 5000)  — routes all requests
  │
  ▼
Movie Service      (port 5001)  — fetches movie from DB, calls Recommendation Service
  │                               implements Circuit Breaker + fallback
  ▼
Recommendation     (port 5002)  — returns recommended movie IDs from DB
Service                           supports CHAOS_MODE for failure simulation
  │
  ▼
SQLite DB          (movies.db)  — shared database, auto-created on first run
```

---

## Setup

Install dependencies for each service:

```bash
cd api_gateway           && pip install -r requirements.txt && cd ..
cd movie_service         && pip install -r requirements.txt && cd ..
cd recommendation_service && pip install -r requirements.txt && cd ..
```

> SQLite is built into Python — no extra database installation needed.

---

## Running the Services

Open **three separate terminals**:

**Terminal 1 — Recommendation Service (normal)**
```bash
cd recommendation_service
python app.py
```

**Terminal 2 — Movie Service**
```bash
cd movie_service
python app.py
```

**Terminal 3 — API Gateway**
```bash
cd api_gateway
python app.py
```

---

## Testing

### Normal request
```bash
curl http://localhost:5000/movie/1
```

Expected response:
```json
{
  "movie": { "id": 1, "title": "The Dark Knight", "description": "..." },
  "similar_movies": [...],
  "source": "recommendation_service",
  "circuit": { "state": "closed", "failures": 0 }
}
```

### Enable Chaos Mode
Stop Terminal 1 and restart with:
```bash
CHAOS_MODE=1 python app.py
```

Now spam requests:
```bash
for i in $(seq 1 10); do curl -s http://localhost:5000/movie/1 | python3 -m json.tool; done
```

You will observe:
1. Some requests return `"source": "fallback"` (503 or timeout from chaos)
2. After **3 failures**, `"circuit": { "state": "open" }` — circuit trips
3. All subsequent requests return fallback immediately (no call to Service B)
4. After **10 seconds**, circuit moves to half-open and retries

### Check circuit state directly
```bash
curl http://localhost:5000/circuit-status
```

---

## Resiliency Patterns Implemented

| Pattern | Implementation |
|---|---|
| **Circuit Breaker** | Trips after 3 consecutive failures; recovers after 10 s |
| **Strict Timeout** | 1.5 s hard timeout on all Recommendation Service calls |
| **Graceful Degradation** | Falls back to Inception, Interstellar, The Matrix from DB |
| **Chaos Mode** | 50% chance of 503 OR 3–10 s latency spike via `CHAOS_MODE=1` |

---

## Database Schema

**movies** — stores all movie data (used by Movie Service)
```
id | title | description
```

**recommendations** — stores per-movie recommendation pairs (used by Recommendation Service)
```
movie_id | recommended_movie_id
```

The database (`movies.db`) is created automatically in the project root on first run with 10 seeded movies and their recommendation pairs.