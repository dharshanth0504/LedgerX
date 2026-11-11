
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Wallet, Transaction, LedgerEntry


def transfer_money(
    db: Session,
    sender_wallet_id: int,
    receiver_wallet_id: int,
    amount: Decimal,
    idempotency_key: str
):

    # 1. Prevent transferring to the same wallet
    existing_transaction = db.query(Transaction).filter(
        Transaction.idempotency_key == idempotency_key
    ).first()

    if existing_transaction:
        if (
            existing_transaction.sender_wallet_id != sender_wallet_id
            or existing_transaction.receiver_wallet_id != receiver_wallet_id
            or existing_transaction.amount != amount
        ):
            raise HTTPException(
                status_code=409,
                detail="Idempotency key already used for a different request"
            )

        return existing_transaction
    if sender_wallet_id == receiver_wallet_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot transfer money to the same wallet"
        )

    # 2. Find sender wallet
    sender = db.query(Wallet).filter(
        Wallet.id == sender_wallet_id
    ).first()

    if not sender:
        raise HTTPException(
            status_code=404,
            detail="Sender wallet not found"
        )

    # 3. Find receiver wallet
    receiver = db.query(Wallet).filter(
        Wallet.id == receiver_wallet_id
    ).first()

    if not receiver:
        raise HTTPException(
            status_code=404,
            detail="Receiver wallet not found"
        )

    # 4. Check sender balance
    if sender.balance < amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient wallet balance"
        )

    try:
        # 5. Update wallet balances
        sender.balance -= amount
        receiver.balance += amount

        # 6. Create transaction record
        transaction = Transaction(
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet_id,
            amount=amount,
            status="COMPLETED",
            idempotency_key=idempotency_key
        )

        db.add(transaction)
        db.flush()

        # 7. Create double-entry ledger records
        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            wallet_id=sender_wallet_id,
            entry_type="DEBIT",
            amount=amount
        )

        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            wallet_id=receiver_wallet_id,
            entry_type="CREDIT",
            amount=amount
        )

        db.add_all([debit_entry, credit_entry])

        # 8. Commit everything together
        db.commit()
        db.refresh(transaction)

        return transaction

    except Exception:
        db.rollback()
        raise

def fund_wallet(db: Session, wallet_id: int, amount: Decimal):

    # 1. Find the wallet receiving the funds
    receiver = db.query(Wallet).filter(
        Wallet.id == wallet_id
    ).first()

    if not receiver:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )

    try:
        # 2. Find the internal system wallet
        system_wallet = db.query(Wallet).filter(
            Wallet.user_id.is_(None)
        ).first()

        # 3. Create it if it does not exist
        if not system_wallet:
            system_wallet = Wallet(
                user_id=None,
                balance=Decimal("1000000000.00"),
                currency="INR"
            )
            db.add(system_wallet)
            db.flush()

        # 4. Check system wallet funds
        if system_wallet.currency != receiver.currency:
            raise HTTPException(
                status_code=400,
                detail="Currency mismatch"
            )

        if system_wallet.balance < amount:
            raise HTTPException(
                status_code=400,
                detail="System wallet has insufficient funds"
            )

        # 5. Update balances
        system_wallet.balance -= amount
        receiver.balance += amount

        # 6. Record the funding transaction
        transaction = Transaction(
            sender_wallet_id=system_wallet.id,
            receiver_wallet_id=receiver.id,
            amount=amount,
            status="COMPLETED"
        )

        db.add(transaction)
        db.flush()

        # 7. Record both ledger entries
        db.add_all([
            LedgerEntry(
                transaction_id=transaction.id,
                wallet_id=system_wallet.id,
                entry_type="DEBIT",
                amount=amount
            ),
            LedgerEntry(
                transaction_id=transaction.id,
                wallet_id=receiver.id,
                entry_type="CREDIT",
                amount=amount
            )
        ])

        # 8. Save everything together
        db.commit()
        db.refresh(transaction)

        return transaction

    except Exception:
        db.rollback()
        raise