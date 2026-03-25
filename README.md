# Customer Data Pipeline

A 3-service Docker data pipeline built with Flask, FastAPI, and PostgreSQL.

## Architecture

```
Flask Mock Server (port 5000)
        │
        │  JSON over HTTP (paginated)
        ▼
FastAPI Pipeline Service (port 8000)
        │
        │  SQLAlchemy upsert
        ▼
PostgreSQL Database (port 5432)
```

## Prerequisites

- Docker Desktop (running)
- docker-compose v2+

## Quick Start

```bash
# 1. Clone / unzip the project
cd project-root

# 2. Start all 3 services
docker-compose up -d --build

# 3. Wait ~10 seconds for services to be healthy, then test
```

## Testing

### Flask Mock Server (port 5000)
```bash
# Health check
curl http://localhost:5000/api/health

# Paginated customer list
curl "http://localhost:5000/api/customers?page=1&limit=5"

# Single customer
curl http://localhost:5000/api/customers/CUST001
```

### FastAPI Pipeline Service (port 8000)
```bash
# Ingest all customers from Flask → PostgreSQL
curl -X POST http://localhost:8000/api/ingest

# Paginated customers from DB
curl "http://localhost:8000/api/customers?page=1&limit=5"

# Single customer from DB
curl http://localhost:8000/api/customers/CUST001
```

### Interactive API Docs
- FastAPI Swagger UI: http://localhost:8000/docs
- FastAPI ReDoc:      http://localhost:8000/redoc

## Project Structure

```
project-root/
├── docker-compose.yml
├── README.md
├── mock-server/
│   ├── app.py                  # Flask REST API
│   ├── data/customers.json     # 22 sample customers
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-service/
    ├── main.py                 # FastAPI app + endpoints
    ├── database.py             # SQLAlchemy engine + session
    ├── models/
    │   └── customer.py         # Customer ORM model
    ├── services/
    │   └── ingestion.py        # Fetch + upsert logic
    ├── Dockerfile
    └── requirements.txt
```

## API Reference

### Flask Mock Server

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/customers?page=1&limit=10` | Paginated customer list |
| GET | `/api/customers/{id}` | Single customer or 404 |

### FastAPI Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/ingest` | Fetch from Flask → upsert to DB |
| GET | `/api/customers?page=1&limit=10` | Paginated customers from DB |
| GET | `/api/customers/{id}` | Single customer from DB or 404 |

## Stopping Services

```bash
docker-compose down          # stop containers
docker-compose down -v       # stop + remove volumes (wipes DB)
```
