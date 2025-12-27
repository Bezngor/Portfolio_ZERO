#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database migration script
Migrates old database to new schema with categories and trip statuses
"""

import sqlite3
import os
import sys

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = "travel_wallet.db"

def migrate_database():
    """Migrate database to new schema"""
    if not os.path.exists(DB_PATH):
        print("✅ No existing database found. New database will be created automatically.")
        return
    
    print("🔄 Migrating database...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if trips table has status column
        cursor.execute("PRAGMA table_info(trips)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'status' not in columns:
            print("  ➕ Adding status column to trips...")
            cursor.execute("ALTER TABLE trips ADD COLUMN status TEXT DEFAULT 'active'")
            cursor.execute("ALTER TABLE trips ADD COLUMN closed_at TIMESTAMP")
        
        # Check if expense_categories table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expense_categories'")
        if not cursor.fetchone():
            print("  ➕ Creating expense_categories table...")
            cursor.execute("""
                CREATE TABLE expense_categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    icon TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default categories
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
            cursor.executemany(
                "INSERT INTO expense_categories (name, icon) VALUES (?, ?)",
                default_categories
            )
        
        # Check if expenses table has category_id column
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'category_id' not in columns:
            print("  ➕ Adding category_id column to expenses...")
            cursor.execute("ALTER TABLE expenses ADD COLUMN category_id INTEGER DEFAULT 8")
        
        # Check if currency_cache table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='currency_cache'")
        if not cursor.fetchone():
            print("  ➕ Creating currency_cache table...")
            cursor.execute("""
                CREATE TABLE currency_cache (
                    country_name TEXT PRIMARY KEY,
                    currency_code TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("🗄  Database Migration")
    print("=" * 50)
    migrate_database()
    print("=" * 50)

