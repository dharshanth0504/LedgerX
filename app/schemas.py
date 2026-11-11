
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class WalletResponse(BaseModel):
    id: int
    balance: Decimal
    currency: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    wallet: WalletResponse | None = None

    model_config = ConfigDict(from_attributes=True)

class TransferCreate(BaseModel):
    sender_wallet_id: int
    receiver_wallet_id: int
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )


class TransactionResponse(BaseModel):
    id: int
    sender_wallet_id: int
    receiver_wallet_id: int
    amount: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)

class FundingRequest(BaseModel):
    wallet_id: int
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )