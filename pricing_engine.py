"""
Dynamic Pricing Engine for EnergyChain
Implements smart pricing based on supply/demand, time of day, and grid load
"""
import math
from datetime import datetime
from typing import Dict, List, Tuple


class PricingEngine:
    """
    Advanced pricing algorithm that considers multiple factors:
    - Time of day (peak vs off-peak hours)
    - Supply and demand ratio
    - Grid load conditions
    - Seasonal adjustments
    - Local weather conditions
    """
    
    BASE_PRICE_PER_KWH = 0.12  # Base price in USD
    
    def __init__(self):
        self.time_multipliers = {
            'night': 0.7,      # 00:00 - 06:00
            'morning': 1.0,    # 06:00 - 09:00
            'peak': 1.5,       # 09:00 - 14:00
            'evening': 1.8,    # 14:00 - 20:00
            'night_peak': 1.2  # 20:00 - 00:00
        }
        
    def get_time_period(self, hour: int) -> str:
        """Determine time period based on hour of day"""
        if 0 <= hour < 6:
            return 'night'
        elif 6 <= hour < 9:
            return 'morning'
        elif 9 <= hour < 14:
            return 'peak'
        elif 14 <= hour < 20:
            return 'evening'
        else:
            return 'night_peak'
    
    def calculate_supply_demand_ratio(
        self, 
        total_production: float, 
        total_consumption: float
    ) -> float:
        """Calculate supply-demand ratio with bounds"""
        if total_consumption == 0:
            return 2.0  # High surplus
        
        ratio = total_production / total_consumption
        return max(0.1, min(ratio, 3.0))  # Bound between 0.1 and 3.0
    
    def calculate_grid_load_factor(self, current_load: float, max_capacity: float) -> float:
        """Calculate grid load factor (higher load = higher prices)"""
        if max_capacity == 0:
            return 1.0
        
        load_percentage = current_load / max_capacity
        
        if load_percentage < 0.5:
            return 0.9  # Low load discount
        elif load_percentage < 0.7:
            return 1.0  # Normal
        elif load_percentage < 0.85:
            return 1.2  # Moderate stress
        else:
            return 1.5  # High stress premium
    
    def calculate_seasonal_factor(self, month: int) -> float:
        """Adjust for seasonal variations"""
        # Summer and winter typically have higher demand
        if month in [6, 7, 8, 12, 1, 2]:
            return 1.15
        elif month in [4, 5, 9, 10]:
            return 1.0
        else:
            return 0.95
    
    def calculate_dynamic_price(
        self,
        total_production: float,
        total_consumption: float,
        current_hour: int = None,
        grid_load: float = None,
        max_capacity: float = None,
        month: int = None
    ) -> Dict[str, float]:
        """
        Calculate dynamic energy price based on multiple factors
        
        Returns:
            Dictionary with base_price, adjusted_price, and breakdown of factors
        """
        if current_hour is None:
            current_hour = datetime.now().hour
        if month is None:
            month = datetime.now().month
        
        # Start with base price
        base_price = self.BASE_PRICE_PER_KWH
        
        # Time-based adjustment
        time_period = self.get_time_period(current_hour)
        time_multiplier = self.time_multipliers[time_period]
        
        # Supply-demand adjustment
        sd_ratio = self.calculate_supply_demand_ratio(total_production, total_consumption)
        # Inverse relationship: high supply = lower price, low supply = higher price
        sd_multiplier = 1.0 + (1.0 - min(sd_ratio, 2.0) / 2.0) * 0.5
        
        # Grid load adjustment
        grid_multiplier = 1.0
        if grid_load is not None and max_capacity is not None:
            grid_multiplier = self.calculate_grid_load_factor(grid_load, max_capacity)
        
        # Seasonal adjustment
        seasonal_multiplier = self.calculate_seasonal_factor(month)
        
        # Calculate final price
        adjusted_price = (
            base_price * 
            time_multiplier * 
            sd_multiplier * 
            grid_multiplier * 
            seasonal_multiplier
        )
        
        # Round to 4 decimal places
        adjusted_price = round(max(0.01, adjusted_price), 4)
        
        return {
            'base_price': base_price,
            'adjusted_price': adjusted_price,
            'time_multiplier': time_multiplier,
            'time_period': time_period,
            'supply_demand_ratio': sd_ratio,
            'sd_multiplier': sd_multiplier,
            'grid_multiplier': grid_multiplier,
            'seasonal_multiplier': seasonal_multiplier,
            'total_multiplier': round(time_multiplier * sd_multiplier * grid_multiplier * seasonal_multiplier, 3)
        }
    
    def recommend_trade_price(
        self,
        seller_production: float,
        buyer_consumption: float,
        market_production: float,
        market_consumption: float,
        urgency: float = 0.5
    ) -> Dict[str, float]:
        """
        Recommend optimal trade price for a specific transaction
        
        Args:
            seller_production: Seller's available energy (kWh)
            buyer_consumption: Buyer's needed energy (kWh)
            market_production: Total market production
            market_consumption: Total market consumption
            urgency: How urgent the trade is (0.0 - 1.0)
        
        Returns:
            Recommended price range and optimal price
        """
        market_data = self.calculate_dynamic_price(market_production, market_consumption)
        base_price = market_data['adjusted_price']
        
        # Adjust for trade size
        trade_size = min(seller_production, buyer_consumption)
        size_discount = 1.0
        if trade_size > 100:
            size_discount = 0.95  # 5% discount for large trades
        elif trade_size > 50:
            size_discount = 0.98  # 2% discount
        
        # Urgency premium
        urgency_premium = 1.0 + (urgency * 0.1)  # Up to 10% premium for urgent trades
        
        # Calculate price range
        min_price = base_price * size_discount * 0.95
        max_price = base_price * urgency_premium * 1.05
        optimal_price = base_price * size_discount * urgency_premium
        
        return {
            'min_recommended': round(min_price, 4),
            'max_recommended': round(max_price, 4),
            'optimal_price': round(optimal_price, 4),
            'market_base': base_price,
            'trade_size_kwh': trade_size
        }
    
    def predict_price_trend(
        self,
        current_production: float,
        current_consumption: float,
        forecast_hours: int = 24
    ) -> List[Dict]:
        """
        Predict price trends for next N hours
        
        Returns list of hourly predictions
        """
        predictions = []
        current_time = datetime.now()
        
        for hour_offset in range(forecast_hours):
            future_time = current_time.replace(
                hour=(current_time.hour + hour_offset) % 24
            )
            
            # Simulate slight variations in supply/demand
            variation = math.sin(hour_offset * 0.5) * 0.1
            future_production = current_production * (1 + variation)
            future_consumption = current_consumption * (1 - variation * 0.5)
            
            price_data = self.calculate_dynamic_price(
                future_production,
                future_consumption,
                future_time.hour,
                month=future_time.month
            )
            
            predictions.append({
                'hour': hour_offset,
                'timestamp': future_time.isoformat(),
                'predicted_price': price_data['adjusted_price'],
                'time_period': price_data['time_period']
            })
        
        return predictions
