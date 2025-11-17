# Phase 4 - Enterprise Features & Admin Dashboard 🚀

## Overview
Phase 4 adds powerful enterprise-grade features including:
- **Admin Dashboard** with full system analytics and user management
- **Fraud Detection System** - Automatically detects duplicate and anomalous expenses
- **Calendar View** - Visual expense tracking by date
- **Savings Goals Tracker** - Create and track savings objectives
- **Receipt Upload** - Attach proof images to expenses
- **Advanced Insights** - Top spending users, category breakdown, spending trends

---

## Features Implemented

### 1. 👨‍💼 Admin Dashboard
**Location:** `/admin/dashboard`

The admin dashboard provides complete visibility into the system:

#### Key Metrics
- **Total Users**: Count of all regular users
- **Total Expenses**: Overall number of expenses tracked
- **Total Amount Spent**: Sum of all expenses (excluding flagged)
- **Flagged Expenses**: Count of duplicate/fraud detections

#### Analytics & Insights
- **Spending by Category Chart**: Pie chart showing expense distribution
- **User Spending Trends**: Bar chart of top 10 users (last 30 days)
- **Top 5 Highest Spending Users**: Ranked list with contact info and totals
- **Category Breakdown**: Detailed table with averages per expense
- **Flagged Expenses List**: All suspicious expenses with reasons

**How to Access:**
```
1. Login with admin account (is_admin = 1)
2. Automatically redirected to /admin/dashboard
3. Navigate using admin menu
```

---

### 2. 🚨 Fraud & Duplicate Detection Engine

**Automatic Detection:**
- **Duplicate Detection**: Checks if identical expense exists within 1 hour
  - Same title, amount, category, and date
  - Flags with message: "Duplicate detected: [details]"
  
- **Fraud/Anomaly Detection**: Identifies unusual spending patterns
  - Flags if amount > 3x average for that category
  - Message: "Unusual spending: ₹X is 3x higher than average (₹Y)"

**How it Works:**
```python
# When adding expense:
1. Check for exact duplicates (1-hour window)
2. Check for spending anomalies (3x average)
3. If flagged, mark with is_duplicate_flagged=1
4. Store reason in duplicate_reason column
5. Exclude from dashboard calculations (but still visible)
```

**User Warning:**
- ⚠️ Alert appears when expense is flagged
- Admin can review in Admin Dashboard > Flagged Expenses
- Users can still proceed but are warned

---

### 3. 📅 Calendar View
**Location:** `/calendar`

Interactive calendar displaying expenses by date:

**Features:**
- Monthly navigation (← Previous / Next →)
- Color-coded expense entries
- Click on date to see details
- Summary shows:
  - Total amount spent on date
  - Number of expenses
  - Average per expense
  
**Visual Indicators:**
- Today's date highlighted in blue
- Other months grayed out
- Green expense badges show total and count
- Hover effects for interactivity

**Data Calculation:**
```
- Only counts non-flagged expenses
- Groups by date for efficiency
- Calculates running totals
```

---

### 4. 🎯 Savings Goals Tracker
**Location:** `/savings`

Comprehensive goal management system:

**Create Goals:**
- Goal name (e.g., "Vacation", "Emergency Fund")
- Target amount in rupees
- Category filter (All or specific category)
- Deadline date

**Track Progress:**
- Visual progress bar (0-100%)
- Current amount vs target
- Remaining amount calculation
- Status badge (Active/Completed)

**Manage Goals:**
- Add funds incrementally
- Auto-complete when target reached
- Delete goals
- View deadline countdown

**Database Structure:**
```sql
savings_goals(
    id, user_id, goal_name, target_amount,
    current_amount, category, deadline,
    created_at, status
)
```

---

### 5. 📸 Receipt Upload & Photo Proof
**Location:** Add Expense form

**Features:**
- Upload receipt images or PDFs
- Supported formats: JPG, PNG, GIF, PDF
- Maximum file size: 5MB
- Automatic image compression (1024x1024 max)
- File preview in form

**How It Works:**
```
1. Select receipt file in add expense form
2. File validated (extension & size)
3. Image compressed if needed (85% quality)
4. Saved to static/receipts/{user_id}/{filename}
5. File path stored in expenses.receipt_file
6. Display receipt link in expense details
```

**File Organization:**
```
static/receipts/
  ├── 1/           (user_id 1)
  │   ├── expense_123_1234567890.jpg
  │   ├── expense_124_1234567891.jpg
  └── 2/           (user_id 2)
      └── expense_456_1234567892.jpg
```

---

### 6. 👥 User Management Dashboard
**Location:** `/admin/users`

View all users with spending analytics:

**User Table Columns:**
- **Username**: User login name
- **Email**: Contact email
- **Monthly Budget**: User's budget limit
- **Expenses**: Count of tracked expenses
- **Total Spent**: Sum of all expenses
- **Budget Usage**: Percentage of budget used
- **Status**: Health indicator
  - ✅ Healthy: < 50%
  - ⚠️ Caution: 50-80%
  - 🚨 Alert: > 80%

**Sorting & Analytics:**
- Users sorted by total spending
- Budget usage percentage calculated
- Status automatically assigned
- Visual spending bar

---

### 7. 📊 Advanced Reporting & Insights

**System-Wide Metrics:**
- Total users and active expenses
- Total amount tracked across platform
- Average spending per user
- Category distribution analysis
- Top spending users identification

**User Trends (Last 30 Days):**
- Individual user spending patterns
- Trend comparison
- Risk identification
- Budget alert generation

---

## Database Schema Changes

### New Tables

#### `savings_goals`
```sql
CREATE TABLE savings_goals(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    goal_name TEXT,
    target_amount REAL,
    current_amount REAL,
    category TEXT,
    deadline TEXT,
    created_at TEXT,
    status TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### Enhanced Tables

#### `users` (New Columns)
```sql
ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN total_savings_goal REAL DEFAULT 0;
ALTER TABLE users ADD COLUMN current_savings REAL DEFAULT 0;
```

#### `expenses` (New Columns)
```sql
ALTER TABLE expenses ADD COLUMN receipt_file TEXT;
ALTER TABLE expenses ADD COLUMN is_duplicate_flagged INTEGER DEFAULT 0;
ALTER TABLE expenses ADD COLUMN duplicate_reason TEXT;
```

---

## API Endpoints

### Admin Routes

#### GET `/admin/dashboard`
- **Auth:** Admin only
- **Returns:** Dashboard with analytics
- **Data:** Users, expenses, top spenders, flagged list

#### GET `/admin/users`
- **Auth:** Admin only
- **Returns:** All users with spending info
- **Columns:** Username, email, budget, expenses, total

### User Routes

#### POST `/add` (Enhanced)
```
New Parameters:
- receipt: [file] - Receipt image/PDF
- Automatic fraud detection
- Auto-flag suspicious expenses
```

#### GET `/calendar`
- **Auth:** Required
- **Returns:** Calendar view with expenses
- **Data:** Expense totals by date

#### POST/GET `/savings`
- **Auth:** Required
- **Actions:** create, update, delete goals
- **Returns:** Goals list with progress

#### GET `/savings`
- **Auth:** Required
- **Returns:** All user's savings goals with progress

---

## File Structure

### New Templates
- `templates/admin_dashboard.html` - Admin dashboard (300+ lines)
- `templates/admin_users.html` - User management (170+ lines)
- `templates/calendar.html` - Calendar view (220+ lines)
- `templates/savings_goals.html` - Savings goals (380+ lines)

### Modified Templates
- `templates/add_expense.html` - Added receipt upload section
- `templates/dashboard.html` - Updated navigation with new links

### Directories
- `static/receipts/` - Receipt file storage (auto-created)
- `static/receipts/{user_id}/` - Per-user subdirectories

---

## Configuration & Setup

### Environment Variables (In .env)
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@expensetracker.com
```

### Receipt Upload Config
```python
# In app.py
UPLOAD_FOLDER = 'static/receipts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
```

---

## Security Features

### Admin Access Control
```python
@app.route('/admin/dashboard')
def admin_dashboard():
    # Check is_admin = 1
    # Redirect to /dashboard if not admin
```

### File Upload Security
- File extension whitelist validation
- File size limit (5MB max)
- MIME type checking
- Filename sanitization using secure_filename()
- User-specific folder isolation

### Fraud Detection
- Automatic duplicate prevention
- Anomaly detection based on averages
- Flagged expenses visible to admins
- Audit trail in database

---

## Usage Examples

### Creating Savings Goal
```
1. Navigate to /savings
2. Fill form:
   - Goal Name: "Vacation Fund"
   - Target: 50000
   - Category: All
   - Deadline: 2025-12-31
3. Click "Create Goal"
```

### Adding Expense with Receipt
```
1. Go to Add Expense
2. Fill details:
   - Title: "Grocery"
   - Amount: 2500
   - Category: Food
   - Date: Today
3. Select receipt image (JPG/PNG)
4. Click "Add Expense"
5. System auto-compresses image
6. Receipt accessible from admin
```

### Reviewing Flagged Expense
```
Admin Dashboard → Flagged Expenses
├── Duplicate: "Lunch" 500 (detected within 1 hour)
└── Fraud Alert: "Electronics" 25000 (3x average)
```

### Viewing Calendar
```
1. Click Calendar (📅) in dashboard
2. Browse months with ← / →
3. Click date to see summary
4. Green badges show total spent
```

---

## Performance Considerations

### Database Queries
- Indexed searches on user_id and date
- Aggregation queries use GROUP BY
- Exclude flagged expenses from main calculations
- Efficient left joins for analytics

### Image Compression
- Auto-resize to 1024x1024 max
- Quality reduced to 85% for storage
- Reduces file size by ~70%

### Calendar Performance
- Loads all dates in JSON format
- Client-side rendering
- No pagination needed

---

## Troubleshooting

### Issue: Receipt file not saving
**Solution:**
- Check `static/receipts/` folder exists
- Verify file size < 5MB
- Check file format is JPG/PNG/GIF/PDF
- Ensure write permissions on folder

### Issue: Admin dashboard not accessible
**Solution:**
- Verify user has `is_admin = 1`
- Check database: `SELECT is_admin FROM users WHERE id=X`
- Login again to refresh session

### Issue: Fraud detection not working
**Solution:**
- Ensure expenses table has new columns
- Check duplicate_reason column populated
- Verify is_duplicate_flagged=1 set

### Issue: Calendar shows no expenses
**Solution:**
- Verify expenses exist in database
- Check created_at column populated
- Use non-flagged expenses only
- Browser console for errors

---

## Future Enhancements

1. **Mobile Receipt OCR** - Automatic receipt scanning
2. **AI Category Mapping** - ML-based category detection
3. **Recurring Goals** - Auto-create monthly/yearly goals
4. **Goal Alerts** - Notifications for deadlines
5. **Receipt Gallery** - View all receipts by expense
6. **Export Receipt Folders** - Batch download receipts
7. **Receipt Search** - OCR text search in receipts
8. **Sharing Goals** - Collaborative goal tracking

---

## Phase 4 Summary

✅ **Admin Dashboard** - Complete system visibility
✅ **Fraud Detection** - Smart duplicate/anomaly detection
✅ **Calendar View** - Visual expense tracking
✅ **Savings Goals** - Goal creation and progress tracking
✅ **Receipt Upload** - Photo proof for expenses
✅ **User Management** - Admin user analytics
✅ **Advanced Insights** - Top users, trends, category breakdown

**Total Lines Added:** 2000+ (app.py + templates)
**New Database Columns:** 6
**New Templates:** 4
**New Routes:** 7 (admin + user routes)
**Security Features:** File validation, access control, fraud detection
