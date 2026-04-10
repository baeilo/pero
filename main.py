"""
EnergyChain - Smart Energy Trading Platform
Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from models import (
    UserCreate, UserResponse, EnergyData, EnergyDataResponse,
    TradeCreate, TradeResponse, LedgerEntry, PricePrediction,
    AnalyticsResponse, UserRole, TradeStatus
)
from pricing_engine import PricingEngine
from ledger import EnergyLedger
from energy_trading import TradingEngine, EnergyTrade
from analytics import EnergyAnalytics

# Initialize FastAPI app
app = FastAPI(
    title="EnergyChain API",
    description="Decentralized Peer-to-Peer Energy Trading Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
pricing_engine = PricingEngine()
ledger = EnergyLedger()
trading_engine = TradingEngine()
analytics = EnergyAnalytics()

# In-memory storage (replace with database in production)
users_db: Dict[int, dict] = {}
energy_data_db: Dict[int, List[dict]] = {}
user_id_counter = 0


# ==================== User Endpoints ====================

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Register a new user on the platform"""
    global user_id_counter
    
    user_id_counter += 1
    user_id = user_id_counter
    
    # Store user data
    user_data = {
        'id': user_id,
        'username': user.username,
        'email': user.email,
        'role': user.role.value,
        'location_lat': user.location_lat,
        'location_lng': user.location_lng,
        'created_at': datetime.utcnow(),
        'password_hash': f"hashed_{user.password}"  # Replace with actual hashing
    }
    
    users_db[user_id] = user_data
    
    # Initialize trading account
    initial_energy = 50 if user.role in [UserRole.PRODUCER, UserRole.BOTH] else 0
    trading_engine.initialize_user(user_id, initial_energy=initial_energy)
    
    return UserResponse(**user_data)


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user details"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**users_db[user_id])


@app.get("/api/users/{user_id}/portfolio")
async def get_user_portfolio(user_id: int):
    """Get user's trading portfolio and statistics"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    portfolio = trading_engine.get_user_portfolio(user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Add consumption analytics
    consumption_analysis = analytics.analyze_consumption_pattern(user_id)
    portfolio['consumption_analysis'] = consumption_analysis
    
    return portfolio


# ==================== Energy Data Endpoints ====================

@app.post("/api/energy/data", response_model=EnergyDataResponse)
async def submit_energy_data(data: EnergyData):
    """Submit energy production/consumption data"""
    if data.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate derived fields
    net_energy = data.production_kwh - data.consumption_kwh
    surplus = net_energy > 0
    
    # Store data
    if data.user_id not in energy_data_db:
        energy_data_db[data.user_id] = []
    
    energy_record = {
        **data.dict(),
        'net_energy': net_energy,
        'surplus': surplus
    }
    energy_data_db[data.user_id].append(energy_record)
    
    # Update analytics
    analytics.add_price_data_point(
        price=pricing_engine.calculate_dynamic_price(
            data.production_kwh, 
            data.consumption_kwh
        )['adjusted_price']
    )
    analytics.add_consumption_data_point(
        user_id=data.user_id,
        consumption=data.consumption_kwh,
        production=data.production_kwh
    )
    
    # Update user's energy balance in trading engine
    if data.user_id in trading_engine.user_balances:
        trading_engine.user_balances[data.user_id]['energy_kwh'] += net_energy
    
    return EnergyDataResponse(**energy_record)


@app.get("/api/energy/current/{user_id}")
async def get_current_energy_data(user_id: int):
    """Get current energy data for a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_id not in energy_data_db or not energy_data_db[user_id]:
        return {"message": "No energy data available"}
    
    # Return most recent data
    latest = energy_data_db[user_id][-1]
    return latest


# ==================== Trading Endpoints ====================

@app.post("/api/trades/sell")
async def create_sell_order(
    user_id: int,
    energy_amount: float,
    min_price: float,
    duration_hours: float = 1.0
):
    """Create a sell order for excess energy"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = trading_engine.submit_sell_order(
        seller_id=user_id,
        energy_amount=energy_amount,
        min_price=min_price,
        duration_hours=duration_hours
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Record matched trades in ledger
    for trade_data in result.get('matched_trades', []):
        ledger.add_transaction(
            trade_id=int(trade_data['trade_id'], 16) % 1000000,
            seller_id=trade_data['seller_id'],
            buyer_id=trade_data['buyer_id'],
            energy_amount=trade_data['energy_amount'],
            price=trade_data['total_price']
        )
    
    return result


@app.post("/api/trades/buy")
async def create_buy_order(
    user_id: int,
    energy_amount: float,
    max_price: float,
    duration_hours: float = 1.0
):
    """Create a buy order for needed energy"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = trading_engine.submit_buy_order(
        buyer_id=user_id,
        energy_amount=energy_amount,
        max_price=max_price,
        duration_hours=duration_hours
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Record matched trades in ledger
    for trade_data in result.get('matched_trades', []):
        ledger.add_transaction(
            trade_id=int(trade_data['trade_id'], 16) % 1000000,
            seller_id=trade_data['seller_id'],
            buyer_id=trade_data['buyer_id'],
            energy_amount=trade_data['energy_amount'],
            price=trade_data['total_price']
        )
    
    return result


@app.get("/api/trades/history/{user_id}")
async def get_trade_history(user_id: int):
    """Get trade history for a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    portfolio = trading_engine.get_user_portfolio(user_id)
    return {
        'user_id': user_id,
        'trades': portfolio.get('recent_trades', [])
    }


@app.get("/api/trades/market/stats")
async def get_market_statistics():
    """Get overall market statistics"""
    stats = trading_engine.get_market_statistics()
    ledger_summary = ledger.get_chain_summary()
    
    return {
        **stats,
        'ledger_stats': ledger_summary
    }


# ==================== Pricing Endpoints ====================

@app.get("/api/pricing/current")
async def get_current_pricing():
    """Get current dynamic energy pricing"""
    # Use market-wide averages
    total_production = sum(
        data[-1]['production_kwh'] 
        for data in energy_data_db.values() 
        if data
    )
    total_consumption = sum(
        data[-1]['consumption_kwh'] 
        for data in energy_data_db.values() 
        if data
    )
    
    pricing_data = pricing_engine.calculate_dynamic_price(
        total_production or 1000,
        total_consumption or 800
    )
    
    return pricing_data


@app.get("/api/pricing/predictions")
async def get_price_predictions(hours: int = 24):
    """Get price predictions for next N hours"""
    predictions = analytics.predict_price_trend(hours_ahead=hours)
    return predictions


@app.get("/api/pricing/recommendations/{user_id}")
async def get_trading_recommendations(user_id: int, energy_amount: float = 10):
    """Get personalized trading recommendations for a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    role = 'seller' if user['role'] == 'producer' else 'buyer'
    
    recommendations = analytics.recommend_optimal_trading_times(
        user_role=role,
        energy_amount=energy_amount
    )
    
    return recommendations


# ==================== Analytics Endpoints ====================

@app.get("/api/analytics/market")
async def get_market_analytics():
    """Get comprehensive market analytics"""
    insights = analytics.get_market_insights()
    return insights


@app.get("/api/analytics/carbon/{user_id}")
async def get_carbon_offset(user_id: int):
    """Calculate user's carbon offset contribution"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's renewable energy production
    user_energy_data = energy_data_db.get(user_id, [])
    total_renewable = sum(d['production_kwh'] for d in user_energy_data)
    
    carbon_data = analytics.calculate_carbon_offset(
        renewable_energy_kwh=total_renewable,
        energy_source='solar'
    )
    
    return carbon_data


# ==================== Ledger Endpoints ====================

@app.get("/api/ledger/transactions")
async def get_ledger_transactions(limit: int = 10):
    """Get recent transactions from the ledger"""
    transactions = ledger.get_recent_transactions(limit)
    return {
        'transactions': transactions,
        'count': len(transactions)
    }


@app.get("/api/ledger/verify")
async def verify_ledger_integrity():
    """Verify the integrity of the ledger"""
    is_valid = ledger.verify_chain()
    summary = ledger.get_chain_summary()
    
    return {
        'is_valid': is_valid,
        'summary': summary
    }


@app.get("/api/ledger/user/{user_id}")
async def get_user_ledger_entries(user_id: int):
    """Get all ledger entries for a specific user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    transactions = ledger.get_user_transactions(user_id)
    return {
        'user_id': user_id,
        'transactions': [t.to_dict() for t in transactions],
        'count': len(transactions)
    }


# ==================== Health Check ====================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "EnergyChain API",
        "version": "1.0.0",
        "description": "Decentralized Peer-to-Peer Energy Trading Platform",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "users": "/api/users",
            "energy": "/api/energy",
            "trades": "/api/trades",
            "pricing": "/api/pricing",
            "analytics": "/api/analytics",
            "ledger": "/api/ledger"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "pricing_engine": "operational",
            "ledger": "operational",
            "trading_engine": "operational",
            "analytics": "operational"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
