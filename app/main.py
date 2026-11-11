from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.services import fund_wallet, transfer_money
from fastapi import Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)


from app.database import get_db
from app.models import User, Wallet, Transaction, LedgerEntry
from app.schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    FundingRequest,
    TransferCreate,
    TransactionResponse
)
from fastapi import FastAPI

from app.database import engine, Base


# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LedgerX",
    description="Reliability-focused payment processing backend",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to LedgerX Payment System",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):

    # Check whether email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Create user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(new_user)
    db.flush()

    # Create wallet for the user
    new_wallet = Wallet(user_id=new_user.id)

    db.add(new_wallet)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/login", response_model=Token)
def login(
    login_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Swagger sends the email in the username field
    user = db.query(User).filter(
        User.email == login_data.username
    ).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }



@app.post(
    "/wallets/fund",
    response_model=TransactionResponse,
    status_code=201
)
def add_funds(
    funding_data: FundingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = db.query(Wallet).filter(
        Wallet.id == funding_data.wallet_id,
        Wallet.user_id == current_user.id
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )

    return fund_wallet(
        db,
        funding_data.wallet_id,
        funding_data.amount
    )

@app.post(
    "/transfers",
    response_model=TransactionResponse,
    status_code=201
)
def create_transfer(
    transfer_data: TransferCreate,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=100
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify that the sender wallet belongs to logged-in user
    sender_wallet = db.query(Wallet).filter(
        Wallet.id == transfer_data.sender_wallet_id,
        Wallet.user_id == current_user.id
    ).first()

    if not sender_wallet:
        raise HTTPException(
            status_code=404,
            detail="Sender wallet not found"
        )

    return transfer_money(
        db,
        transfer_data.sender_wallet_id,
        transfer_data.receiver_wallet_id,
        transfer_data.amount,
        idempotency_key
    )




@app.get("/wallets")
def get_all_wallets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallets = db.query(Wallet).filter(
        Wallet.user_id == current_user.id
    ).all()

    return [
        {
            "wallet_id": wallet.id,
            "user_id": wallet.user_id,
            "balance": wallet.balance,
            "currency": wallet.currency
        }
        for wallet in wallets
    ]


@app.get("/wallets/{wallet_id}")
def get_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )

    return {
        "wallet_id": wallet.id,
        "balance": wallet.balance,
        "currency": wallet.currency
    }

@app.get(
    "/wallets/{wallet_id}/transactions",
    response_model=list[TransactionResponse]
)
def get_wallet_transactions(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )

    transactions = db.query(Transaction).filter(
        (Transaction.sender_wallet_id == wallet_id) |
        (Transaction.receiver_wallet_id == wallet_id)
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return transactions
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend"
)
