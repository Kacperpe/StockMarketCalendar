from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AccountStatus, BrokerProvider


class AccountCreate(BaseModel):
    provider: BrokerProvider
    name: str = Field(min_length=1, max_length=120)
    currency: str = Field(min_length=1, max_length=16)


class AccountOut(BaseModel):
    id: int
    user_id: int
    provider: BrokerProvider
    name: str
    currency: str
    status: AccountStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class MT5ConnectResponse(BaseModel):
    account_id: int
    ingest_key: str
    api_url: str
    instructions: list[str]


class CTraderConnectResponse(BaseModel):
    account_id: int
    oauth_url: str
    state: str
    note: str

