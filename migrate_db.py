import sqlite3

connection = sqlite3.connect("ledgerx.db")

columns = [
    row[1]
    for row in connection.execute(
        "PRAGMA table_info(transactions)"
    )
]

if "idempotency_key" not in columns:
    connection.execute(
        "ALTER TABLE transactions ADD COLUMN idempotency_key VARCHAR(100)"
    )

connection.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
    uq_transactions_idempotency_key
    ON transactions(idempotency_key)
""")

connection.commit()
connection.close()

print("Database migration completed successfully!")