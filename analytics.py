"""
Analytics and Prediction Engine for EnergyChain
Uses ML to predict energy prices, consumption patterns, and trading opportunities
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


class EnergyAnalytics:
    """
    Advanced analytics engine for energy trading insights
    Features:
    - Price prediction using historical data
    - Consumption pattern analysis
    - Optimal trading time recommendations
    - Carbon offset calculations
    """
    
    def __init__(self):
        self.price_history: List[Dict] = []
        self.consumption_history: List[Dict] = []
        self.model_cache: Dict = {}
        
        # Carbon emission factors (kg CO2 per kWh)
        self.carbon_factors = {
            'grid_average': 0.4,  # Average grid electricity
            'solar': 0.05,        # Solar (manufacturing/maintenance)
            'wind': 0.01,         # Wind
            'natural_gas': 0.5,   # Natural gas
            'coal': 0.9           # Coal
        }
    
    def add_price_data_point(
        self,
        price: float,
        timestamp: datetime = None,
        volume: float = 0,
        source: str = 'market'
    ):
        """Add a price data point to history"""
        self.price_history.append({
            'price': price,
            'timestamp': timestamp or datetime.utcnow(),
            'volume': volume,
            'source': source
        })
        
        # Keep only last 1000 data points
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
    
    def add_consumption_data_point(
        self,
        user_id: int,
        consumption: float,
        production: float,
        timestamp: datetime = None
    ):
        """Add consumption data point"""
        self.consumption_history.append({
            'user_id': user_id,
            'consumption': consumption,
            'production': production,
            'net': production - consumption,
            'timestamp': timestamp or datetime.utcnow()
        })
        
        # Keep only last 10000 data points
        if len(self.consumption_history) > 10000:
            self.consumption_history = self.consumption_history[-10000:]
    
    def predict_price_trend(
        self,
        hours_ahead: int = 24,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        Predict energy price trends using polynomial regression
        Returns predictions with confidence scores
        """
        if len(self.price_history) < 10:
            return self._get_baseline_prediction(hours_ahead)
        
        # Prepare training data
        timestamps = []
        prices = []
        
        for i, data in enumerate(self.price_history[-100:]):
            timestamps.append(i)
            prices.append(data['price'])
        
        X = np.array(timestamps).reshape(-1, 1)
        y = np.array(prices)
        
        # Create polynomial features
        degree = min(3, len(X) // 5)
        poly = PolynomialFeatures(degree=degree)
        X_poly = poly.fit_transform(X)
        
        # Train model
        model = LinearRegression()
        model.fit(X_poly, y)
        
        # Generate predictions
        future_hours = list(range(len(X), len(X) + hours_ahead))
        X_future = poly.transform(np.array(future_hours).reshape(-1, 1))
        predictions = model.predict(X_future)
        
        # Calculate confidence score based on R²
        r2_score = model.score(X_poly, y)
        confidence = max(0, min(1, r2_score))
        
        # Generate hourly predictions
        hourly_predictions = []
        current_time = datetime.utcnow()
        
        for i, pred in enumerate(predictions):
            hourly_predictions.append({
                'hour': i + 1,
                'timestamp': (current_time + timedelta(hours=i+1)).isoformat(),
                'predicted_price': round(max(0.01, pred), 4),
                'confidence': round(confidence, 3)
            })
        
        # Calculate summary statistics
        predicted_prices = [p['predicted_price'] for p in hourly_predictions]
        
        return {
            'predictions': hourly_predictions,
            'average_predicted_price': round(np.mean(predicted_prices), 4),
            'min_predicted_price': round(min(predicted_prices), 4),
            'max_predicted_price': round(max(predicted_prices), 4),
            'confidence_score': round(confidence, 3),
            'trend': 'upward' if predictions[-1] > predictions[0] else 'downward',
            'volatility': round(np.std(predicted_prices), 4)
        }
    
    def _get_baseline_prediction(self, hours_ahead: int) -> Dict:
        """Return baseline prediction when insufficient data"""
        current_time = datetime.utcnow()
        base_price = 0.12  # Default base price
        
        predictions = []
        for i in range(hours_ahead):
            hour = (current_time.hour + i) % 24
            
            # Simple time-based adjustment
            if 14 <= hour < 20:  # Peak hours
                price = base_price * 1.5
            elif 9 <= hour < 14:  # Mid-day
                price = base_price * 1.2
            elif 0 <= hour < 6:  # Night
                price = base_price * 0.7
            else:
                price = base_price
            
            predictions.append({
                'hour': i + 1,
                'timestamp': (current_time + timedelta(hours=i+1)).isoformat(),
                'predicted_price': round(price, 4),
                'confidence': 0.3  # Low confidence for baseline
            })
        
        return {
            'predictions': predictions,
            'average_predicted_price': base_price,
            'min_predicted_price': base_price * 0.7,
            'max_predicted_price': base_price * 1.5,
            'confidence_score': 0.3,
            'trend': 'stable',
            'volatility': 0.02
        }
    
    def recommend_optimal_trading_times(
        self,
        user_role: str,  # 'buyer' or 'seller'
        energy_amount: float,
        time_window_hours: int = 24
    ) -> Dict:
        """
        Recommend optimal times for buying or selling energy
        """
        price_prediction = self.predict_price_trend(time_window_hours)
        
        if user_role == 'buyer':
            # Find cheapest hours to buy
            sorted_predictions = sorted(
                price_prediction['predictions'],
                key=lambda x: x['predicted_price']
            )
            best_times = sorted_predictions[:5]
            worst_times = sorted_predictions[-5:]
            recommendation = "Buy during low-price periods"
        else:
            # Find most expensive hours to sell
            sorted_predictions = sorted(
                price_prediction['predictions'],
                key=lambda x: x['predicted_price'],
                reverse=True
            )
            best_times = sorted_predictions[:5]
            worst_times = sorted_predictions[-5:]
            recommendation = "Sell during high-price periods"
        
        potential_savings = 0
        if best_times and worst_times:
            price_diff = abs(best_times[0]['predicted_price'] - worst_times[0]['predicted_price'])
            potential_savings = round(price_diff * energy_amount, 2)
        
        return {
            'recommendation': recommendation,
            'best_times': best_times,
            'worst_times': worst_times,
            'potential_savings_usd': potential_savings,
            'average_price': price_prediction['average_predicted_price'],
            'confidence': price_prediction['confidence_score']
        }
    
    def analyze_consumption_pattern(
        self,
        user_id: int,
        days_back: int = 7
    ) -> Dict:
        """Analyze user's energy consumption patterns"""
        user_data = [
            d for d in self.consumption_history
            if d['user_id'] == user_id
        ]
        
        if not user_data:
            return {'error': 'No consumption data available'}
        
        # Calculate statistics
        total_consumption = sum(d['consumption'] for d in user_data)
        total_production = sum(d['production'] for d in user_data)
        avg_consumption = total_consumption / len(user_data)
        avg_production = total_production / len(user_data)
        
        # Self-sufficiency ratio
        self_sufficiency = (total_production / total_consumption * 100) if total_consumption > 0 else 0
        
        # Peak consumption hours
        hourly_consumption = {}
        for d in user_data:
            hour = d['timestamp'].hour
            hourly_consumption[hour] = hourly_consumption.get(hour, 0) + d['consumption']
        
        peak_hour = max(hourly_consumption, key=hourly_consumption.get) if hourly_consumption else None
        
        return {
            'user_id': user_id,
            'data_points': len(user_data),
            'total_consumption_kwh': round(total_consumption, 2),
            'total_production_kwh': round(total_production, 2),
            'average_consumption_kwh': round(avg_consumption, 2),
            'average_production_kwh': round(avg_production, 2),
            'self_sufficiency_percent': round(self_sufficiency, 2),
            'peak_consumption_hour': peak_hour,
            'net_energy_balance': round(total_production - total_consumption, 2)
        }
    
    def calculate_carbon_offset(
        self,
        renewable_energy_kwh: float,
        energy_source: str = 'solar'
    ) -> Dict:
        """
        Calculate carbon emissions avoided by using renewable energy
        """
        grid_factor = self.carbon_factors['grid_average']
        renewable_factor = self.carbon_factors.get(energy_source, 0.05)
        
        # Emissions that would have been produced by grid
        grid_emissions = renewable_energy_kwh * grid_factor
        
        # Actual emissions from renewable source
        renewable_emissions = renewable_energy_kwh * renewable_factor
        
        # Net offset
        carbon_offset = grid_emissions - renewable_emissions
        
        # Equivalent metrics
        trees_equivalent = carbon_offset / 20  # One tree absorbs ~20 kg CO2/year
        car_miles_equivalent = carbon_offset / 0.4  # Average car emits ~0.4 kg CO2/mile
        
        return {
            'renewable_energy_kwh': renewable_energy_kwh,
            'energy_source': energy_source,
            'carbon_offset_kg': round(carbon_offset, 2),
            'grid_emissions_avoided_kg': round(grid_emissions, 2),
            'trees_equivalent_per_year': round(trees_equivalent, 2),
            'car_miles_equivalent': round(car_miles_equivalent, 2),
            'environmental_impact_score': round(min(100, carbon_offset / 10), 1)
        }
    
    def get_market_insights(self) -> Dict:
        """Generate comprehensive market insights"""
        if not self.price_history:
            return {'message': 'Insufficient market data'}
        
        recent_prices = [p['price'] for p in self.price_history[-50:]]
        
        # Calculate metrics
        current_price = recent_prices[-1] if recent_prices else 0
        avg_price = np.mean(recent_prices)
        price_volatility = np.std(recent_prices)
        
        # Trend analysis
        if len(recent_prices) >= 10:
            recent_trend = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
        else:
            recent_trend = 0
        
        # Market sentiment
        if recent_trend > 0.001:
            sentiment = 'bullish'
        elif recent_trend < -0.001:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return {
            'current_price': round(current_price, 4),
            'average_price_24h': round(avg_price, 4),
            'price_volatility': round(price_volatility, 4),
            'trend_direction': 'up' if recent_trend > 0 else 'down',
            'trend_strength': round(abs(recent_trend), 4),
            'market_sentiment': sentiment,
            'data_points_analyzed': len(recent_prices),
            'recommendation': self._generate_trading_recommendation(sentiment, price_volatility)
        }
    
    def _generate_trading_recommendation(self, sentiment: str, volatility: float) -> str:
        """Generate simple trading recommendation"""
        if sentiment == 'bullish' and volatility < 0.05:
            return "Good time to sell - prices trending up with low volatility"
        elif sentiment == 'bearish' and volatility < 0.05:
            return "Good time to buy - prices trending down with low volatility"
        elif volatility >= 0.05:
            return "High volatility - consider waiting for market stabilization"
        else:
            return "Market neutral - no strong trading signals"
