
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    wallet = relationship(
        "Wallet",
        back_populates="owner",
        uselist=False
    )


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    balance = Column(Numeric(12, 2), default=0, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)

    __table_args__ = (
        CheckConstraint("balance >= 0", name="check_wallet_balance"),
    )

    owner = relationship("User", back_populates="wallet")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(100), unique=True, nullable=True)
    sender_wallet_id = Column(
        Integer,
        ForeignKey("wallets.id"),
        nullable=False
    )
    receiver_wallet_id = Column(
        Integer,
        ForeignKey("wallets.id"),
        nullable=False
    )
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="COMPLETED", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_transaction_amount"),
        CheckConstraint(
            "sender_wallet_id != receiver_wallet_id",
            name="check_different_wallets"
        ),
    )


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id"),
        nullable=False
    )
    wallet_id = Column(
        Integer,
        ForeignKey("wallets.id"),
        nullable=False
    )
    entry_type = Column(String(10), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('DEBIT', 'CREDIT')",
            name="check_entry_type"
        ),
        CheckConstraint("amount > 0", name="check_ledger_amount"),
    )
