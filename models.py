"""
Data models and schemas for EnergyChain Platform
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    PRODUCER = "producer"
    CONSUMER = "consumer"
    BOTH = "both"


class TradeStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    role: UserRole = UserRole.BOTH
    location_lat: float = Field(..., ge=-90, le=90)
    location_lng: float = Field(..., ge=-180, le=180)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class EnergyData(BaseModel):
    user_id: int
    production_kwh: float = Field(..., ge=0)
    consumption_kwh: float = Field(..., ge=0)
    battery_level: Optional[float] = Field(None, ge=0, le=100)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EnergyDataResponse(EnergyData):
    net_energy: float
    surplus: bool
    
    class Config:
        from_attributes = True


class TradeCreate(BaseModel):
    seller_id: int
    buyer_id: int
    energy_amount: float = Field(..., gt=0)
    price_per_kwh: float = Field(..., gt=0)
    duration_hours: float = Field(..., gt=0)


class TradeResponse(BaseModel):
    id: int
    seller_id: int
    buyer_id: int
    energy_amount: float
    price_per_kwh: float
    total_price: float
    status: TradeStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LedgerEntry(BaseModel):
    transaction_id: int
    trade_id: int
    seller_id: int
    buyer_id: int
    energy_amount: float
    price: float
    timestamp: datetime
    hash: str
    previous_hash: str


class PricePrediction(BaseModel):
    current_price: float
    predicted_price_1h: float
    predicted_price_6h: float
    predicted_price_24h: float
    confidence_score: float
    factors: List[str]


class AnalyticsResponse(BaseModel):
    user_id: int
    total_production: float
    total_consumption: float
    total_trades: int
    earnings: float
    savings: float
    carbon_offset_kg: float
    predictions: PricePrediction
