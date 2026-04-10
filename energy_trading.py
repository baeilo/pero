"""
Energy Trading Core Logic for EnergyChain
Handles matching, trade execution, and settlement
"""
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
import uuid


class TradeStatus(Enum):
    PENDING = "pending"
    MATCHED = "matched"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class EnergyTrade:
    """Represents an energy trade between producer and consumer"""
    
    def __init__(
        self,
        seller_id: int,
        buyer_id: int,
        energy_amount: float,
        price_per_kwh: float,
        duration_hours: float,
        trade_id: str = None
    ):
        self.trade_id = trade_id or str(uuid.uuid4())[:8]
        self.seller_id = seller_id
        self.buyer_id = buyer_id
        self.energy_amount = energy_amount
        self.price_per_kwh = price_per_kwh
        self.duration_hours = duration_hours
        self.total_price = energy_amount * price_per_kwh
        self.status = TradeStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.settlement_price: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'seller_id': self.seller_id,
            'buyer_id': self.buyer_id,
            'energy_amount': self.energy_amount,
            'price_per_kwh': self.price_per_kwh,
            'total_price': self.total_price,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class OrderBook:
    """Manages buy and sell orders for energy trading"""
    
    def __init__(self):
        self.sell_orders: List[Dict] = []  # Offers to sell
        self.buy_orders: List[Dict] = []   # Requests to buy
        self.trades: List[EnergyTrade] = []
    
    def add_sell_order(
        self,
        seller_id: int,
        energy_amount: float,
        min_price: float,
        available_from: datetime = None,
        duration_hours: float = 1.0
    ):
        """Add a sell order to the order book"""
        order = {
            'order_id': str(uuid.uuid4())[:8],
            'type': 'sell',
            'seller_id': seller_id,
            'energy_amount': energy_amount,
            'min_price': min_price,
            'available_from': available_from or datetime.utcnow(),
            'duration_hours': duration_hours,
            'created_at': datetime.utcnow(),
            'filled_amount': 0.0
        }
        self.sell_orders.append(order)
        # Sort by price (lowest first for sell orders)
        self.sell_orders.sort(key=lambda x: x['min_price'])
        return order
    
    def add_buy_order(
        self,
        buyer_id: int,
        energy_amount: float,
        max_price: float,
        needed_from: datetime = None,
        duration_hours: float = 1.0
    ):
        """Add a buy order to the order book"""
        order = {
            'order_id': str(uuid.uuid4())[:8],
            'type': 'buy',
            'buyer_id': buyer_id,
            'energy_amount': energy_amount,
            'max_price': max_price,
            'needed_from': needed_from or datetime.utcnow(),
            'duration_hours': duration_hours,
            'created_at': datetime.utcnow(),
            'filled_amount': 0.0
        }
        self.buy_orders.append(order)
        # Sort by price (highest first for buy orders)
        self.buy_orders.sort(key=lambda x: x['max_price'], reverse=True)
        return order
    
    def match_orders(self) -> List[EnergyTrade]:
        """
        Match compatible buy and sell orders
        Returns list of created trades
        """
        matched_trades = []
        
        for buy_order in self.buy_orders[:]:
            if buy_order['filled_amount'] >= buy_order['energy_amount']:
                continue
            
            for sell_order in self.sell_orders[:]:
                if sell_order['filled_amount'] >= sell_order['energy_amount']:
                    continue
                
                # Check price compatibility
                if buy_order['max_price'] < sell_order['min_price']:
                    continue
                
                # Calculate matchable amount
                buy_remaining = buy_order['energy_amount'] - buy_order['filled_amount']
                sell_remaining = sell_order['energy_amount'] - sell_order['filled_amount']
                match_amount = min(buy_remaining, sell_remaining)
                
                if match_amount <= 0:
                    continue
                
                # Determine execution price (midpoint between bid and ask)
                execution_price = (buy_order['max_price'] + sell_order['min_price']) / 2
                
                # Create trade
                trade = EnergyTrade(
                    seller_id=sell_order['seller_id'],
                    buyer_id=buy_order['buyer_id'],
                    energy_amount=match_amount,
                    price_per_kwh=execution_price,
                    duration_hours=min(
                        buy_order['duration_hours'],
                        sell_order['duration_hours']
                    )
                )
                trade.status = TradeStatus.MATCHED
                
                # Update order filled amounts
                buy_order['filled_amount'] += match_amount
                sell_order['filled_amount'] += match_amount
                
                self.trades.append(trade)
                matched_trades.append(trade)
        
        return matched_trades
    
    def get_order_book_snapshot(self) -> Dict:
        """Get current state of the order book"""
        return {
            'sell_orders': [
                {
                    'order_id': o['order_id'],
                    'seller_id': o['seller_id'],
                    'energy_amount': o['energy_amount'],
                    'filled_amount': o['filled_amount'],
                    'price': o['min_price']
                }
                for o in self.sell_orders
            ],
            'buy_orders': [
                {
                    'order_id': o['order_id'],
                    'buyer_id': o['buyer_id'],
                    'energy_amount': o['energy_amount'],
                    'filled_amount': o['filled_amount'],
                    'price': o['max_price']
                }
                for o in self.buy_orders
            ],
            'spread': self._calculate_spread()
        }
    
    def _calculate_spread(self) -> Optional[float]:
        """Calculate bid-ask spread"""
        if not self.sell_orders or not self.buy_orders:
            return None
        
        best_ask = self.sell_orders[0]['min_price']
        best_bid = self.buy_orders[0]['max_price']
        
        return best_ask - best_bid
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        for orders_list in [self.sell_orders, self.buy_orders]:
            for i, order in enumerate(orders_list):
                if order['order_id'] == order_id:
                    orders_list.pop(i)
                    return True
        return False


class TradingEngine:
    """Main trading engine coordinating all trading operations"""
    
    def __init__(self):
        self.order_book = OrderBook()
        self.active_trades: List[EnergyTrade] = []
        self.completed_trades: List[EnergyTrade] = []
        self.user_balances: Dict[int, Dict] = {}  # user_id -> {energy, currency}
    
    def initialize_user(self, user_id: int, initial_energy: float = 0, initial_balance: float = 1000):
        """Initialize a user account with starting balances"""
        self.user_balances[user_id] = {
            'energy_kwh': initial_energy,
            'balance_usd': initial_balance,
            'total_earned': 0,
            'total_spent': 0
        }
    
    def submit_sell_order(
        self,
        seller_id: int,
        energy_amount: float,
        min_price: float,
        duration_hours: float = 1.0
    ) -> Dict:
        """Submit a sell order and attempt immediate matching"""
        if seller_id not in self.user_balances:
            self.initialize_user(seller_id)
        
        # Check if user has enough energy
        if self.user_balances[seller_id]['energy_kwh'] < energy_amount:
            return {'success': False, 'error': 'Insufficient energy balance'}
        
        order = self.order_book.add_sell_order(
            seller_id=seller_id,
            energy_amount=energy_amount,
            min_price=min_price,
            duration_hours=duration_hours
        )
        
        # Try to match immediately
        matched = self.order_book.match_orders()
        
        return {
            'success': True,
            'order': order,
            'matched_trades': [t.to_dict() for t in matched]
        }
    
    def submit_buy_order(
        self,
        buyer_id: int,
        energy_amount: float,
        max_price: float,
        duration_hours: float = 1.0
    ) -> Dict:
        """Submit a buy order and attempt immediate matching"""
        if buyer_id not in self.user_balances:
            self.initialize_user(buyer_id)
        
        # Check if user has enough balance (rough estimate)
        estimated_cost = energy_amount * max_price
        if self.user_balances[buyer_id]['balance_usd'] < estimated_cost:
            return {'success': False, 'error': 'Insufficient balance'}
        
        order = self.order_book.add_buy_order(
            buyer_id=buyer_id,
            energy_amount=energy_amount,
            max_price=max_price,
            duration_hours=duration_hours
        )
        
        # Try to match immediately
        matched = self.order_book.match_orders()
        
        return {
            'success': True,
            'order': order,
            'matched_trades': [t.to_dict() for t in matched]
        }
    
    def execute_trade_settlement(self, trade: EnergyTrade):
        """Execute settlement for a completed trade"""
        # Update seller balance
        seller_id = trade.seller_id
        buyer_id = trade.buyer_id
        
        # Transfer energy from seller to buyer
        self.user_balances[seller_id]['energy_kwh'] -= trade.energy_amount
        self.user_balances[buyer_id]['energy_kwh'] += trade.energy_amount
        
        # Transfer money from buyer to seller
        self.user_balances[buyer_id]['balance_usd'] -= trade.total_price
        self.user_balances[seller_id]['balance_usd'] += trade.total_price
        
        # Update statistics
        self.user_balances[seller_id]['total_earned'] += trade.total_price
        self.user_balances[buyer_id]['total_spent'] += trade.total_price
        
        # Move trade to completed
        trade.status = TradeStatus.COMPLETED
        trade.completed_at = datetime.utcnow()
        
        if trade in self.active_trades:
            self.active_trades.remove(trade)
        self.completed_trades.append(trade)
    
    def get_market_statistics(self) -> Dict:
        """Get overall market statistics"""
        total_volume = sum(t.energy_amount for t in self.completed_trades)
        total_value = sum(t.total_price for t in self.completed_trades)
        avg_price = total_value / total_volume if total_volume > 0 else 0
        
        return {
            'total_trades': len(self.completed_trades),
            'active_trades': len(self.active_trades),
            'total_volume_kwh': round(total_volume, 2),
            'total_value_usd': round(total_value, 2),
            'average_price_per_kwh': round(avg_price, 4),
            'registered_users': len(self.user_balances)
        }
    
    def get_user_portfolio(self, user_id: int) -> Optional[Dict]:
        """Get user's portfolio and trading history"""
        if user_id not in self.user_balances:
            return None
        
        balance = self.user_balances[user_id]
        
        # Get user's trades
        user_trades = [
            t for t in self.completed_trades 
            if t.seller_id == user_id or t.buyer_id == user_id
        ]
        
        return {
            'user_id': user_id,
            'energy_balance_kwh': balance['energy_kwh'],
            'cash_balance_usd': round(balance['balance_usd'], 2),
            'total_earned_usd': round(balance['total_earned'], 2),
            'total_spent_usd': round(balance['total_spent'], 2),
            'net_position_usd': round(balance['total_earned'] - balance['total_spent'], 2),
            'trades_completed': len(user_trades),
            'recent_trades': [t.to_dict() for t in user_trades[-5:]]
        }
