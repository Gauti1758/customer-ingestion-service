import os
import requests
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.customer import Customer

FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://mock-server:5000")
PAGE_SIZE = 10  # how many records to fetch per Flask page


def fetch_all_customers_from_flask() -> list[dict]:
    """Paginate through the Flask /api/customers endpoint and collect all records."""
    all_customers = []
    page = 1

    while True:
        response = requests.get(
            f"{FLASK_BASE_URL}/api/customers",
            params={"page": page, "limit": PAGE_SIZE},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        data  = payload.get("data", [])
        total = payload.get("total", 0)

        all_customers.extend(data)

        # Stop when we've fetched all records
        if len(all_customers) >= total or not data:
            break

        page += 1

    return all_customers

def _parse_customer(record: dict) -> dict:
    """Convert raw JSON dict into typed values suitable for the DB."""
    dob_raw = record.get("date_of_birth")
    dob: date | None = None
    if dob_raw:
        dob = datetime.strptime(dob_raw, "%Y-%m-%d").date()

    created_raw = record.get("created_at")
    created_at: datetime | None = None
    if created_raw:
        # Accept both "2023-01-10T09:00:00" and "2023-01-10 09:00:00" formats
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                created_at = datetime.strptime(created_raw, fmt)
                break
            except ValueError:
                continue

    balance_raw = record.get("account_balance")
    balance: Decimal | None = Decimal(str(balance_raw)) if balance_raw is not None else None

    return {
        "customer_id":     record["customer_id"],
        "first_name":      record["first_name"],
        "last_name":       record["last_name"],
        "email":           record["email"],
        "phone":           record.get("phone"),
        "address":         record.get("address"),
        "date_of_birth":   dob,
        "account_balance": balance,
        "created_at":      created_at,
    }


def upsert_customers(db: Session, customers: list[dict]) -> int:
    """
    Upsert a list of customer dicts into PostgreSQL using ON CONFLICT DO UPDATE.
    Returns the number of records processed.
    """
    if not customers:
        return 0

    parsed = [_parse_customer(c) for c in customers]

    stmt = pg_insert(Customer).values(parsed)
    stmt = stmt.on_conflict_do_update(
        index_elements=["customer_id"],
        set_={
            "first_name":      stmt.excluded.first_name,
            "last_name":       stmt.excluded.last_name,
            "email":           stmt.excluded.email,
            "phone":           stmt.excluded.phone,
            "address":         stmt.excluded.address,
            "date_of_birth":   stmt.excluded.date_of_birth,
            "account_balance": stmt.excluded.account_balance,
            "created_at":      stmt.excluded.created_at,
        },
    )

    db.execute(stmt)
    db.commit()
    return len(parsed)


def run_ingestion(db: Session) -> int:
    """Full pipeline: fetch from Flask → upsert into PostgreSQL."""
    customers = fetch_all_customers_from_flask()
    return upsert_customers(db, customers)
