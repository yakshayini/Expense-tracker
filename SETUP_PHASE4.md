# Phase 4 Quick Setup Guide 🚀

## Installation (3 Steps)

### Step 1: Install Dependencies
```powershell
cd "c:\Users\wilma\EXPENSE TRACKER"
pip install -r requirements.txt
```

Required packages for Phase 4:
- ✅ `pillow==12.0.0` - Image compression
- ✅ `flask-mail==0.9.1` - Email system
- ✅ `apscheduler==3.10.4` - Background tasks

### Step 2: Start the App
```powershell
python app.py
```

Open browser: **http://127.0.0.1:5000**

### Step 3: Configure Admin User (Optional)
```sql
-- To make a user admin:
UPDATE users SET is_admin = 1 WHERE username = 'your_username';
```

Admin gets access to:
- `/admin/dashboard` - Analytics & insights
- `/admin/users` - User management
- Flagged expense review

---

## New Features Quick Access

### 📅 Calendar View
**Route:** `/calendar`
- Click on any date to see expenses
- Navigate months with arrows
- Green badges show totals
- No setup needed

### 🎯 Savings Goals
**Route:** `/savings`
- Create goals with deadline
- Track progress with visual bars
- Add funds incrementally
- Auto-complete on target reach

### 📸 Receipt Upload
**Location:** Add Expense form
- Upload JPG/PNG/GIF/PDF
- Max 5MB per file
- Auto-compressed
- Stored securely per user

### 👨‍💼 Admin Dashboard
**Route:** `/admin/dashboard` (Admin only)
- View all system analytics
- Identify top spending users
- Review flagged expenses
- Category breakdown charts
- User spending trends

### 👥 User Management
**Route:** `/admin/users` (Admin only)
- See all users with budgets
- Track total spent per user
- Budget usage percentage
- Health status (Healthy/Caution/Alert)

---

## Fraud Detection Features

### Automatic Duplicate Detection
```
When you add an expense:
1. System checks if identical expense exists (1 hour window)
2. If found: ⚠️ "Duplicate detected"
3. Expense flagged but still tracked
4. Admin can review in dashboard
```

**How it works:**
- Same title + amount + category + date = duplicate
- Alert shown immediately
- Flagged expenses excluded from main calculations
- Still visible in reports

### Anomaly Detection
```
When spending is unusual:
1. System compares to your average for category
2. If amount > 3x average: 🚨 "Fraud Alert"
3. Example: If average food = ₹500, ₹1500+ = alert
4. Admin notified automatically
```

---

## File Organization

### Receipt Storage
```
static/receipts/
  ├── 1/
  │   ├── expense_123_1234567890.jpg
  │   └── expense_124_1234567891.jpg
  └── 2/
      └── expense_456_1234567892.jpg
```

Each user has their own folder for security.

### Database
```sql
-- New columns in expenses table:
receipt_file           -- Path to uploaded file
is_duplicate_flagged   -- 1 if duplicate/fraud detected
duplicate_reason       -- Reason for flagging

-- New table:
savings_goals          -- All user savings goals
```

---

## Admin Dashboard Walkthrough

### 1. View Metrics
```
┌─────────────────────┐
│ Total Users: 15     │
│ Total Expenses: 342 │
│ Amount Spent: ₹50K  │
│ Flagged: 5          │
└─────────────────────┘
```

### 2. View Charts
- **Spending by Category** - Pie chart
- **User Trends** - Bar chart (last 30 days)

### 3. Top 5 Users
```
#1 Rahul     ₹15,000
#2 Priya     ₹12,500
#3 Arjun     ₹11,000
#4 Anjali    ₹9,500
#5 Vikram    ₹8,000
```

### 4. Flagged Expenses
```
| User    | Expense | Amount  | Reason           |
|---------|---------|---------|------------------|
| Rahul   | Lunch   | ₹500    | ⚠️ Duplicate     |
| Priya   | Phone   | ₹25,000 | 🚨 Fraud (3x avg)|
```

### 5. Category Breakdown
```
| Category      | Total   | Count | Average |
|---------------|---------|-------|---------|
| Food          | ₹15,000 | 120   | ₹125    |
| Transport     | ₹8,000  | 80    | ₹100    |
| Entertainment | ₹5,000  | 20    | ₹250    |
```

---

## Common Tasks

### Create a Savings Goal
```
1. Login
2. Click 🎯 Savings (in nav)
3. Fill form:
   ☐ Goal Name: "Vacation"
   ☐ Amount: 50000
   ☐ Category: All
   ☐ Deadline: 2025-12-31
4. Click "Create Goal"
5. Goal appears in list
```

### Add Receipt to Expense
```
1. Go to Add Expense
2. Fill expense details
3. Scroll to "Receipt (Optional)"
4. Click "Choose File"
5. Select JPG/PNG/GIF/PDF
6. Click "Add Expense"
7. Receipt saved automatically
```

### Review Flagged Expenses
```
Admin only:
1. Go to /admin/dashboard
2. Scroll to "Flagged Expenses"
3. View duplicate/fraud alerts
4. Click user to see details
```

### Check User Budgets
```
Admin only:
1. Go to /admin/users
2. View budget usage %
3. Red status = over budget
4. Yellow = 50-80%
5. Green = under 50%
```

---

## Troubleshooting

### Q: Receipt not uploading
**A:** 
- File must be JPG/PNG/GIF/PDF
- Size must be < 5MB
- Check `static/receipts/` folder exists
- Ensure write permissions

### Q: Admin dashboard blank
**A:**
- Verify user has `is_admin = 1`
- Try logout/login again
- Check browser console for errors

### Q: Fraud detection not working
**A:**
- Ensure new expense columns exist
- Try adding duplicate expense within 1 hour
- Check database for is_duplicate_flagged=1

### Q: Calendar shows no dates
**A:**
- Verify expenses in database
- Check is_duplicate_flagged = 0 (only shows non-flagged)
- Refresh page
- Check browser console

---

## Demo Workflow

### Step 1: Add Multiple Expenses
```
1. Add Expense: "Lunch" ₹500 today
2. Add Expense: "Lunch" ₹500 today → ⚠️ Duplicate alert!
3. Add Expense: "Expensive laptop" ₹100,000 → 🚨 Fraud alert!
```

### Step 2: View Calendar
```
1. Click Calendar (📅)
2. See all expenses by date
3. Click date to view summary
4. Navigate months
```

### Step 3: Create Savings Goal
```
1. Click Savings (🎯)
2. Create goal: "Vacation" ₹50,000 by 2025-12-31
3. Add progress: ₹10,000
4. Watch progress bar fill
```

### Step 4: Admin Review (If Admin)
```
1. Go to /admin/dashboard
2. View analytics
3. See top users
4. Review flagged expenses
5. Check trends chart
```

---

## What's New in Phase 4

| Feature | Route | Access | Description |
|---------|-------|--------|-------------|
| Calendar | `/calendar` | User | View expenses by date |
| Savings Goals | `/savings` | User | Create & track goals |
| Receipt Upload | Add Expense | User | Upload proof images |
| Admin Dashboard | `/admin/dashboard` | Admin | System analytics |
| User Manager | `/admin/users` | Admin | User spending analysis |
| Fraud Detection | Auto | User/Admin | Duplicate & anomaly alerts |

---

## Performance & Storage

### Receipt Storage
- Images auto-compressed to 1024x1024
- Quality reduced to 85% (saves space)
- Each user folder separate
- Max 5MB per file

### Calendar Performance
- Loads entire month in JSON
- Client-side rendering
- No pagination needed
- Smooth navigation

### Admin Queries
- Optimized with GROUP BY
- Aggregates calculated efficiently
- Excludes flagged expenses automatically
- Runs in <1 second

---

## Next Steps

✅ Phase 4 complete with:
- Admin dashboard
- Fraud detection
- Calendar view
- Savings goals
- Receipt uploads
- User management
- Advanced analytics

Ready for Phase 5? (Optional enhancements)
- Mobile app
- SMS alerts
- Budget forecasting
- AI category learning
- Social sharing

---

## Support & Issues

Found a bug? Check:
1. All packages installed: `pip install -r requirements.txt`
2. Database initialized: Database auto-creates on first run
3. Folders exist: `static/receipts/` created automatically
4. Admin set: `UPDATE users SET is_admin=1 WHERE id=1;`

For detailed documentation, see: **PHASE_4_FEATURES.md**
