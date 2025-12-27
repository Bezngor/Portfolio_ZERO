import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import threading


class Database:
    """Database manager for the travel wallet bot"""
    
    def __init__(self, db_path: str = "travel_wallet.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        with self._lock:
            # check_same_thread=False allows multi-threaded access
            # timeout=30 increases wait time for locked database
            conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0,
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
    
    def init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    active_trip_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Trips table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    trip_name TEXT NOT NULL,
                    from_country TEXT NOT NULL,
                    to_country TEXT NOT NULL,
                    from_currency TEXT NOT NULL,
                    to_currency TEXT NOT NULL,
                    exchange_rate REAL NOT NULL,
                    initial_amount_home REAL NOT NULL,
                    initial_amount_foreign REAL NOT NULL,
                    current_balance_home REAL NOT NULL,
                    current_balance_foreign REAL NOT NULL,
                    is_custom_rate INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Expense categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expense_categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    icon TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default categories if not exists
            default_categories = [
                ('Еда и напитки', '🍽'),
                ('Транспорт', '🚕'),
                ('Жильё', '🏨'),
                ('Развлечения', '🎭'),
                ('Покупки', '🛍'),
                ('Здоровье', '💊'),
                ('Связь', '📱'),
                ('Прочее', '📦')
            ]
            for cat_name, cat_icon in default_categories:
                cursor.execute("""
                    INSERT OR IGNORE INTO expense_categories (name, icon)
                    VALUES (?, ?)
                """, (cat_name, cat_icon))
            
            # Expenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trip_id INTEGER NOT NULL,
                    category_id INTEGER DEFAULT 8,
                    amount_foreign REAL NOT NULL,
                    amount_home REAL NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trip_id) REFERENCES trips (trip_id),
                    FOREIGN KEY (category_id) REFERENCES expense_categories (category_id)
                )
            """)
            
            # Currency cache table (for auto-detection)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS currency_cache (
                    country_name TEXT PRIMARY KEY,
                    currency_code TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User states table (for conversation flow)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id INTEGER PRIMARY KEY,
                    state TEXT,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    # User operations
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def set_active_trip(self, user_id: int, trip_id: int):
        """Set active trip for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET active_trip_id = ? WHERE user_id = ?", (trip_id, user_id))
    
    # Trip operations
    def create_trip(self, user_id: int, trip_name: str, from_country: str, to_country: str,
                    from_currency: str, to_currency: str, exchange_rate: float,
                    initial_amount_home: float, initial_amount_foreign: float, 
                    is_custom_rate: bool = False) -> int:
        """Create a new trip"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trips (user_id, trip_name, from_country, to_country, 
                                 from_currency, to_currency, exchange_rate,
                                 initial_amount_home, initial_amount_foreign,
                                 current_balance_home, current_balance_foreign, is_custom_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, trip_name, from_country, to_country, from_currency, to_currency,
                  exchange_rate, initial_amount_home, initial_amount_foreign,
                  initial_amount_home, initial_amount_foreign, 1 if is_custom_rate else 0))
            
            trip_id = cursor.lastrowid
            
            # Set as active trip if it's the first trip
            cursor.execute("SELECT COUNT(*) as cnt FROM trips WHERE user_id = ?", (user_id,))
            if cursor.fetchone()["cnt"] == 1:
                self.set_active_trip(user_id, trip_id)
            
            return trip_id
    
    def get_trip(self, trip_id: int) -> Optional[Dict]:
        """Get trip by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trips WHERE trip_id = ?", (trip_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_trips(self, user_id: int) -> List[Dict]:
        """Get all trips for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_trip(self, user_id: int) -> Optional[Dict]:
        """Get active trip for user"""
        user = self.get_user(user_id)
        if user and user.get('active_trip_id'):
            return self.get_trip(user['active_trip_id'])
        return None
    
    def update_trip_balance(self, trip_id: int, balance_home: float, balance_foreign: float):
        """Update trip balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trips 
                SET current_balance_home = ?, current_balance_foreign = ?
                WHERE trip_id = ?
            """, (balance_home, balance_foreign, trip_id))
    
    def update_trip_rate(self, trip_id: int, new_rate: float, is_custom: bool = True):
        """Update exchange rate for a trip"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trips 
                SET exchange_rate = ?, is_custom_rate = ?
                WHERE trip_id = ?
            """, (new_rate, 1 if is_custom else 0, trip_id))
    
    def close_trip(self, trip_id: int):
        """Close a trip"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trips 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP
                WHERE trip_id = ?
            """, (trip_id,))
    
    def reopen_trip(self, trip_id: int):
        """Reopen a closed trip"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trips 
                SET status = 'active', closed_at = NULL
                WHERE trip_id = ?
            """, (trip_id,))
    
    def get_user_trips_by_status(self, user_id: int, status: str = 'active') -> List[Dict]:
        """Get trips by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trips 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (user_id, status))
            return [dict(row) for row in cursor.fetchall()]
    
    # Currency cache operations
    def cache_currency(self, country_name: str, currency_code: str):
        """Cache country-currency mapping"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO currency_cache (country_name, currency_code, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (country_name, currency_code))
    
    def get_cached_currency(self, country_name: str) -> Optional[str]:
        """Get cached currency for country"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT currency_code FROM currency_cache 
                WHERE country_name = ?
            """, (country_name,))
            row = cursor.fetchone()
            return row['currency_code'] if row else None
    
    # Category operations
    def get_all_categories(self) -> List[Dict]:
        """Get all expense categories"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expense_categories ORDER BY category_id")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_category(self, category_id: int) -> Optional[Dict]:
        """Get category by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expense_categories WHERE category_id = ?", (category_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Expense operations
    def add_expense(self, trip_id: int, amount_foreign: float, amount_home: float, 
                    category_id: int = 8, description: str = None):
        """Add an expense"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (trip_id, category_id, amount_foreign, amount_home, description)
                VALUES (?, ?, ?, ?, ?)
            """, (trip_id, category_id, amount_foreign, amount_home, description))
            return cursor.lastrowid
    
    def get_trip_expenses(self, trip_id: int, limit: int = 10) -> List[Dict]:
        """Get expenses for a trip"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, c.name as category_name, c.icon as category_icon
                FROM expenses e
                LEFT JOIN expense_categories c ON e.category_id = c.category_id
                WHERE e.trip_id = ? 
                ORDER BY e.created_at DESC 
                LIMIT ?
            """, (trip_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_expenses_by_category(self, trip_id: int, category_id: int) -> List[Dict]:
        """Get expenses by category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, c.name as category_name, c.icon as category_icon
                FROM expenses e
                LEFT JOIN expense_categories c ON e.category_id = c.category_id
                WHERE e.trip_id = ? AND e.category_id = ?
                ORDER BY e.created_at DESC
            """, (trip_id, category_id))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trip_expenses_grouped(self, trip_id: int) -> List[Dict]:
        """Get expenses grouped by category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.category_id,
                    c.name as category_name,
                    c.icon as category_icon,
                    COUNT(e.expense_id) as count,
                    COALESCE(SUM(e.amount_foreign), 0) as total_foreign,
                    COALESCE(SUM(e.amount_home), 0) as total_home
                FROM expense_categories c
                LEFT JOIN expenses e ON c.category_id = e.category_id AND e.trip_id = ?
                GROUP BY c.category_id, c.name, c.icon
                HAVING count > 0
                ORDER BY total_foreign DESC
            """, (trip_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trip_total_expenses(self, trip_id: int) -> Dict[str, float]:
        """Get total expenses for a trip"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(amount_foreign), 0) as total_foreign,
                    COALESCE(SUM(amount_home), 0) as total_home
                FROM expenses 
                WHERE trip_id = ?
            """, (trip_id,))
            row = cursor.fetchone()
            return dict(row) if row else {"total_foreign": 0, "total_home": 0}
    
    # State management
    def set_user_state(self, user_id: int, state: str, data: Dict = None):
        """Set user conversation state"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_states (user_id, state, data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, state, json.dumps(data) if data else None))
    
    def get_user_state(self, user_id: int) -> Optional[Dict]:
        """Get user conversation state"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_states WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('data'):
                    result['data'] = json.loads(result['data'])
                return result
            return None
    
    def clear_user_state(self, user_id: int):
        """Clear user conversation state"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_states WHERE user_id = ?", (user_id,))

