from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import secrets
import string
import re
import json
import os
import shutil
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from PIL import Image
import hashlib

load_dotenv()

app = Flask(__name__)
app.secret_key = "secretkey123"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# File Upload Configuration
UPLOAD_FOLDER = 'static/receipts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Email Configuration (Set environment variables or use defaults)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@expensetracker.com')

mail = Mail(app)

# Initialize scheduler for background tasks
scheduler = BackgroundScheduler()

# Category detection keywords
CATEGORY_KEYWORDS = {
    'Food': ['grocery', 'restaurant', 'food', 'pizza', 'burger', 'cafe', 'lunch', 'dinner', 'breakfast', 'snack', 'bakery'],
    'Transport': ['uber', 'taxi', 'bus', 'gas', 'petrol', 'fuel', 'train', 'metro', 'ticket', 'parking'],
    'Bills': ['electricity', 'water', 'internet', 'phone', 'bill', 'rent', 'mortgage', 'insurance'],
    'Shopping': ['mall', 'store', 'amazon', 'flipkart', 'clothes', 'shoe', 'shopping', 'buy', 'purchase'],
    'Entertainment': ['movie', 'cinema', 'concert', 'music', 'game', 'netflix', 'play', 'show', 'ticket'],
    'Health': ['doctor', 'hospital', 'pharmacy', 'medicine', 'health', 'clinic', 'dental', 'fitness', 'gym'],
    'Education': ['school', 'college', 'university', 'course', 'tuition', 'book', 'education', 'class', 'coaching']
}

def detect_category(title):
    """Auto-detect category based on title keywords"""
    title_lower = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return category
    return 'Other'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_receipt(file, user_id, expense_id):
    """Save receipt file and return filename"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Create user folder
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"expense_{expense_id}_{datetime.now().timestamp()}.{ext}"
    filepath = os.path.join(user_folder, filename)
    
    # Compress image if it's an image file
    if ext in {'jpg', 'jpeg', 'png', 'gif'}:
        img = Image.open(file)
        img.thumbnail((1024, 1024))
        img.save(filepath, quality=85)
    else:
        file.save(filepath)
    
    return os.path.join(str(user_id), filename)

# ==================== FRAUD & DUPLICATE DETECTION ====================

def detect_duplicate_expense(user_id, title, amount, category, date):
    """Detect potential duplicate or fraud expense"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Check for exact duplicates (same title, amount, category within 1 hour)
    one_hour_ago = (datetime.fromisoformat(datetime.now().isoformat()) - timedelta(hours=1)).isoformat()
    c.execute("""
        SELECT id, created_at FROM expenses 
        WHERE user_id=? AND title=? AND amount=? AND category=? AND date=? AND created_at > ?
        ORDER BY created_at DESC LIMIT 1
    """, (user_id, title, amount, category, date, one_hour_ago))
    
    duplicate = c.fetchone()
    conn.close()
    
    if duplicate:
        return True, f"Duplicate detected: {title} for ₹{amount} was added {duplicate[1]}"
    
    return False, None

def detect_fraud_anomaly(user_id, amount, category):
    """Detect unusual spending patterns"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get average spending in this category for this user
    c.execute("""
        SELECT AVG(amount), MAX(amount) FROM expenses 
        WHERE user_id=? AND category=?
    """, (user_id, category))
    
    result = c.fetchone()
    conn.close()
    
    if result[0] is None:
        return False, None
    
    avg_amount, max_amount = result
    
    # If amount is more than 300% of average, flag as potential fraud
    if amount > (avg_amount * 3):
        return True, f"Unusual spending: ₹{amount} is 3x higher than your average {category} expense (₹{avg_amount:.2f})"
    
    return False, None

# ==================== DATABASE SETUP ====================

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
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
    
    # Savings goals table (NEW)
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
    
    conn.commit()
    conn.close()

    # Ensure columns exist (simple migration)
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    columns_to_add = [
        ("email", "TEXT", "users"),
        ("daily_limit", "REAL", "users"),
        ("monthly_budget", "REAL", "users"),
        ("last_activity", "TEXT", "users"),
        ("send_daily_summary", "INTEGER DEFAULT 0", "users"),
        ("send_weekly_summary", "INTEGER DEFAULT 1", "users"),
        ("send_limit_alert", "INTEGER DEFAULT 1", "users"),
        ("send_reminder", "INTEGER DEFAULT 1", "users"),
        ("last_expense_date", "TEXT", "users"),
        ("device_token", "TEXT", "users"),
        ("is_admin", "INTEGER DEFAULT 0", "users"),
        ("total_savings_goal", "REAL DEFAULT 0", "users"),
        ("current_savings", "REAL DEFAULT 0", "users"),
        ("created_at", "TEXT", "expenses"),
        ("receipt_file", "TEXT", "expenses"),
        ("is_duplicate_flagged", "INTEGER DEFAULT 0", "expenses"),
        ("duplicate_reason", "TEXT", "expenses"),
    ]
    
    for col_name, col_type, table_name in columns_to_add:
        try:
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    
    conn.close()

# ==================== EMAIL FUNCTIONS ====================

def send_email(to_email, subject, html_body):
    """Send email with error handling"""
    try:
        msg = Message(subject=subject, recipients=[to_email], html=html_body)
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False, str(e)

def send_daily_summary(user_id, user_email, username):
    """Send daily spending summary"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("""
        SELECT SUM(amount), COUNT(*), GROUP_CONCAT(DISTINCT category)
        FROM expenses WHERE user_id=? AND date=?
    """, (user_id, today))
    
    result = c.fetchone()
    total_today = result[0] or 0
    count = result[1] or 0
    categories = result[2] or "None"
    conn.close()
    
    subject = f"📊 Your Daily Spending Summary - {today}"
    
    html_body = f"""
    <h2>Daily Spending Summary</h2>
    <p>Hi {username},</p>
    <p><strong>Date:</strong> {today}</p>
    <p><strong>Total Spent:</strong> ₹{total_today:.2f}</p>
    <p><strong>Number of Expenses:</strong> {count}</p>
    <p><strong>Categories:</strong> {categories}</p>
    <p><a href="http://127.0.0.1:5000/dashboard">View Detailed Dashboard</a></p>
    """
    
    success, msg = send_email(user_email, subject, html_body)
    if success:
        log_email(user_id, "daily_summary", subject, "sent")
    return success

def send_weekly_summary(user_id, user_email, username):
    """Send weekly spending summary"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("""
        SELECT SUM(amount), COUNT(*), GROUP_CONCAT(DISTINCT category)
        FROM expenses WHERE user_id=? AND date BETWEEN ? AND ?
    """, (user_id, week_ago, today))
    
    result = c.fetchone()
    total_week = result[0] or 0
    count = result[1] or 0
    categories = result[2] or "None"
    
    c.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses WHERE user_id=? AND date BETWEEN ? AND ?
        GROUP BY category ORDER BY total DESC LIMIT 1
    """, (user_id, week_ago, today))
    
    top_cat = c.fetchone()
    top_category = f"{top_cat[0]} (₹{top_cat[1]:.2f})" if top_cat else "N/A"
    
    conn.close()
    
    subject = f"📈 Your Weekly Spending Summary ({week_ago} to {today})"
    
    html_body = f"""
    <h2>Weekly Spending Summary</h2>
    <p>Hi {username},</p>
    <p><strong>Period:</strong> {week_ago} to {today}</p>
    <p><strong>Total Spent:</strong> ₹{total_week:.2f}</p>
    <p><strong>Number of Expenses:</strong> {count}</p>
    <p><strong>Top Category:</strong> {top_category}</p>
    <p><strong>Categories Used:</strong> {categories}</p>
    <p><a href="http://127.0.0.1:5000/dashboard">View Detailed Dashboard</a></p>
    """
    
    success, msg = send_email(user_email, subject, html_body)
    if success:
        log_email(user_id, "weekly_summary", subject, "sent")
    return success

def send_spend_limit_alert(user_id, email, current_total, budget):
    """Send budget limit alert"""
    pct = (current_total / budget * 100) if budget > 0 else 0
    subject = f"⚠️ Budget Alert: You've spent {pct:.1f}% of your monthly budget!"
    
    html_body = f"""
    <h2>Budget Alert</h2>
    <p>Hi,</p>
    <p>You've spent <strong>₹{current_total:.2f}</strong> out of your <strong>₹{budget:.2f}</strong> monthly budget.</p>
    <p>That's <strong>{pct:.1f}%</strong> of your budget!</p>
    <p><a href="http://127.0.0.1:5000/dashboard">Review your spending</a></p>
    """
    
    send_email(email, subject, html_body)
    log_email(user_id, "budget_alert", subject, "sent")


def send_daily_limit_alert(user_id, email, today_total, daily_limit):
    """Send email alert when daily limit is reached"""
    subject = f"⚠️ Daily Limit Reached: You've spent ₹{today_total:.2f} today"
    pct = (today_total / daily_limit * 100) if daily_limit and daily_limit > 0 else 0
    html_body = f"""
    <h2>Daily Limit Alert</h2>
    <p>Hi,</p>
    <p>You've spent <strong>₹{today_total:.2f}</strong> today.</p>
    <p>Your daily limit is <strong>₹{daily_limit:.2f}</strong>. That's <strong>{pct:.1f}%</strong> of your limit.</p>
    <p><a href=\"http://127.0.0.1:5000/dashboard\">View Dashboard</a></p>
    """
    send_email(email, subject, html_body)
    log_email(user_id, "daily_limit_alert", subject, "sent")


def send_push_notification(user_id, message):
    """Placeholder push notification sender. Uses device_token if available.
    This is a lightweight implementation: if a device token exists it logs a push event
    and stores it in email_logs table as a record with type 'push_notification'.
    """
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT device_token FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        device_token = row[0] if row else None
        # In a real system you'd call a push provider here (FCM/APNs) using device_token
        if device_token:
            print(f"Push to {device_token}: {message}")
            # Log as a notification (reusing email_logs for simplicity)
            c.execute("INSERT INTO email_logs (user_id, email_type, sent_at, subject, status) VALUES (?, ?, ?, ?, ?)",
                      (user_id, 'push_notification', datetime.now().isoformat(), message, 'sent'))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Push error: {e}")

def send_expense_reminder(user_id, user_email, username, days_since):
    """Send reminder to add expense"""
    subject = f"💰 Reminder: No expenses recorded for {days_since} days"
    
    html_body = f"""
    <h2>Expense Entry Reminder</h2>
    <p>Hi {username},</p>
    <p>We haven't seen any expense entries from you in the last <strong>{days_since} days</strong>.</p>
    <p>Track your daily spending to better manage your finances!</p>
    <p><a href="http://127.0.0.1:5000/add">Add an Expense</a> | <a href="http://127.0.0.1:5000/dashboard">View Dashboard</a></p>
    """
    
    success, msg = send_email(user_email, subject, html_body)
    if success:
        log_email(user_id, "expense_reminder", subject, "sent")
    return success

def log_email(user_id, email_type, subject, status):
    """Log email sending"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO email_logs (user_id, email_type, sent_at, subject, status)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, email_type, datetime.now().isoformat(), subject, status))
    conn.commit()
    conn.close()

# ==================== BACKUP FUNCTIONS ====================

def create_backup():
    """Create database backup"""
    try:
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'database_backup_{timestamp}.db')
        
        shutil.copy('database.db', backup_file)
        
        size = os.path.getsize(backup_file) / 1024  # KB
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO backup_logs (backup_date, backup_file, backup_size, status)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), backup_file, f"{size:.2f} KB", "success"))
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Backup error: {str(e)}")
        return False

def cleanup_old_backups(days=30):
    """Remove backups older than specified days"""
    try:
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for file in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, file)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
    except Exception as e:
        print(f"Cleanup error: {str(e)}")

# ==================== SCHEDULER FUNCTIONS ====================

def check_and_send_summaries():
    """Check and send daily/weekly summaries"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, send_daily_summary, send_weekly_summary FROM users WHERE email IS NOT NULL")
    users = c.fetchall()
    conn.close()
    
    for user in users:
        user_id, username, email, send_daily, send_weekly = user
        
        if send_daily:
            send_daily_summary(user_id, email, username)
        
        if send_weekly and datetime.now().weekday() == 6:  # Sunday
            send_weekly_summary(user_id, email, username)

def check_and_send_reminders():
    """Check and send expense reminders"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, send_reminder, last_expense_date FROM users WHERE email IS NOT NULL AND send_reminder=1")
    users = c.fetchall()
    conn.close()
    
    for user in users:
        user_id, username, email, send_reminder, last_expense_date = user
        
        if not last_expense_date:
            continue
        
        last_date = datetime.fromisoformat(last_expense_date)
        days_since = (datetime.now() - last_date).days
        
        if days_since >= 2:
            send_expense_reminder(user_id, email, username, days_since)

def check_budget_limits():
    """Check and send budget alerts"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, email, monthly_budget FROM users WHERE email IS NOT NULL AND send_limit_alert=1 AND monthly_budget > 0")
    users = c.fetchall()
    conn.close()
    
    for user in users:
        user_id, email, budget = user
        
        if not email:
            continue
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        current_month = datetime.now().strftime('%Y-%m')
        c.execute("""
            SELECT SUM(amount) FROM expenses 
            WHERE user_id=? AND date LIKE ?
        """, (user_id, f"{current_month}%"))
        
        result = c.fetchone()
        current_total = result[0] or 0
        conn.close()
        
        pct = (current_total / budget * 100) if budget > 0 else 0
        if pct >= 80:
            send_spend_limit_alert(user_id, email, current_total, budget)

def start_scheduler():
    """Start background scheduler"""
    if not scheduler.running:
        scheduler.add_job(check_and_send_summaries, 'cron', hour=8, minute=0)
        scheduler.add_job(check_and_send_reminders, 'interval', hours=6)
        scheduler.add_job(check_budget_limits, 'interval', hours=1)
        scheduler.add_job(create_backup, 'cron', hour=2, minute=0)
        scheduler.add_job(cleanup_old_backups, 'cron', day_of_week=0, hour=3, minute=0)
        scheduler.start()
        print("Scheduler started!")

# ==================== SESSION & MIDDLEWARE ====================

@app.before_request
def before_request():
    """Track last activity and check session timeout"""
    if 'user_id' in session:
        session.permanent = True
        last_activity = session.get('last_activity')
        if last_activity:
            last_time = datetime.fromisoformat(last_activity)
            if datetime.now() - last_time > timedelta(minutes=30):
                session.clear()
                return redirect('/login')
        session['last_activity'] = datetime.now().isoformat()
    
    if 'user_id' in session:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('UPDATE users SET last_activity=? WHERE id=?', (datetime.now().isoformat(), session['user_id']))
        conn.commit()
        conn.close()

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        hashed_password = generate_password_hash(password)
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO users (username, password, email, send_weekly_summary, send_limit_alert, send_reminder, is_admin) 
                VALUES (?, ?, ?, 1, 1, 1, 0)
            """, (username, hashed_password, email))
            conn.commit()
            return redirect('/login')
        except:
            return "Username already exists!"
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, password, username FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = user[2]
            session.permanent = True
            session['last_activity'] = datetime.now().isoformat()
            
            # Check if admin
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT is_admin FROM users WHERE id=?", (user[0],))
            is_admin = c.fetchone()[0]
            conn.close()
            
            if is_admin:
                return redirect('/admin/dashboard')
            return redirect('/dashboard')
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Current month expenses
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("""
        SELECT SUM(amount), COUNT(*), GROUP_CONCAT(category) FROM expenses 
        WHERE user_id=? AND date LIKE ? AND is_duplicate_flagged=0
    """, (user_id, f"{current_month}%"))
    result = c.fetchone()
    total = result[0] or 0
    count = result[1] or 0
    categories = result[2] or ""
    
    # Get user budget
    c.execute("SELECT monthly_budget FROM users WHERE id=?", (user_id,))
    budget = c.fetchone()[0] or 0
    
    # Get all expenses this month
    c.execute("""
        SELECT id, title, amount, category, date, receipt_file, is_duplicate_flagged, duplicate_reason 
        FROM expenses 
        WHERE user_id=? AND date LIKE ? 
        ORDER BY date DESC
    """, (user_id, f"{current_month}%"))
    expenses = c.fetchall()
    
    # Get flagged duplicates
    c.execute("""
        SELECT id, title, amount, duplicate_reason, date 
        FROM expenses 
        WHERE user_id=? AND is_duplicate_flagged=1 AND date LIKE ?
        ORDER BY date DESC
    """, (user_id, f"{current_month}%"))
    flagged_expenses = c.fetchall()
    
    # Get savings goals
    c.execute("""
        SELECT id, goal_name, target_amount, current_amount, deadline, status 
        FROM savings_goals 
        WHERE user_id=? 
        ORDER BY deadline ASC
    """, (user_id,))
    savings_goals = c.fetchall()
    
    # Pass filter/query params back to template so inputs stay in sync
    req_range = request.args.get('range')
    start_date_q = request.args.get('start_date')
    end_date_q = request.args.get('end_date')
    q = request.args.get('q')
    category_q = request.args.get('category')

    # Get today's total and daily limit for progress bar
    try:
        c.execute("SELECT daily_limit FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        daily_limit = row[0] if row else None
    except Exception:
        daily_limit = None

    try:
        today = datetime.now().date().isoformat()
        c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND date=? AND is_duplicate_flagged=0", (user_id, today))
        trow = c.fetchone()
        today_total = trow[0] or 0
    except Exception:
        today_total = 0

    conn.close()
    # Pass any immediate warning (from add expense) to template
    warning = request.args.get('warning', '')

    return render_template('dashboard.html', 
        expenses=expenses,
        total=total,
        count=count,
        budget=budget,
        monthly_budget=budget,
        current_month_total=total,
        remaining=budget - total,
        flagged_expenses=flagged_expenses,
        savings_goals=savings_goals,
        warning=warning,
        daily_limit=daily_limit,
        today_total=today_total,
        username=session.get('username', ''),
        range=req_range,
        start_date=start_date_q,
        end_date=end_date_q,
        q=q,
        category=category_q
    )

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        category = request.form.get('category', detect_category(title))
        date = request.form['date']
        
        # Check for duplicates
        is_dup, dup_msg = detect_duplicate_expense(user_id, title, amount, category, date)
        is_fraud, fraud_msg = detect_fraud_anomaly(user_id, amount, category)
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        # Check daily total BEFORE inserting so we can detect crossing
        daily_limit = None
        try:
            c.execute("SELECT daily_limit, email FROM users WHERE id=?", (user_id,))
            row = c.fetchone()
            if row:
                daily_limit = row[0]
                user_email = row[1]
            else:
                user_email = None
        except Exception:
            daily_limit = None
            user_email = None

        today = datetime.now().date().isoformat()
        try:
            c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND date=? AND is_duplicate_flagged=0", (user_id, today))
            pre = c.fetchone()
            today_total_before = pre[0] or 0
        except Exception:
            today_total_before = 0

        # Insert expense
        c.execute("""
            INSERT INTO expenses (user_id, title, amount, category, date, created_at, is_duplicate_flagged, duplicate_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, amount, category, date, datetime.now().isoformat(), 1 if (is_dup or is_fraud) else 0, 
              dup_msg or fraud_msg or ""))
        
        conn.commit()
        expense_id = c.lastrowid
        
        # Handle receipt upload
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename != '' and allowed_file(file.filename):
                receipt_file = save_receipt(file, user_id, expense_id)
                if receipt_file:
                    c.execute("UPDATE expenses SET receipt_file=? WHERE id=?", (receipt_file, expense_id))
                    conn.commit()
        
        # Update last_expense_date
        c.execute("UPDATE users SET last_expense_date=? WHERE id=?", (datetime.now().isoformat(), user_id))
        conn.commit()
        # Recalculate today's total after insert
        try:
            c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND date=? AND is_duplicate_flagged=0", (user_id, today))
            post = c.fetchone()
            today_total_after = post[0] or 0
        except Exception:
            today_total_after = today_total_before

        conn.close()
        
        warning_msg = ""
        if is_dup:
            warning_msg = f"⚠️ Duplicate Alert: {dup_msg}"
        elif is_fraud:
            warning_msg = f"⚠️ Fraud Alert: {fraud_msg}"
        else:
            # Check daily limit (if user has set one) and send notifications only when crossing threshold
            try:
                if daily_limit and daily_limit > 0:
                    # If before was below limit and after is >= limit, send notifications
                    if today_total_before < daily_limit and today_total_after >= daily_limit:
                        warning_msg = f"⚠️ Daily limit reached: You've spent ₹{today_total_after:.2f} today (limit: ₹{daily_limit:.2f})."
                        # send email if user opted for alerts
                        try:
                            send_daily_limit_alert(user_id, user_email, today_total_after, daily_limit)
                        except Exception as e:
                            print(f"Error sending daily email alert: {e}")
                        # send push notification if device token exists
                        try:
                            send_push_notification(user_id, f"Daily limit reached: ₹{today_total_after:.2f} spent today")
                        except Exception as e:
                            print(f"Error sending push notification: {e}")
            except Exception:
                pass
        
        return redirect(f'/dashboard?warning={warning_msg}' if warning_msg else '/dashboard')
    
    return render_template('add_expense.html')

@app.route('/savings', methods=['GET', 'POST'])
def savings_goals():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            goal_name = request.form['goal_name']
            target_amount = float(request.form['target_amount'])
            category = request.form.get('category', 'All')
            deadline = request.form['deadline']
            
            c.execute("""
                INSERT INTO savings_goals (user_id, goal_name, target_amount, current_amount, category, deadline, created_at, status)
                VALUES (?, ?, ?, 0, ?, ?, ?, 'active')
            """, (user_id, goal_name, target_amount, category, deadline, datetime.now().isoformat()))
            conn.commit()
        
        elif action == 'update':
            goal_id = int(request.form['goal_id'])
            amount_to_add = float(request.form['amount'])
            
            c.execute("SELECT current_amount, target_amount FROM savings_goals WHERE id=? AND user_id=?", (goal_id, user_id))
            goal = c.fetchone()
            
            if goal:
                new_amount = goal[0] + amount_to_add
                status = 'completed' if new_amount >= goal[1] else 'active'
                c.execute("UPDATE savings_goals SET current_amount=?, status=? WHERE id=?", (new_amount, status, goal_id))
                conn.commit()
        
        elif action == 'delete':
            goal_id = int(request.form['goal_id'])
            c.execute("DELETE FROM savings_goals WHERE id=? AND user_id=?", (goal_id, user_id))
            conn.commit()
    
    c.execute("""
        SELECT id, goal_name, target_amount, current_amount, deadline, status, category
        FROM savings_goals 
        WHERE user_id=? 
        ORDER BY deadline ASC
    """, (user_id,))
    goals = c.fetchall()
    conn.close()
    
    return render_template('savings_goals.html', goals=goals)

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get all expenses
    c.execute("""
        SELECT date, SUM(amount) as total, COUNT(*) as count
        FROM expenses 
        WHERE user_id=? AND is_duplicate_flagged=0
        GROUP BY date
        ORDER BY date DESC
    """, (user_id,))
    
    expenses_by_date = {}
    for row in c.fetchall():
        expenses_by_date[row[0]] = {'amount': row[1], 'count': row[2]}
    
    conn.close()
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    return render_template('calendar.html', 
        expenses_by_date=json.dumps(expenses_by_date),
        current_year=current_year,
        current_month=current_month
    )

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Check if user is admin
    c.execute("SELECT is_admin FROM users WHERE id=?", (user_id,))
    is_admin = c.fetchone()
    
    if not is_admin or is_admin[0] != 1:
        conn.close()
        return redirect('/dashboard')
    
    # Get total users
    c.execute("SELECT COUNT(*) FROM users WHERE is_admin=0")
    total_users = c.fetchone()[0]
    
    # Get total expenses
    c.execute("SELECT COUNT(*) FROM expenses")
    total_expenses = c.fetchone()[0]
    
    # Get total amount spent
    c.execute("SELECT SUM(amount) FROM expenses WHERE is_duplicate_flagged=0")
    total_amount = c.fetchone()[0] or 0
    
    # Top 5 highest spending users
    c.execute("""
        SELECT u.id, u.username, u.email, SUM(e.amount) as total_spent
        FROM users u
        LEFT JOIN expenses e ON u.id = e.user_id AND e.is_duplicate_flagged=0
        WHERE u.is_admin=0
        GROUP BY u.id
        ORDER BY total_spent DESC
        LIMIT 5
    """)
    top_users = c.fetchall()
    
    # Category breakdown
    c.execute("""
        SELECT category, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        WHERE is_duplicate_flagged=0
        GROUP BY category
        ORDER BY total DESC
    """)
    category_breakdown = c.fetchall()
    
    # Flagged expenses (duplicates/fraud)
    c.execute("""
        SELECT e.id, u.username, e.title, e.amount, e.duplicate_reason, e.date
        FROM expenses e
        JOIN users u ON e.user_id = u.id
        WHERE e.is_duplicate_flagged=1
        ORDER BY e.date DESC
        LIMIT 20
    """)
    flagged_expenses = c.fetchall()
    
    # User spending trends (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    c.execute("""
        SELECT u.username, SUM(e.amount) as total_30days
        FROM users u
        LEFT JOIN expenses e ON u.id = e.user_id AND e.date >= ? AND e.is_duplicate_flagged=0
        WHERE u.is_admin=0
        GROUP BY u.id
        ORDER BY total_30days DESC
        LIMIT 10
    """, (thirty_days_ago,))
    user_trends = c.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html',
        total_users=total_users,
        total_expenses=total_expenses,
        total_amount=total_amount,
        top_users=top_users,
        category_breakdown=category_breakdown,
        flagged_expenses=flagged_expenses,
        user_trends=user_trends
    )

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute("SELECT is_admin FROM users WHERE id=?", (user_id,))
    is_admin = c.fetchone()
    
    if not is_admin or is_admin[0] != 1:
        conn.close()
        return redirect('/dashboard')
    
    # Get all users with spending info
    c.execute("""
        SELECT u.id, u.username, u.email, u.monthly_budget, COUNT(e.id) as expense_count, SUM(e.amount) as total_spent
        FROM users u
        LEFT JOIN expenses e ON u.id = e.user_id AND e.is_duplicate_flagged=0
        WHERE u.is_admin=0
        GROUP BY u.id
        ORDER BY total_spent DESC
    """)
    users = c.fetchall()
    conn.close()
    
    return render_template('admin_users.html', users=users)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        send_daily = 1 if request.form.get('send_daily_summary') else 0
        send_weekly = 1 if request.form.get('send_weekly_summary') else 0
        send_alert = 1 if request.form.get('send_limit_alert') else 0
        send_reminder = 1 if request.form.get('send_reminder') else 0
        # accept daily limit (optional)
        daily_limit_val = request.form.get('daily_limit')
        try:
            daily_limit = float(daily_limit_val) if daily_limit_val else None
        except ValueError:
            daily_limit = None
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""
            UPDATE users 
            SET send_daily_summary=?, send_weekly_summary=?, send_limit_alert=?, send_reminder=?, daily_limit=?
            WHERE id=?
        """, (send_daily, send_weekly, send_alert, send_reminder, daily_limit, user_id))
        conn.commit()
        conn.close()
        
        return redirect('/dashboard')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""
        SELECT send_daily_summary, send_weekly_summary, send_limit_alert, send_reminder, email, daily_limit
        FROM users WHERE id=?
    """, (user_id,))
    
    user_prefs = c.fetchone()
    conn.close()
    
    return render_template('settings.html', 
        send_daily=user_prefs[0] if user_prefs else 0,
        send_weekly=user_prefs[1] if user_prefs else 1,
        send_alert=user_prefs[2] if user_prefs else 1,
        send_reminder=user_prefs[3] if user_prefs else 1,
        email=user_prefs[4] if user_prefs else '',
        daily_limit=user_prefs[5] if user_prefs and user_prefs[5] is not None else ''
    )

@app.route('/export-pdf')
def export_pdf():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("""
        SELECT title, amount, category, date FROM expenses 
        WHERE user_id=? AND date LIKE ? AND is_duplicate_flagged=0
        ORDER BY date DESC
    """, (user_id, f"{current_month}%"))
    
    expenses = c.fetchall()
    c.execute("SELECT SUM(amount), COUNT(*) FROM expenses WHERE user_id=? AND date LIKE ? AND is_duplicate_flagged=0", (user_id, f"{current_month}%"))
    total, count = c.fetchone()
    total = total or 0
    
    c.execute("SELECT monthly_budget FROM users WHERE id=?", (user_id,))
    budget = c.fetchone()[0] or 0
    
    conn.close()
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#7c3aed'),
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph("Monthly Expense Report", title_style))
    elements.append(Paragraph(f"<b>Month:</b> {current_month}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>Summary</b>", styles['Heading2']))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Expenses', f'₹{total:.2f}'],
        ['Number of Entries', str(count)],
        ['Monthly Budget', f'₹{budget:.2f}'],
        ['Remaining', f'₹{budget - total:.2f}']
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>Detailed Expenses</b>", styles['Heading2']))
    expense_data = [['Title', 'Category', 'Amount', 'Date']]
    for exp in expenses:
        expense_data.append([exp[0], exp[2], f'₹{exp[1]:.2f}', exp[3]])
    
    expense_table = Table(expense_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    expense_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(expense_table)
    
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='expense_report.pdf')

@app.route('/api/latest-expense')
def latest_expense():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT id, title, amount, created_at FROM expenses 
        WHERE user_id=? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user_id,))
    
    expense = c.fetchone()
    conn.close()
    
    if expense:
        return jsonify({
            "id": expense[0],
            "title": expense[1],
            "amount": expense[2],
            "created_at": expense[3]
        })
    
    return jsonify({"error": "No expenses found"}), 404


@app.route('/api/insights')
def api_insights():
    if 'user_id' not in session:
        return jsonify({}), 401

    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Current month totals
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND date LIKE ? AND is_duplicate_flagged=0", (user_id, f"{current_month}%"))
    total = c.fetchone()[0] or 0

    # Top category this month
    c.execute("SELECT category, SUM(amount) as total FROM expenses WHERE user_id=? AND date LIKE ? AND is_duplicate_flagged=0 GROUP BY category ORDER BY total DESC LIMIT 1", (user_id, f"{current_month}%"))
    top = c.fetchone()
    top_category = top[0] if top else None
    top_amount = top[1] if top else 0

    # Average daily (for days so far in month)
    day_of_month = datetime.now().day
    avg_daily = (total / day_of_month) if day_of_month > 0 else 0

    conn.close()

    insight = None
    if top_category:
        insight = f"This month you spent the most on {top_category} (₹{top_amount:.2f}). Total: ₹{total:.2f}. Avg/day: ₹{avg_daily:.2f}."

    return jsonify({
        'insight': insight,
        'top_category': top_category,
        'top_amount': round(top_amount, 2),
        'monthly_total': round(total, 2),
        'avg_daily': round(avg_daily, 2)
    })


@app.route('/api/chart-data')
def api_chart_data():
    if 'user_id' not in session:
        return jsonify({}), 401

    user_id = session['user_id']
    rng = request.args.get('range', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    q = request.args.get('q')
    category = request.args.get('category')

    # Determine date window
    today = datetime.now().date()
    if start_date and end_date:
        try:
            sd = datetime.fromisoformat(start_date).date()
            ed = datetime.fromisoformat(end_date).date()
        except Exception:
            sd = today - timedelta(days=7)
            ed = today
    else:
        if rng == 'today':
            sd = ed = today
        elif rng == 'week':
            sd = today - timedelta(days=6)
            ed = today
        elif rng == 'month':
            sd = today - timedelta(days=29)
            ed = today
        else:
            sd = today - timedelta(days=29)
            ed = today

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Categories breakdown
    params = [user_id, sd.isoformat(), ed.isoformat()]
    query = "SELECT category, SUM(amount) FROM expenses WHERE user_id=? AND date BETWEEN ? AND ? AND is_duplicate_flagged=0"
    if category:
        query += " AND category=?"
        params.append(category)
    query += " GROUP BY category ORDER BY SUM(amount) DESC"
    c.execute(query, tuple(params))
    cats = c.fetchall()
    categories = [r[0] for r in cats]
    category_amounts = [round(r[1] or 0, 2) for r in cats]

    # Daily amounts (grouped)
    c.execute("SELECT date, SUM(amount) FROM expenses WHERE user_id=? AND date BETWEEN ? AND ? AND is_duplicate_flagged=0 GROUP BY date ORDER BY date", (user_id, sd.isoformat(), ed.isoformat()))
    rows = c.fetchall()
    date_map = {r[0]: r[1] for r in rows}

    dates = []
    daily_amounts = []
    cur = sd
    while cur <= ed:
        key = cur.isoformat()
        dates.append(key)
        daily_amounts.append(round(date_map.get(key, 0) or 0, 2))
        cur = cur + timedelta(days=1)

    # Monthly summary for last 6 months
    months = []
    month_amounts = []
    for i in range(5, -1, -1):
        m = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        label = m.strftime('%Y-%m')
        c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND date LIKE ? AND is_duplicate_flagged=0", (user_id, f"{label}%"))
        ma = c.fetchone()[0] or 0
        months.append(label)
        month_amounts.append(round(ma, 2))

    conn.close()

    return jsonify({
        'categories': categories,
        'category_amounts': category_amounts,
        'dates': dates,
        'daily_amounts': daily_amounts,
        'months': months,
        'month_amounts': month_amounts
    })


@app.route('/set-budget', methods=['POST'])
def set_budget():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'not_logged_in'}), 401

    user_id = session['user_id']
    monthly_budget = request.form.get('monthly_budget') or request.json.get('monthly_budget') if request.is_json else request.form.get('monthly_budget')
    daily_limit = request.form.get('daily_limit') or (request.json.get('daily_limit') if request.is_json else None)

    try:
        mb = float(monthly_budget) if monthly_budget not in (None, '') else None
    except Exception:
        mb = None

    try:
        dl = float(daily_limit) if daily_limit not in (None, '') else None
    except Exception:
        dl = None

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET monthly_budget=?, daily_limit=? WHERE id=?", (mb, dl, user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'monthly_budget': mb, 'daily_limit': dl})

@app.route('/api/backup-now', methods=['POST'])
def backup_now():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    success = create_backup()
    return jsonify({"success": success, "message": "Backup created!" if success else "Backup failed!"})

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_info':
            username = request.form.get('username')
            email = request.form.get('email')
            
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE users SET username=?, email=? WHERE id=?", (username, email, user_id))
            conn.commit()
            conn.close()
            
            session['username'] = username
            return redirect('/profile')
        
        elif action == 'change_password':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                return render_template('profile.html', msg="Passwords don't match!")
            
            if len(new_password) < 6:
                return render_template('profile.html', msg="Password must be at least 6 characters!")
            
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE id=?", (user_id,))
            user = c.fetchone()
            
            if not user or not check_password_hash(user[0], old_password):
                conn.close()
                return render_template('profile.html', msg="Old password is incorrect!")
            
            hashed_password = generate_password_hash(new_password)
            c.execute("UPDATE users SET password=? WHERE id=?", (hashed_password, user_id))
            conn.commit()
            conn.close()
            
            return render_template('profile.html', msg="Password changed successfully!")
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT username, email FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    return render_template('profile.html', username=user[0] if user else '', email=user[1] if user else '')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        user = c.fetchone()
        
        if user:
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
            c.execute("INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)", 
                     (user[0], token, expires_at))
            conn.commit()
            conn.close()
            
            return render_template('forgot_password.html', msg=f"Reset link: /reset-password/{token}", token=token)
        
        conn.close()
        return render_template('forgot_password.html', msg="Email not found!")
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT user_id, expires_at FROM password_resets WHERE token=?", (token,))
    reset = c.fetchone()
    
    if not reset:
        conn.close()
        return render_template('reset_password.html', msg="Invalid or expired token!")
    
    user_id, expires_at = reset
    if datetime.fromisoformat(expires_at) < datetime.now():
        conn.close()
        return render_template('reset_password.html', msg="Token expired! Request a new one.")
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            return render_template('reset_password.html', msg="Passwords don't match!")
        
        if len(new_password) < 6:
            return render_template('reset_password.html', msg="Password must be at least 6 characters!")
        
        hashed_password = generate_password_hash(new_password)
        c.execute("UPDATE users SET password=? WHERE id=?", (hashed_password, user_id))
        c.execute("DELETE FROM password_resets WHERE token=?", (token,))
        conn.commit()
        conn.close()
        
        return render_template('reset_password.html', msg="Password reset successfully! <a href='/login'>Login here</a>")
    
    conn.close()
    return render_template('reset_password.html')

@app.route('/delete/<int:expense_id>')
def delete_expense(expense_id):
    """Delete an expense by ID"""
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        # Verify expense belongs to user
        c.execute("SELECT user_id FROM expenses WHERE id=?", (expense_id,))
        expense = c.fetchone()
        
        if not expense or expense[0] != user_id:
            conn.close()
            return redirect('/dashboard')
        
        # Delete the expense
        c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error deleting expense: {e}")
    
    return redirect('/dashboard')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    return "File too large! Maximum size is 5MB.", 413

if __name__ == '__main__':
    init_db()
    start_scheduler()
    app.run(debug=True)
