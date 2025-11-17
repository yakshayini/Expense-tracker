# ⚡ PHASE 3 QUICK SETUP GUIDE

## What's New? 🎉

Your expense tracker now has:
- 📧 **Automated email summaries** (daily & weekly)
- 💰 **Spend limit alerts** (automatic notifications)
- ⚡ **Instant dashboard updates** (real-time expense sync)
- 💬 **Smart reminders** (if no entry for 2+ days)
- ☁️ **Cloud database support** (multi-device login)
- 💾 **Automatic backups** (daily at 2 AM)

---

## 🚀 Getting Started (3 Steps)

### Step 1: Install New Packages
```bash
cd "c:\Users\wilma\EXPENSE TRACKER"
pip install -r requirements.txt
```

New packages installed:
- `flask-mail` - Email notifications
- `apscheduler` - Scheduled tasks
- `python-dotenv` - Environment variables
- `psycopg2-binary` - PostgreSQL support

### Step 2: Configure Email (Optional but Recommended)

Edit `.env` file in project root:

**For Gmail**:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@expensetracker.com
```

**Get Gmail App Password**:
1. Go to [Google Account](https://myaccount.google.com/)
2. Click "Security" in left menu
3. Enable 2-factor authentication
4. Generate "App passwords"
5. Select Mail + Other (custom app)
6. Copy the 16-character password
7. Paste in `.env` as `MAIL_PASSWORD`

### Step 3: Start the App

```bash
cd "c:\Users\wilma\EXPENSE TRACKER"
.\venv\Scripts\python.exe app.py
```

**Output should show**:
```
Scheduler started!
Running on http://127.0.0.1:5000
```

✅ You're ready to go!

---

## 📋 What Gets Sent Automatically?

### Daily Summaries (8 AM)
If enabled in Settings:
- Today's total spending
- Number of expenses
- Category breakdown

### Weekly Summaries (Sunday)
If enabled in Settings:
- 7-day total
- Top spending category
- All categories used

### Budget Alerts (Immediate)
When spending reaches:
- 80% of budget → **Orange alert**
- 100% of budget → **Red alert**

### Expense Reminders (Every 6 Hours)
If no entry for 2+ days:
- Reminder to add expense
- Link to add expense page

### Daily Backups (2 AM)
Automatic backup created:
- Stored in `backups/` folder
- Old backups deleted after 30 days

---

## ⚙️ Configure Notifications

### In Your App:

1. Click **"⚙️ Settings"** in navigation
2. Toggle each notification type:
   - ✅ Daily Summary
   - ✅ Weekly Summary
   - ✅ Budget Limit Alerts
   - ✅ Expense Reminders
3. Click **"💾 Save Settings"**

---

## ⚡ Real-Time Features

### Instant Expense Updates:
1. Add expense from any browser
2. See **toast notification** (top-right): "✅ New expense added"
3. Dashboard auto-refreshes
4. No manual refresh needed!

**How it works**:
- Checks for new expenses every 5 seconds
- Shows notification automatically
- Refreshes dashboard after 2 seconds

---

## 💾 Backups

### Automatic:
- Created daily at 2 AM
- Stored in `backups/` folder
- Old files auto-deleted after 30 days

### Manual Backup:
```bash
curl -X POST http://127.0.0.1:5000/api/backup-now
```

### Restore:
1. Stop app
2. Copy backup file to `database.db`
3. Restart app

---

## 🌐 Cloud Setup (Optional)

### Use PostgreSQL for Multi-Device Sync:

1. **Create database** (Heroku, Railway, AWS RDS)
2. **Edit `.env`**:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/db
   DB_TYPE=postgres
   ```
3. **Update app.py** to use PostgreSQL (optional, contact developer)
4. **Deploy to cloud**
5. **Same login = multi-device access**

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Emails not sending | Check `.env` credentials, ensure app is running |
| Real-time updates not working | Refresh browser, check console (F12) for errors |
| Backups not created | Check `backups/` folder permissions, disk space |
| Scheduler not running | Look for "Scheduler started!" in app output |
| Can't find Settings | Click ⚙️ icon in navigation bar at top |

---

## 📧 Email Setup Tips

### Test Email Connection:
1. Add email address in registration or profile
2. Enable "Daily Summary" in Settings
3. Wait until 8 AM (or manually test endpoint)
4. Check email inbox

### Gmail Troubleshooting:
- "Less secure app access" error? Use **App Password** (not regular password)
- "Connection refused"? Check MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS
- "Authentication failed"? Verify username and password in `.env`

### No Local SMTP?
- Comment out email settings in `.env`
- App works fine without email (just no notifications)
- Features like budget limits, reminders still work locally

---

## 📊 Scheduler Details

Runs in background automatically:

| Time | Task | Purpose |
|------|------|---------|
| 8 AM | Send Daily Summaries | Email today's spending |
| Every 6 hours | Send Reminders | Alert if 2+ days no entry |
| Every hour | Check Budget | Alert if limit reached |
| 2 AM | Create Backup | Daily database backup |
| 3 AM (Weekly) | Clean Backups | Delete 30+ day old backups |

All tasks run automatically in background. No manual action needed!

---

## 🎯 Feature Comparison

| Feature | Phase 1 | Phase 2 | Phase 3 |
|---------|---------|---------|---------|
| Add/View Expenses | ✅ | ✅ | ✅ |
| Charts & Analytics | ✅ | ✅ | ✅ |
| Auto-Category | | ✅ | ✅ |
| Profile Management | | ✅ | ✅ |
| Session Timeout | | ✅ | ✅ |
| **Daily Summaries** | | | ✅ NEW |
| **Weekly Summaries** | | | ✅ NEW |
| **Budget Alerts** | | | ✅ NEW |
| **Entry Reminders** | | | ✅ NEW |
| **Real-Time Updates** | | | ✅ NEW |
| **Auto Backups** | | | ✅ NEW |
| **Cloud Database** | | | ✅ NEW |
| **Email System** | | | ✅ NEW |
| **Settings Page** | | | ✅ NEW |

---

## 💡 Pro Tips

1. **Gmail App Password**: Must use app password, not account password
2. **Real-time Updates**: Works on same app instance; use cloud DB for multi-device
3. **Backups**: Automatically created and cleaned up - no manual management needed
4. **Email Timing**: Summaries sent at scheduled times (8 AM, Sunday)
5. **Budget Alerts**: Trigger immediately when expense added that crosses threshold
6. **Settings**: Per-user preference - each user controls their own notifications
7. **Reminders**: Only sent if user has email configured

---

## 🚀 You're All Set!

**Your app now has**:
- ✅ Automated email notifications
- ✅ Instant dashboard updates
- ✅ Smart reminders
- ✅ Daily backups
- ✅ Cloud-ready architecture
- ✅ Professional notification system

**Start using it**:
1. Restart app with new packages installed
2. Configure email (optional)
3. Go to Settings and enable notifications
4. Add expenses and watch real-time magic happen!
5. Check email for summaries and alerts

---

**Status**: ✅ READY TO USE
**Version**: 3.0 with Advanced Notifications
**Questions?**: See PHASE_3_FEATURES.md for detailed documentation

Happy tracking! 🎉
