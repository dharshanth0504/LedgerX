
import pytest

from decimal import Decimal
from fastapi import HTTPException

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Wallet, LedgerEntry, Transaction
from app.services import transfer_money


# Create a separate in-memory database for testing
@pytest.fixture
def db():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


# Create two wallets for every test
@pytest.fixture
def wallets(db):
    sender = Wallet(
        balance=Decimal("600.00"),
        currency="INR"
    )

    receiver = Wallet(
        balance=Decimal("300.00"),
        currency="INR"
    )

    db.add_all([sender, receiver])
    db.commit()

    db.refresh(sender)
    db.refresh(receiver)

    return sender, receiver


# Test 1: Successful transfer
def test_successful_transfer(db, wallets):
    sender, receiver = wallets

    transaction = transfer_money(
        db,
        sender.id,
        receiver.id,
        Decimal("100.00"),
        "test-key-001"
    )

    db.refresh(sender)
    db.refresh(receiver)

    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("400.00")
    assert transaction.status == "COMPLETED"


# Test 2: Duplicate request should not transfer twice
def test_duplicate_transfer(db, wallets):
    sender, receiver = wallets

    first = transfer_money(
        db, sender.id, receiver.id,
        Decimal("100.00"), "test-key-002"
    )

    second = transfer_money(
        db, sender.id, receiver.id,
        Decimal("100.00"), "test-key-002"
    )

    db.refresh(sender)
    db.refresh(receiver)

    assert first.id == second.id
    assert sender.balance == Decimal("500.00")
    assert receiver.balance == Decimal("400.00")


# Test 3: Same key with different amount should fail
def test_idempotency_key_reuse_with_different_amount(db, wallets):
    sender, receiver = wallets

    transfer_money(
        db, sender.id, receiver.id,
        Decimal("100.00"), "test-key-003"
    )

    with pytest.raises(HTTPException) as error:
        transfer_money(
            db, sender.id, receiver.id,
            Decimal("200.00"), "test-key-003"
        )

    assert error.value.status_code == 409


# Test 4: Insufficient balance should fail
def test_insufficient_balance(db, wallets):
    sender, receiver = wallets

    with pytest.raises(HTTPException) as error:
        transfer_money(
            db, sender.id, receiver.id,
            Decimal("1000.00"), "test-key-004"
        )

    assert error.value.status_code == 400


# Test 5: Same-wallet transfer should fail
def test_same_wallet_transfer(db, wallets):
    sender, receiver = wallets

    with pytest.raises(HTTPException) as error:
        transfer_money(
            db, sender.id, sender.id,
            Decimal("100.00"), "test-key-005"
        )

    assert error.value.status_code == 400


# Test 6: Transfer should create DEBIT and CREDIT entries
def test_double_entry_ledger(db, wallets):
    sender, receiver = wallets

    transaction = transfer_money(
        db, sender.id, receiver.id,
        Decimal("100.00"), "test-key-006"
    )

    entries = db.query(LedgerEntry).filter(
        LedgerEntry.transaction_id == transaction.id
    ).all()

    assert len(entries) == 2

    entry_types = {
        (entry.wallet_id, entry.entry_type, entry.amount)
        for entry in entries
    }

    assert entry_types == {
        (sender.id, "DEBIT", Decimal("100.00")),
        (receiver.id, "CREDIT", Decimal("100.00"))
    }

# Test 7: Failed database operation should roll back the transfer
def test_transfer_rollback(db, wallets):
    sender, receiver = wallets

    # Save the original balances
    original_sender_balance = sender.balance
    original_receiver_balance = receiver.balance

    # Force a database error by using an invalid status value
    from unittest.mock import patch

    with patch(
        "app.services.Transaction",
        side_effect=Exception("Simulated database failure")
    ):
        with pytest.raises(Exception):
            transfer_money(
                db,
                sender.id,
                receiver.id,
                Decimal("100.00"),
                "test-key-007"
            )

    # Refresh wallets from the database
    db.refresh(sender)
    db.refresh(receiver)

    # Balances must remain unchanged
    assert sender.balance == original_sender_balance
    assert receiver.balance == original_receiver_balance

    # No transaction should have been saved
    assert db.query(Transaction).filter(
        Transaction.idempotency_key == "test-key-007"
    ).first() is None

