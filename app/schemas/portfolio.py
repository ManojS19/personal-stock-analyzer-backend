from pydantic import BaseModel
from typing import List

class PortfolioHolding(BaseModel):
    symbol: str
    shares: float
    costBasis: float
    currentValue: float
    gain: float
    dayChange: float
    dayChangePercent: float
    yesterdayChange: float
    yesterdayChangePercent: float

class PortfolioResponse(BaseModel):
    holdings: List[PortfolioHolding]

class AddPortfolioRequest(BaseModel):
    symbol: str
    shares: float
    cost_basis: float

class UpdatePortfolioRequest(BaseModel):
    shares: float
    cost_basis: float

class AngelOneConnectRequest(BaseModel):
    client_code: str
    pin: str
    totp: str
    api_key: str | None = None
    client_local_ip: str | None = None
    client_public_ip: str | None = None
    mac_address: str | None = None
    sync: bool = False
    replace: bool = False

class AngelOneHolding(BaseModel):
    symbol: str
    shares: float
    averagePrice: float

class AngelOneSyncResponse(BaseModel):
    synced: bool
    holdings: List[AngelOneHolding]
