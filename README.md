LedgerX is a payment processing backend designed to demonstrate how financial transactions can be handled with consistency, traceability and controlled access.

Unlike a basic CRUD application, LedgerX focuses on the engineering challenges involved in transferring money between wallets.

The system implements:

Wallet-based financial transactions.

Atomic database operations with rollback on failure.

Idempotency keys to prevent duplicate payment processing.

Double-entry ledger records for transaction traceability.

JWT-based authentication and password hashing.

Ownership-based authorization for wallet operations.

A dashboard interface for interacting with wallet and transaction data.

Automated tests for critical financial operations.

Core engineering objective: A payment should either complete all its required database changes or leave the financial state unchanged.

2. System Architecture

                 CLIENT
                   |
          Dashboard / API Client
                   |
                   v
             FASTAPI LAYER
                   |
          Authentication & Access
                   |
                   v
             SERVICE LAYER
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
    Wallet     Transfer    Idempotency
   Management  Processing     Check
       |           |           |
       +-----------+-----------+
                   |
                   v
             SQLALCHEMY ORM
                   |
                   v
               SQLITE DB
                   |
          +--------+--------+
          |        |        |
          v        v        v
        Users   Wallets  Transactions
                            |
                            v
                       Ledger Entries

Architecture responsibilities

Layer

Responsibility

API layer

HTTP endpoints, request validation and response handling

Authentication

Password verification, JWT generation and token validation

Service layer

Financial business rules and transaction execution

ORM layer

Database interaction through SQLAlchemy

Database

Persistent users, wallets, transactions and ledger records

Frontend

Wallet dashboard and transaction interaction

3. Key Engineering Features

A. Idempotent Payment Processing

Network failures and client retries can cause the same payment request to be submitted multiple times.

LedgerX uses an idempotency key to identify previously processed transfer requests.

Example:

Request 1:
POST /transfers
Idempotency-Key: payment-123

Result:
Transaction created successfully.

Request 2:
POST /transfers
Idempotency-Key: payment-123

Result:
Previously processed transaction returned.

Reusing the same key with a different transaction payload is rejected.

This prevents duplicate execution when clients retry requests.

B. Double-Entry Ledger

Every successful transfer produces two ledger records:

DEBIT — amount deducted from the sender's wallet.

CREDIT — amount added to the receiver's wallet.

For a transfer of ₹500:

Wallet

Entry

Amount

Sender

DEBIT

₹500

Receiver

CREDIT

₹500

The transaction is represented through linked ledger entries, making financial operations easier to trace and audit.

C. Transaction Atomicity and Rollback

Financial operations must not leave partially updated wallet balances.

LedgerX uses SQLAlchemy database transactions.

A successful transfer performs:

Validate sender and receiver wallets.

Check available balance.

Deduct money from the sender.

Credit the receiver.

Create the transaction record.

Create debit and credit ledger entries.

Commit the database transaction.

If an operation fails, the transaction is rolled back.

try:
    # Update wallet balances
    # Create transaction
    # Create ledger entries

    db.commit()

except Exception:
    db.rollback()
    raise

This ensures that a failed operation does not leave partially committed financial changes within the transaction.

D. Authentication and Authorization

LedgerX implements authentication using:

Argon2-backed password hashing through pwdlib.

JSON Web Tokens (JWT).

PyJWT for token creation and validation.

OAuth2 password-bearer authentication.

User ownership checks for protected wallet operations.

Passwords are stored as hashes rather than plaintext.

Protected endpoints validate the JWT and restrict wallet access to the authenticated user.

E. Financial Validation

The application enforces important business rules:

Transfer amount must be greater than zero.

Wallet balance cannot become negative.

Sender and receiver must be different wallets.

Sender must own the wallet used to initiate a transfer.

Users cannot access wallets belonging to other users.

Duplicate idempotency keys cannot execute a transfer twice.

4. Technology Stack

Technology

Purpose

Python 3.12

Core programming language

FastAPI

REST API framework

SQLAlchemy

ORM and database transaction management

SQLite

Persistent relational database

Pydantic

Request validation and data schemas

PyJWT

JWT generation and validation

pwdlib + Argon2

Password hashing

python-dotenv

Environment variable management

Pytest

Automated testing

HTML, CSS, JavaScript

Dashboard frontend

Chart.js

Dashboard data visualization

5. Project Structure

LedgerX/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   └── security.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── tests/
│   ├── __init__.py
│   └── test_services.py
│
├── check_ledger.py
├── migrate_auth.py
├── migrate_db.py
├── requirements.txt
├── .gitignore
└── README.md

Important modules

main.py — API routes and dependency injection.

models.py — SQLAlchemy database models.

schemas.py — Pydantic request and response schemas.

services.py — Wallet funding and transfer business logic.

security.py — Password hashing, JWT creation and authentication.

database.py — Database engine, session management and ORM configuration.

test_services.py — Tests for financial service operations.

6. API Endpoints

Method

Endpoint

Description

Access

GET

/

Home endpoint

Public

GET

/health

Health check

Public

POST

/users

Register a user and create wallet

Public

POST

/login

Authenticate and obtain JWT

Public

GET

/wallets

Retrieve authenticated user's wallets

Protected

GET

/wallets/{wallet_id}

Retrieve an owned wallet

Protected

GET

/wallets/{wallet_id}/transactions

Retrieve wallet transactions

Protected

POST

/wallets/fund

Add funds to an owned wallet

Protected

POST

/transfers

Transfer funds between wallets

Protected

Interactive API documentation is available through FastAPI Swagger UI at /docs.

7. Testing and Reliability

LedgerX includes automated tests for critical financial operations.

Current service test coverage includes:

Test scenario

Expected behaviour

Successful transfer

Both wallet balances update correctly

Duplicate request

Previously processed payment is not executed again

Reused key with different amount

Request rejected

Insufficient balance

Transfer rejected

Same sender and receiver

Transfer rejected

Double-entry ledger

Debit and credit entries created

Simulated database failure

Changes rolled back

Run the test suite:

python -m pytest -v

The service test suite has previously passed all 7 implemented tests.

8. Local Setup

Prerequisites

Python 3.12+

Git

pip

Clone the repository

git clone https://github.com/dharshanth0504/LedgerX.git
cd LedgerX

Create a virtual environment

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Install dependencies

pip install -r requirements.txt

Configure environment variables

Create a .env file in the project root:

JWT_SECRET_KEY=your_generated_secret_key

Generate a secure secret locally:

python -c "import secrets; print(secrets.token_urlsafe(32))"

Never commit .env or expose your JWT secret.

Start the application

uvicorn app.main:app --reload

Open:

Dashboard: http://127.0.0.1:8000/dashboard

API documentation: http://127.0.0.1:8000/docs

Health check: http://127.0.0.1:8000/health

9. Engineering Decisions and Trade-offs

Why FastAPI?

FastAPI provides request validation, dependency injection, automatic OpenAPI documentation and a clean structure for building REST APIs.

Why SQLAlchemy?

SQLAlchemy separates business logic from database implementation and provides transaction management through database sessions.

Why Idempotency?

Payment requests can be retried because of timeouts or network failures. Idempotency protects against duplicate execution.

Why a Ledger?

Wallet balances alone do not provide a complete transaction history. Ledger entries provide a traceable representation of debits and credits.

Why SQLite initially?

SQLite keeps local development and testing simple. However, it is not the final database choice for a high-concurrency payment system.

10. Current Limitations and Future Improvements

LedgerX is an educational backend engineering project, not a production payment gateway.

The following improvements are planned:

Migrate from SQLite to PostgreSQL.

Implement robust concurrent wallet updates using database-level locking.

Add concurrent transfer and double-spend prevention tests.

Complete frontend JWT authentication integration.

Add integration tests for authentication and authorization.

Add structured logging and request correlation IDs.

Introduce Docker and containerized deployment.

Add CI/CD using GitHub Actions.

Add monitoring and operational health metrics.

Introduce rate limiting and production-grade security controls.

Important: SQLite's transaction behaviour does not provide the row-level locking strategy needed for robust concurrent payment processing. Production-grade concurrency requires a database and transaction design that explicitly handles competing updates.

11. Project Goals

LedgerX was built to explore practical backend engineering concepts:

Designing RESTful APIs.

Structuring applications using service layers.

Managing relational data and database transactions.

Understanding idempotency in payment systems.

Implementing ledger-based financial records.

Designing authentication and authorization.

Testing failure scenarios and rollback behaviour.

