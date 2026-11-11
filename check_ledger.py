from app.database import SessionLocal
from app.models import LedgerEntry

db = SessionLocal()

entries = db.query(LedgerEntry).filter(
    LedgerEntry.transaction_id == 4
).all()

for entry in entries:
    print(
        "Transaction:", entry.transaction_id,
        "| Wallet:", entry.wallet_id,
        "| Type:", entry.entry_type,
        "| Amount:", entry.amount
    )

db.close()