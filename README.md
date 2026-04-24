# PaisaCoach — AI Wealth Copilot

AI-powered wealth and personal finance copilot for Indian users.

PaisaCoach helps users understand spending behavior, identify idle money, optimize EMI decisions, and learn financial fundamentals with conversational guidance.

## Recent Updates (April 2026)

- Profile now supports user age and saves it from the profile screen.
- Dashboard shows a dedicated Profile Age stat card.
- Analytics 6-month income vs expense trend chart render timing fixed.
- Transactions page visual polish aligned with the rest of the app UI.

## Highlights

- Financial age scoring and action plan generation
- Idle money detection with opportunity-cost alerts
- Expense optimization tips from transaction history
- AI financial assistant chat (with optional Anthropic integration)
- Financial literacy hub with structured modules
- PDF bank-statement import for quick transaction ingestion

## Tech Stack

- Backend: Django 4.2
- Database: SQLite (default), PostgreSQL-ready
- Frontend: Django templates, CSS, vanilla JavaScript, Chart.js
- AI: Rule-based fallback + optional Anthropic API
- Parsing: pdfplumber for PDF bank statements

## Quick Start

### 1) Clone and install

```bash
git clone <your-repo-url>
cd paisacoach
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Configure environment

```bash
cp .env.example .env
```

Edit `.env` as needed.

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes (prod) | Django secret key |
| `DEBUG` | Yes | `True` for local dev, `False` for prod |
| `ALLOWED_HOSTS` | Yes (prod) | Comma-separated hostnames |
| `ANTHROPIC_API_KEY` | Optional | Enables Anthropic-backed chat/insights |

### 3) Migrate and run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000

## Project Structure

```text
paisacoach/
├── accounts/                 # authentication and user flows
├── analytics/                # analytics page/views
├── core/                     # models, AI engine, main templates and logic
├── paisacoach/               # Django settings and root urls
├── manage.py
├── requirements.txt
└── .env.example
```

## Core User Flows

1. Register/login
2. Add transactions manually or import statement PDF
3. View dashboard insights and financial score
4. Chat with AI advisor for personalized suggestions
5. Track goals and monitor analytics trends

## Current Implementation Snapshot

- AI chatbot with conversation storage and user-scoped history
- Expense optimization API that suggests monthly savings opportunities
- Financial literacy hub with structured learning modules
- Idle money and EMI-risk alerts on dashboard
- Analytics trend charts and financial score breakdown

### Key Routes

- `/dashboard/` - main financial cockpit
- `/analytics/` - trend and score analysis
- `/learn/` - financial literacy hub
- `/upload-statement/` - PDF statement import
- `/api/chatbot/` - AI chat endpoint
- `/api/expense-optimization/` - expense optimization insights

## Development Commands

```bash
python manage.py check
python manage.py test
python manage.py runserver
```

## GitHub Publish Steps

If this folder was shared without git history, initialize and publish with:

```bash
git init
git add .
git commit -m "Initial project commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

Notes:

- `.env`, `venv`, and `db.sqlite3` are ignored by default.
- Keep `.env.example` committed for setup reference.

## Deployment Checklist

- Set `DEBUG=False`
- Set secure `DJANGO_SECRET_KEY`
- Configure `ALLOWED_HOSTS`
- Use managed database for production
- Run migrations in deploy pipeline
- Configure static files handling
- Set `ANTHROPIC_API_KEY` if AI API responses are required

## Documentation

Primary project documentation:

- `SETUP_GUIDE.md`
- `ARCHITECTURE_OVERVIEW.md`

## License

Distributed under the MIT License. See `LICENSE` for details.

 
