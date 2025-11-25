"""
Personal Finance Tracker - Core Models and Database
Demonstrates: Classes, Inheritance, Database, Iterators, Collections
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Set
import json


class Transaction:
    """Parent class for all financial transactions"""
    
    def __init__(self, transaction_id: int, amount: float, category: str, 
                 description: str, date: str):
        self.transaction_id = transaction_id
        self.amount = float(amount)  # Casting
        self.category = category.strip().title()  # String modification
        self.description = description
        self.date = date
    
    def __str__(self):
        """String representation"""
        return f"Transaction #{self.transaction_id}: ${self.amount:.2f} - {self.category}"
    
    def __iter__(self):
        """Make transaction iterable"""
        self._iter_fields = [
            ('ID', self.transaction_id),
            ('Amount', self.amount),
            ('Category', self.category),
            ('Description', self.description),
            ('Date', self.date)
        ]
        self._iter_index = 0
        return self
    
    def __next__(self):
        """Iterator implementation"""
        if self._iter_index >= len(self._iter_fields):
            raise StopIteration
        field = self._iter_fields[self._iter_index]
        self._iter_index += 1
        return field
    
    def to_dict(self) -> Dict:
        """Convert to dictionary - Collections"""
        return {
            'id': self.transaction_id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'date': self.date,
            'type': self.__class__.__name__
        }


class Income(Transaction):
    """Child class for income transactions"""
    
    def __init__(self, transaction_id: int, amount: float, category: str,
                 description: str, date: str, source: str = ""):
        super().__init__(transaction_id, amount, category, description, date)
        self.source = source
    
    def __str__(self):
        return f"Income #{self.transaction_id}: +${self.amount:.2f} from {self.source or self.category}"


class Expense(Transaction):
    """Child class for expense transactions"""
    
    def __init__(self, transaction_id: int, amount: float, category: str,
                 description: str, date: str, payment_method: str = ""):
        super().__init__(transaction_id, amount, category, description, date)
        self.payment_method = payment_method
    
    def __str__(self):
        return f"Expense #{self.transaction_id}: -${self.amount:.2f} for {self.category}"


class TransactionIterator:
    """Custom iterator for transaction filtering"""
    
    def __init__(self, transactions: List[Transaction], filter_func=None):
        self.transactions = transactions
        self.filter_func = filter_func or (lambda x: True)
        self.index = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        while self.index < len(self.transactions):
            transaction = self.transactions[self.index]
            self.index += 1
            if self.filter_func(transaction):
                return transaction
        raise StopIteration


class FinanceDatabase:
    """Database management using SQLite"""
    
    def __init__(self, db_path: str = "finance.db"):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                extra_data TEXT
            )
        """)
        self.connection.commit()
    
    def add_transaction(self, transaction: Transaction) -> int:
        """Save transaction to database"""
        extra_data = {}
        if isinstance(transaction, Income):
            extra_data['source'] = transaction.source
        elif isinstance(transaction, Expense):
            extra_data['payment_method'] = transaction.payment_method
        
        self.cursor.execute("""
            INSERT INTO transactions (type, amount, category, description, date, extra_data)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            transaction.__class__.__name__,
            transaction.amount,
            transaction.category,
            transaction.description,
            transaction.date,
            json.dumps(extra_data)
        ))
        self.connection.commit()
        last_id = self.cursor.lastrowid
        return last_id if last_id is not None else 0
    
    def get_all_transactions(self) -> List[Transaction]:
        """Load all transactions"""
        self.cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        transactions = []
        
        for row in self.cursor.fetchall():
            tid, ttype, amount, category, description, date, extra_data = row
            extra = json.loads(extra_data) if extra_data else {}
            
            if ttype == "Income":
                transaction = Income(tid, amount, category, description, date, 
                                   extra.get('source', ''))
            else:
                transaction = Expense(tid, amount, category, description, date,
                                    extra.get('payment_method', ''))
            transactions.append(transaction)
        
        return transactions
    
    def get_transactions_by_category(self, category: str) -> List[Transaction]:
        """Filter transactions by category"""
        all_trans = self.get_all_transactions()
        # Using lambda for filtering
        return list(filter(lambda t: t.category.lower() == category.lower(), all_trans))
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics - Collections: Dict"""
        self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as total_expenses,
                COUNT(*) as transaction_count
            FROM transactions
        """)
        row = self.cursor.fetchone()
        
        return {
            'total_income': row[0] or 0,
            'total_expenses': row[1] or 0,
            'net_balance': (row[0] or 0) - (row[1] or 0),
            'transaction_count': row[2] or 0
        }
    
    def get_category_summary(self) -> List[Tuple[str, float]]:
        """Get spending by category - Collections: List, Tuple"""
        self.cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE type='Expense'
            GROUP BY category
            ORDER BY total DESC
        """)
        return self.cursor.fetchall()
    
    def get_categories(self) -> Set[str]:
        """Get unique categories - Collections: Set"""
        self.cursor.execute("SELECT DISTINCT category FROM transactions")
        return {row[0] for row in self.cursor.fetchall()}
    
    def delete_transaction(self, transaction_id: int):
        """Delete a transaction"""
        self.cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
        self.connection.commit()
    
    def clear_all(self):
        """Clear all data"""
        self.cursor.execute("DELETE FROM transactions")
        self.connection.commit()
    
    def close(self):
        """Close database connection"""
        self.connection.close()
