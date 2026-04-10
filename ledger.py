"""
Blockchain-inspired Ledger System for EnergyChain
Provides immutable transaction records with hash chaining
"""
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional


class Transaction:
    """Represents a single energy trade transaction"""
    
    def __init__(
        self,
        transaction_id: int,
        trade_id: int,
        seller_id: int,
        buyer_id: int,
        energy_amount: float,
        price: float,
        timestamp: datetime = None
    ):
        self.transaction_id = transaction_id
        self.trade_id = trade_id
        self.seller_id = seller_id
        self.buyer_id = buyer_id
        self.energy_amount = energy_amount
        self.price = price
        self.timestamp = timestamp or datetime.utcnow()
        self.hash = ""
        self.previous_hash = ""
    
    def to_dict(self) -> Dict:
        return {
            'transaction_id': self.transaction_id,
            'trade_id': self.trade_id,
            'seller_id': self.seller_id,
            'buyer_id': self.buyer_id,
            'energy_amount': self.energy_amount,
            'price': self.price,
            'timestamp': self.timestamp.isoformat()
        }
    
    def calculate_hash(self, previous_hash: str) -> str:
        """Calculate SHA-256 hash of transaction data"""
        self.previous_hash = previous_hash
        
        data = json.dumps({
            'transaction_id': self.transaction_id,
            'trade_id': self.trade_id,
            'seller_id': self.seller_id,
            'buyer_id': self.buyer_id,
            'energy_amount': self.energy_amount,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'previous_hash': previous_hash
        }, sort_keys=True).encode()
        
        self.hash = hashlib.sha256(data).hexdigest()
        return self.hash


class EnergyLedger:
    """
    Blockchain-inspired ledger for recording energy trades
    Features:
    - Immutable transaction records
    - Hash chaining for integrity verification
    - Distributed consensus ready
    """
    
    def __init__(self):
        self.chain: List[Transaction] = []
        self.pending_transactions: List[Transaction] = []
        self.transaction_counter = 0
        
        # Create genesis block
        self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the first block in the chain"""
        genesis = Transaction(
            transaction_id=0,
            trade_id=0,
            seller_id=0,
            buyer_id=0,
            energy_amount=0,
            price=0,
            timestamp=datetime(2024, 1, 1, 0, 0, 0)
        )
        genesis.hash = genesis.calculate_hash("0" * 64)
        self.chain.append(genesis)
    
    def get_latest_hash(self) -> str:
        """Get hash of the most recent transaction"""
        if not self.chain:
            return "0" * 64
        return self.chain[-1].hash
    
    def add_transaction(
        self,
        trade_id: int,
        seller_id: int,
        buyer_id: int,
        energy_amount: float,
        price: float
    ) -> Transaction:
        """Add a new transaction to the ledger"""
        self.transaction_counter += 1
        
        transaction = Transaction(
            transaction_id=self.transaction_counter,
            trade_id=trade_id,
            seller_id=seller_id,
            buyer_id=buyer_id,
            energy_amount=energy_amount,
            price=price
        )
        
        # Calculate hash and add to chain
        previous_hash = self.get_latest_hash()
        transaction.calculate_hash(previous_hash)
        
        self.chain.append(transaction)
        return transaction
    
    def verify_chain(self) -> bool:
        """Verify the integrity of the entire chain"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # Verify previous hash linkage
            if current.previous_hash != previous.hash:
                print(f"Hash mismatch at transaction {current.transaction_id}")
                return False
            
            # Verify current hash
            expected_hash = current.calculate_hash(current.previous_hash)
            if current.hash != expected_hash:
                print(f"Invalid hash at transaction {current.transaction_id}")
                return False
        
        return True
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Retrieve a specific transaction by ID"""
        for tx in self.chain:
            if tx.transaction_id == transaction_id:
                return tx
        return None
    
    def get_transactions_by_trade(self, trade_id: int) -> List[Transaction]:
        """Get all transactions related to a specific trade"""
        return [tx for tx in self.chain if tx.trade_id == trade_id]
    
    def get_user_transactions(self, user_id: int) -> List[Transaction]:
        """Get all transactions where user is either buyer or seller"""
        return [
            tx for tx in self.chain 
            if tx.seller_id == user_id or tx.buyer_id == user_id
        ]
    
    def get_chain_summary(self) -> Dict:
        """Get summary statistics of the ledger"""
        if len(self.chain) <= 1:
            return {
                'total_transactions': 0,
                'total_energy_traded': 0,
                'total_value': 0,
                'unique_sellers': 0,
                'unique_buyers': 0
            }
        
        # Exclude genesis block
        real_transactions = self.chain[1:]
        
        total_energy = sum(tx.energy_amount for tx in real_transactions)
        total_value = sum(tx.price for tx in real_transactions)
        unique_sellers = len(set(tx.seller_id for tx in real_transactions))
        unique_buyers = len(set(tx.buyer_id for tx in real_transactions))
        
        return {
            'total_transactions': len(real_transactions),
            'total_energy_traded_kwh': round(total_energy, 2),
            'total_value_usd': round(total_value, 2),
            'unique_sellers': unique_sellers,
            'unique_buyers': unique_buyers,
            'chain_length': len(self.chain),
            'latest_hash': self.get_latest_hash()[:16] + '...'
        }
    
    def export_chain(self) -> List[Dict]:
        """Export entire chain as list of dictionaries"""
        return [tx.to_dict() for tx in self.chain]
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """Get most recent transactions"""
        recent = self.chain[-limit:] if len(self.chain) > limit else self.chain[1:]
        return [tx.to_dict() for tx in recent]
