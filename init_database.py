import sqlite3
import os

# Remove old database if it exists
if os.path.exists('database.db'):
    try:
        os.remove('database.db')
        print("Removed old database")
    except:
        print("Could not remove old database (it's in use)")

# Create new database
conn = sqlite3.connect('database.db')
c = conn.cursor()

try:
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            monthly_budget REAL,
            last_activity TEXT,
            send_daily_summary INTEGER DEFAULT 0,
            send_weekly_summary INTEGER DEFAULT 1,
            send_limit_alert INTEGER DEFAULT 1,
            send_reminder INTEGER DEFAULT 1,
            last_expense_date TEXT,
            device_token TEXT,
            is_admin INTEGER DEFAULT 0,
            total_savings_goal REAL DEFAULT 0,
            current_savings REAL DEFAULT 0
        )
    ''')
    print("✓ Users table created")

    # Expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            amount REAL,
            category TEXT,
            date TEXT,
            created_at TEXT,
            receipt_file TEXT,
            is_duplicate_flagged INTEGER DEFAULT 0,
            duplicate_reason TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    print("✓ Expenses table created")

    # Password resets table
    c.execute('''
        CREATE TABLE IF NOT EXISTS password_resets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            expires_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    print("✓ Password resets table created")

    # Email logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email_type TEXT,
            sent_at TEXT,
            subject TEXT,
            status TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    print("✓ Email logs table created")

    # Backup logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS backup_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_date TEXT,
            backup_file TEXT,
            backup_size TEXT,
            status TEXT
        )
    ''')
    print("✓ Backup logs table created")

    # Savings goals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS savings_goals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_name TEXT,
            target_amount REAL,
            current_amount REAL,
            category TEXT,
            deadline TEXT,
            created_at TEXT,
            status TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    print("✓ Savings goals table created")

    conn.commit()
    print("\n✅ Database initialized successfully!")
    print("You can now run: python app.py")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
