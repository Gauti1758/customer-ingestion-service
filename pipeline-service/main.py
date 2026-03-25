from fastapi import FastAPI, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from database import get_db, init_db
from models.customer import Customer
from services.ingestion import run_ingestion

app = FastAPI(
    title="Customer Data Pipeline",
    description="Ingests customer data from Flask mock server into PostgreSQL",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    """Create DB tables automatically on startup."""
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "pipeline-service"}


@app.post("/api/ingest")
def ingest(db: Session = Depends(get_db)):
    """
    Fetch all customers from the Flask mock server (auto-paginated)
    and upsert them into PostgreSQL.
    """
    try:
        records_processed = run_ingestion(db)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ingestion failed: {str(exc)}")

    return {"status": "success", "records_processed": records_processed}


@app.get("/api/customers")
def list_customers(
    page:  int = Query(1,  ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
):
    """Return a paginated list of customers stored in the database."""
    total  = db.query(Customer).count()
    offset = (page - 1) * limit
    rows   = db.query(Customer).offset(offset).limit(limit).all()

    return {
        "data":  [r.to_dict() for r in rows],
        "total": total,
        "page":  page,
        "limit": limit,
    }


@app.get("/api/customers/{customer_id}")
def get_customer(
    customer_id: str = Path(
        ...,
        description="Unique ID of the customer",
        example="CUST001"
    ),
    db: Session = Depends(get_db)):
    """Return a single customer by ID or 404."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    return customer.to_dict()
