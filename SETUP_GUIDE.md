# PaisaCoach Setup & Troubleshooting Guide

This guide helps you set up PaisaCoach and avoid common issues.

---

## ✅ Prerequisites

Before starting, ensure you have:
- **Python 3.8+** installed
- **pip** (Python package manager)
- **Git** (optional, for cloning)

---

## 🚀 Step-by-Step Setup

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd paisacoach
```

### 2. Create a Virtual Environment (Recommended)

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**What each package does:**
- `Django>=4.2` — Web framework
- `python-dotenv>=1.0.0` — Loads environment variables from `.env`
- `pdfplumber>=0.10.0` — Extracts transactions from bank statement PDFs
- `Pillow>=10.0.0` — Image processing
- `whitenoise>=6.6.0` — Serves static files in production
- `gunicorn>=21.0.0` — Production WSGI server
- `anthropic>=0.7.0` — Claude AI API (optional, app works without it)

### 4. Configure Environment Variables

**Copy the example file:**
```bash
cp .env.example .env
```

**Edit `.env` with your values:**
```env
# Required for security (Django will complain if missing)
SECRET_KEY=your-secret-key-here-change-this

# Set to False in production
DEBUG=True

# Comma-separated hosts (add your domain if deploying)
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: Get from console.anthropic.com
# If empty, app uses rule-based insights (still works great!)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

This creates the SQLite database and tables.

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, core, accounts, analytics
Running migrations:
  Applying core.0001_initial... OK
  Applying accounts.0001_initial... OK
  ...
```

### 6. Create a Superuser (Optional)

To access the admin panel at `/admin/`:
```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 7. Run the Development Server

```bash
python manage.py runserver
```

**Expected output:**
```
Watching for file changes with StatReloader
Quit the server with CONTROL-C.
October 20, 2024 - 10:30:45
Django version 4.2.7, using settings 'paisacoach.settings'
Starting development server at http://127.0.0.1:8000/
```

Visit: **http://127.0.0.1:8000**

---

## 📝 Quick Start: Demo Data

On the login page, you'll see a **"Try with Demo Data"** button.

**How to use it:**
1. Click the button without logging in
2. It auto-creates a demo user with sample transactions
3. Explore the dashboard with realistic data
4. Your Financial Age Score, Idle Money, EMI Analysis, and AI Insights are auto-calculated

**Demo user credentials:**
- Username: `demo`
- Password: `demo123` (or check console output)

---

## ❌ Common Errors & Fixes

### 1. **"ModuleNotFoundError: No module named 'django'"**

**Cause:** Django not installed  
**Fix:**
```bash
pip install -r requirements.txt
```

---

### 2. **"django.core.exceptions.ImproperlyConfigured: Allowed host mismatch"**

**Cause:** Your app URL is not in `ALLOWED_HOSTS`  
**Fix:** Edit `.env` and add your host:
```env
ALLOWED_HOSTS=localhost,127.0.0.1,yourapp.railway.app
```

---

### 3. **"FileNotFoundError: [Errno 2] No such file or directory: '.env'"**

**Cause:** `.env` file doesn't exist  
**Fix:**
```bash
cp .env.example .env
# Edit .env with your values
```

---

### 4. **"relation 'core_transaction' does not exist"**

**Cause:** Migrations not applied  
**Fix:**
```bash
python manage.py migrate
```

---

### 5. **PDF Upload Returns Empty (No Transactions Imported)**

**Cause:** Bank statement PDF format not recognized  
**Fix:**
1. Ensure PDF contains bank transactions
2. Try exporting from your bank as a fresh PDF
3. Common bank formats (HDFC, ICICI, Axis, SBI) are supported
4. If it still fails, add transactions manually

---

### 6. **"TemplateDoesNotExist: 'core/dashboard.html'"**

**Cause:** Template files missing  
**Fix:**
Ensure project structure matches:
```
paisacoach/
├── core/
│   ├── templates/
│   │   └── core/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── transactions.html
│   │       ├── emis.html
│   │       ├── goals.html
│   │       ├── profile.html
│   │       ├── home.html
│   │       ├── upload_statement.html
│   └── ...
├── accounts/
│   └── templates/
│       └── accounts/
│           ├── login.html
│           └── register.html
└── ...
```

---

### 7. **Claude AI Insights Not Working**

**Cause:** Missing or invalid Anthropic API key  
**Fix:**
1. Get API key: https://console.anthropic.com
2. Add to `.env`:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-actual-key
   ```
3. Restart the server
4. If API key is invalid, app falls back to rule-based insights (no error)

---

### 8. **"SECRET_KEY is a required setting"**

**Cause:** `SECRET_KEY` not in `.env`  
**Fix:** Add to `.env`:
```env
SECRET_KEY=your-unique-secret-key-here
```

For production, use Django's secret key generator:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🔒 Security Checklist (Before Deployment)

- [ ] Change `DEBUG=False` in `.env`
- [ ] Generate a new `SECRET_KEY` (don't use the example)
- [ ] Set `ALLOWED_HOSTS` to your actual domain
- [ ] Use a production database (PostgreSQL, MySQL) instead of SQLite
- [ ] Set secure cookies: `SESSION_COOKIE_SECURE=True`
- [ ] Enable HTTPS only: `SECURE_SSL_REDIRECT=True`

---

## 📦 Database Backup

To backup your SQLite database:
```bash
cp db.sqlite3 db.sqlite3.backup
```

To use the backup:
```bash
cp db.sqlite3.backup db.sqlite3
```

---

## 🚢 Deploying to Railway/Render

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Railway/Render:**
   - Link your GitHub repo
   - Set environment variables in platform settings
   - Railway/Render will auto-detect `requirements.txt` and deploy

3. **Procfile is already configured:**
   ```
   web: gunicorn paisacoach.wsgi
   ```

---

## 📊 Project Architecture Overview

```
paisacoach/                    # Django project folder
├── core/                      # Main app
│   ├── models.py             # UserProfile, Transaction, EMI, SavingsGoal, AIInsight
│   ├── views.py              # Dashboard, transactions, EMI, goals, profile
│   ├── ai_engine.py          # 🧠 Financial Age Score, Idle Money, EMI Trap, AI Insights
│   ├── forms.py              # Forms for data entry
│   ├── urls.py               # URL routing
│   ├── admin.py              # Django admin configuration
│   └── templates/core/       # HTML templates
│
├── accounts/                 # Authentication
│   ├── views.py             # Login, register, demo data loader
│   ├── urls.py              # Auth URLs
│   └── templates/accounts/  # Login/register forms
│
├── analytics/               # Charts & analytics
│   ├── views.py            # Analytics dashboard
│   ├── urls.py             # Analytics URLs
│   └── templates/analytics/
│
├── paisacoach/             # Django settings
│   ├── settings.py         # Configuration (database, installed apps, etc.)
│   ├── urls.py            # Main URL router
│   └── wsgi.py            # Production server config
│
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── db.sqlite3             # SQLite database (created after migrate)
└── .env                   # Environment variables (SECRET_KEY, API keys, etc.)
```

---

## 🧪 Testing the App

### Test 1: Demo Data
1. Go to http://localhost:8000
2. Click "Try with Demo Data"
3. Verify dashboard shows sample transactions

### Test 2: Manual Transaction Entry
1. Log in
2. Go to Transactions → Add Transaction
3. Add a test transaction
4. Verify it appears in the list

### Test 3: Financial Score
1. Go to Dashboard
2. Scroll to "Financial Age Score"
3. Should show a score (18–70) and recommendation

### Test 4: PDF Upload
1. Go to Upload Statement
2. Select a bank statement PDF
3. Verify transactions are imported

---

## 🆘 Still Having Issues?

### Check Django Logs

```bash
# Run with verbose output
python manage.py runserver --verbosity=2
```

### Database Issues

```bash
# Reset database (WARNING: deletes all data!)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Static Files Issues

```bash
python manage.py collectstatic --noinput
```

---

## 📚 Project Features Quick Reference

| Feature | File | How to Test |
|---------|------|-----------|
| Financial Age Score | `core/ai_engine.py::compute_financial_age_score()` | Dashboard → Score card |
| Idle Money Detection | `core/ai_engine.py::detect_idle_money()` | Dashboard → Idle Money widget |
| EMI Trap Analyzer | `core/ai_engine.py::analyze_emi_trap()` | Add EMI → Dashboard/EMI page |
| Salary Autopilot | `core/ai_engine.py::salary_autopilot()` | Dashboard → Salary Day Plan |
| AI Insights | `core/ai_engine.py::generate_ai_insight()` | Dashboard → AI Insight button (needs API key) |
| Bank Statement Parser | `core/ai_engine.py::parse_bank_statement()` | Upload Statement page |

---

## 🎯 Next Steps

1. ✅ Complete setup above
2. 🔍 Explore the dashboard with demo data
3. 📝 Add your own transactions
4. 🎓 Read the README.md for feature details
5. 🚀 Deploy to production when ready

---

**Questions?** Check the README.md or review the inline code comments in `core/ai_engine.py`.
