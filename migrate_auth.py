
import sqlite3

connection = sqlite3.connect("ledgerx.db")

columns = [
    row[1]
    for row in connection.execute(
        "PRAGMA table_info(users)"
    )
]

if "password_hash" not in columns:
    connection.execute(
        "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"
    )
    print("Password column added successfully!")
else:
    print("Password column already exists.")

connection.commit()
connection.close()

print("Authentication database migration completed!")
