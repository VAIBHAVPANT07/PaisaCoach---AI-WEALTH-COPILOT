#!/bin/bash
# PaisaCoach Quick Start Script
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   PaisaCoach — AI Financial Coach    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install requirements
echo "→ Installing dependencies..."
pip install -r requirements.txt -q

# Setup .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "→ Created .env from .env.example"
    echo "  ⚠️  Edit .env to add your ANTHROPIC_API_KEY (optional)"
fi

# Run migrations
echo "→ Running database migrations..."
python manage.py migrate --run-syncdb -v 0

# Create demo superuser
echo "→ Creating admin user (admin/admin123)..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin','admin@example.com','admin123')
    print('  Admin created: admin / admin123')
else:
    print('  Admin already exists')
" 2>/dev/null

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ✅ Setup complete! Starting server...        ║"
echo "║                                              ║"
echo "║  → Open: http://127.0.0.1:8000               ║"
echo "║  → Click 'Try with Demo Data' to start       ║"
echo "║  → Admin: http://127.0.0.1:8000/admin/       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

python manage.py runserver
