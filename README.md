# ⚡ Smart Energy Trading Platform (EnergyChain)

## Overview
A decentralized peer-to-peer energy trading platform that enables homeowners with renewable energy sources (solar panels, wind turbines) to trade excess energy directly with their neighbors. This addresses the growing demand for sustainable energy solutions and grid decentralization.

## 🌟 Key Features
- **Real-time Energy Monitoring**: Track production and consumption in real-time
- **Smart Pricing Algorithm**: Dynamic pricing based on supply/demand, time of day, and grid load
- **Secure Transaction Ledger**: Blockchain-inspired immutable transaction records
- **Automated Trading**: AI-powered buy/sell recommendations
- **Grid Integration**: Seamless connection with existing power infrastructure
- **Carbon Credit Tracking**: Automatic calculation and tracking of environmental impact

## 🚀 Why This Project?
- **High Demand**: Global P2P energy trading market expected to reach $19B by 2030
- **Sustainability**: Promotes renewable energy adoption
- **Cost Savings**: Reduces energy costs for both producers and consumers
- **Grid Stability**: Helps balance local energy grids
- **Innovation**: Combines IoT, AI, and distributed ledger technology

## Tech Stack
- **Backend**: Python FastAPI
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL + Redis for caching
- **Real-time**: WebSocket connections
- **Analytics**: Pandas, NumPy for energy prediction models
- **Security**: JWT authentication, encryption

## Quick Start

### Option 1: Run the Demo Script (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the comprehensive demo
python demo.py
```

### Option 2: Run the API Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend server
python main.py

# Access API documentation at http://localhost:8000/docs
# Access interactive ReDoc at http://localhost:8000/redoc
```

## Project Structure
```
/workspace
├── main.py                 # FastAPI application entry point
├── models.py               # Data models and schemas
├── energy_trading.py       # Core trading logic with order matching
├── pricing_engine.py       # Dynamic pricing algorithms
├── ledger.py               # Blockchain-inspired transaction ledger
├── analytics.py            # ML-powered energy prediction and analytics
├── demo.py                 # Comprehensive demonstration script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## API Endpoints
- `POST /api/users` - Register new user
- `GET /api/energy/current` - Get current energy data
- `POST /api/trades` - Create energy trade
- `GET /api/trades/history` - View trade history
- `GET /api/analytics/predictions` - Get energy predictions
- `GET /api/ledger/transactions` - View transaction ledger

## Future Enhancements
- Mobile app integration
- Smart contract implementation on Ethereum
- IoT device integration for automatic meter reading
- Machine learning for consumption pattern prediction
- Multi-currency support for international energy trading