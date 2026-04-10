#!/usr/bin/env python3
"""
EnergyChain Demo Script
Demonstrates the full capabilities of the P2P Energy Trading Platform
"""

from main import app
from fastapi.testclient import TestClient
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_json(data, indent=2):
    print(json.dumps(data, indent=indent, default=str))

def run_demo():
    client = TestClient(app)
    
    print_section("🌟 ENERGYCHAIN DEMO - P2P Energy Trading Platform")
    
    # 1. System Health Check
    print_section("1. System Status")
    response = client.get('/health')
    health = response.json()
    print(f"✅ Status: {health['status'].upper()}")
    print(f"   Timestamp: {health['timestamp']}")
    print(f"   Components: {', '.join([k for k,v in health['components'].items() if v == 'operational'])}")
    
    # 2. Register Users
    print_section("2. Registering Market Participants")
    
    # Producer (Solar Farm)
    producer = {
        'username': 'solar_farm_alpha',
        'email': 'operator@solarfarm.com',
        'role': 'producer',
        'location_lat': 37.7749,
        'location_lng': -122.4194,
        'password': 'securepass123'
    }
    response = client.post('/api/users', json=producer)
    producer_id = response.json()['id']
    print(f"☀️  Producer Registered: {producer['username']} (ID: {producer_id})")
    print(f"    Location: San Francisco, CA")
    
    # Consumer 1 (Residential)
    consumer1 = {
        'username': 'home_owner_john',
        'email': 'john@home.com',
        'role': 'consumer',
        'location_lat': 37.7751,
        'location_lng': -122.4180,
        'password': 'securepass123'
    }
    response = client.post('/api/users', json=consumer1)
    consumer1_id = response.json()['id']
    print(f"🏠 Consumer Registered: {consumer1['username']} (ID: {consumer1_id})")
    
    # Consumer 2 (Business)
    consumer2 = {
        'username': 'tech_office_building',
        'email': 'energy@techcorp.com',
        'role': 'consumer',
        'location_lat': 37.7760,
        'location_lng': -122.4200,
        'password': 'securepass123'
    }
    response = client.post('/api/users', json=consumer2)
    consumer2_id = response.json()['id']
    print(f"🏢 Consumer Registered: {consumer2['username']} (ID: {consumer2_id})")
    
    # Prosumer (Both)
    prosumer = {
        'username': 'green_home_lisa',
        'email': 'lisa@greenhome.com',
        'role': 'both',
        'location_lat': 37.7740,
        'location_lng': -122.4170,
        'password': 'securepass123'
    }
    response = client.post('/api/users', json=prosumer)
    prosumer_id = response.json()['id']
    print(f"⚡ Prosumer Registered: {prosumer['username']} (ID: {prosumer_id})")
    
    # 3. Submit Energy Data
    print_section("3. Energy Production & Consumption Data")
    
    # Solar farm produces energy
    solar_data = {
        'user_id': producer_id,
        'production_kwh': 500.0,
        'consumption_kwh': 50.0,
        'battery_level': 90.0
    }
    response = client.post('/api/energy/data', json=solar_data)
    solar_net = response.json()
    print(f"☀️  Solar Farm: Producing {solar_data['production_kwh']} kWh")
    print(f"    Consuming: {solar_data['consumption_kwh']} kWh")
    print(f"    Net Surplus: {solar_net['net_energy']} kWh ✅")
    
    # Home consumes energy
    home_data = {
        'user_id': consumer1_id,
        'production_kwh': 5.0,
        'consumption_kwh': 25.0,
        'battery_level': 40.0
    }
    response = client.post('/api/energy/data', json=home_data)
    home_net = response.json()
    print(f"🏠 Home Owner: Producing {home_data['production_kwh']} kWh (rooftop solar)")
    print(f"    Consuming: {home_data['consumption_kwh']} kWh")
    print(f"    Net Deficit: {home_net['net_energy']} kWh ⚠️")
    
    # Office building consumes energy
    office_data = {
        'user_id': consumer2_id,
        'production_kwh': 20.0,
        'consumption_kwh': 150.0,
        'battery_level': 30.0
    }
    response = client.post('/api/energy/data', json=office_data)
    office_net = response.json()
    print(f"🏢 Tech Office: Producing {office_data['production_kwh']} kWh")
    print(f"    Consuming: {office_data['consumption_kwh']} kWh")
    print(f"    Net Deficit: {office_net['net_energy']} kWh ⚠️")
    
    # Prosumer data
    prosumer_data = {
        'user_id': prosumer_id,
        'production_kwh': 30.0,
        'consumption_kwh': 20.0,
        'battery_level': 75.0
    }
    response = client.post('/api/energy/data', json=prosumer_data)
    prosumer_net = response.json()
    print(f"⚡ Green Home: Producing {prosumer_data['production_kwh']} kWh")
    print(f"    Consuming: {prosumer_data['consumption_kwh']} kWh")
    print(f"    Net Surplus: {prosumer_net['net_energy']} kWh ✅")
    
    # 4. Current Market Pricing
    print_section("4. Dynamic Market Pricing")
    response = client.get('/api/pricing/current')
    pricing = response.json()
    print(f"💰 Base Price: ${pricing['base_price']}/kWh")
    print(f"📊 Adjusted Price: ${pricing['adjusted_price']}/kWh")
    print(f"⏰ Time Period: {pricing['time_period']} (multiplier: {pricing['time_multiplier']}x)")
    print(f"📈 Supply/Demand Ratio: {pricing['supply_demand_ratio']:.2f}")
    print(f"🔌 Total Multiplier: {pricing['total_multiplier']}x")
    
    # 5. Create Trading Orders
    print_section("5. Energy Trading Marketplace")
    
    # Solar farm sells energy
    print("\n📤 SELL ORDER: Solar Farm offers 200 kWh")
    response = client.post('/api/trades/sell', params={
        'user_id': producer_id,
        'energy_amount': 200.0,
        'min_price': 0.15,
        'duration_hours': 2.0
    })
    sell_result = response.json()
    print(f"   Status: {'✅ ACCEPTED' if sell_result['success'] else '❌ REJECTED'}")
    if sell_result.get('matched_trades'):
        print(f"   Immediate Matches: {len(sell_result['matched_trades'])}")
    
    # Prosumer sells excess energy
    print("\n📤 SELL ORDER: Green Home offers 10 kWh")
    response = client.post('/api/trades/sell', params={
        'user_id': prosumer_id,
        'energy_amount': 10.0,
        'min_price': 0.18,
        'duration_hours': 1.0
    })
    sell_result = response.json()
    print(f"   Status: {'✅ ACCEPTED' if sell_result['success'] else '❌ REJECTED'}")
    
    # Home owner buys energy
    print("\n📥 BUY ORDER: Home Owner needs 20 kWh")
    response = client.post('/api/trades/buy', params={
        'user_id': consumer1_id,
        'energy_amount': 20.0,
        'max_price': 0.25,
        'duration_hours': 1.0
    })
    buy_result = response.json()
    print(f"   Status: {'✅ ACCEPTED' if buy_result['success'] else '❌ REJECTED'}")
    if buy_result.get('matched_trades'):
        for trade in buy_result['matched_trades']:
            print(f"   🎯 MATCHED: {trade['energy_amount']} kWh @ ${trade['price_per_kwh']}/kWh")
            print(f"      From: User {trade['seller_id']} → To: User {trade['buyer_id']}")
            print(f"      Total: ${trade['total_price']:.2f}")
    
    # Office building buys energy
    print("\n📥 BUY ORDER: Tech Office needs 100 kWh")
    response = client.post('/api/trades/buy', params={
        'user_id': consumer2_id,
        'energy_amount': 100.0,
        'max_price': 0.22,
        'duration_hours': 2.0
    })
    buy_result = response.json()
    print(f"   Status: {'✅ ACCEPTED' if buy_result['success'] else '❌ REJECTED'}")
    if buy_result.get('matched_trades'):
        for trade in buy_result['matched_trades']:
            print(f"   🎯 MATCHED: {trade['energy_amount']} kWh @ ${trade['price_per_kwh']}/kWh")
    
    # 6. Market Statistics
    print_section("6. Market Statistics")
    response = client.get('/api/trades/market/stats')
    stats = response.json()
    print(f"📊 Total Trades Executed: {stats['total_trades']}")
    print(f"⚡ Active Orders: {stats['active_trades']}")
    print(f"💹 Total Volume: {stats['total_volume_kwh']} kWh")
    print(f"💰 Total Value: ${stats['total_value_usd']:.2f}")
    print(f"👥 Registered Users: {stats['registered_users']}")
    
    # 7. Blockchain Ledger
    print_section("7. Blockchain Transaction Ledger")
    response = client.get('/api/ledger/transactions')
    ledger = response.json()
    print(f"📝 Total Transactions: {ledger['count']}")
    if ledger['transactions']:
        print("\nRecent Transactions:")
        for tx in ledger['transactions'][-3:]:
            print(f"   TX #{tx['transaction_id']}: {tx['energy_amount']} kWh - ${tx['price']:.2f}")
            print(f"      {tx['seller_id']} → {tx['buyer_id']} @ {tx['timestamp'][:19]}")
    
    response = client.get('/api/ledger/verify')
    verification = response.json()
    print(f"\n🔐 Ledger Integrity: {'✅ VERIFIED' if verification['is_valid'] else '❌ COMPROMISED'}")
    print(f"   Chain Length: {verification['summary']['chain_length']} blocks")
    
    # 8. Analytics & Predictions
    print_section("8. AI-Powered Analytics")
    
    # Price predictions
    response = client.get('/api/pricing/predictions')
    predictions = response.json()
    print(f"🔮 Price Forecast (24h):")
    print(f"   Trend: {predictions['trend'].upper()}")
    print(f"   Avg Price: ${predictions['average_predicted_price']}/kWh")
    print(f"   Range: ${predictions['min_predicted_price']} - ${predictions['max_predicted_price']}")
    print(f"   Confidence: {predictions['confidence_score']*100:.0f}%")
    print(f"   Volatility: {predictions['volatility']}")
    
    # Market insights
    response = client.get('/api/analytics/market')
    insights = response.json()
    print(f"\n📈 Market Sentiment: {insights['market_sentiment'].upper()}")
    print(f"   Recommendation: {insights['recommendation']}")
    
    # 9. Carbon Offset Impact
    print_section("9. Environmental Impact")
    response = client.get(f'/api/analytics/carbon/{producer_id}')
    carbon = response.json()
    print(f"🌱 Solar Farm Carbon Offset:")
    print(f"   Renewable Energy: {carbon['renewable_energy_kwh']} kWh")
    print(f"   CO₂ Offset: {carbon['carbon_offset_kg']} kg")
    print(f"   Equivalent to: {carbon['trees_equivalent_per_year']} trees planted 🌳")
    print(f"   Equivalent to: {carbon['car_miles_equivalent']:.0f} car miles avoided 🚗")
    print(f"   Environmental Score: {carbon['environmental_impact_score']}/100")
    
    # 10. User Portfolio
    print_section("10. User Portfolio Example")
    response = client.get(f'/api/users/{producer_id}/portfolio')
    portfolio = response.json()
    print(f"👤 {producer['username']}'s Portfolio:")
    print(f"   Energy Balance: {portfolio['energy_balance_kwh']} kWh")
    print(f"   Cash Balance: ${portfolio['cash_balance_usd']:.2f}")
    print(f"   Total Earned: ${portfolio['total_earned_usd']:.2f}")
    print(f"   Trades Completed: {portfolio['trades_completed']}")
    
    # Trading recommendations
    response = client.get(f'/api/pricing/recommendations/{consumer1_id}', params={'energy_amount': 20})
    recs = response.json()
    print(f"\n💡 Trading Recommendation for {consumer1['username']}:")
    print(f"   Strategy: {recs['recommendation']}")
    print(f"   Potential Savings: ${recs['potential_savings_usd']:.2f}")
    if recs.get('best_times'):
        best = recs['best_times'][0]
        print(f"   Best Time: Hour {best['hour']} @ ${best['predicted_price']}/kWh")
    
    print_section("✅ DEMO COMPLETE")
    print("\n🎉 EnergyChain successfully demonstrated:")
    print("   ✓ User registration (producers, consumers, prosumers)")
    print("   ✓ Real-time energy monitoring")
    print("   ✓ Dynamic pricing based on supply/demand")
    print("   ✓ P2P energy trading with order matching")
    print("   ✓ Blockchain-based transaction ledger")
    print("   ✓ AI-powered price predictions")
    print("   ✓ Carbon offset tracking")
    print("   ✓ Personalized trading recommendations")
    print("\n🚀 Ready for production deployment!")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_demo()
