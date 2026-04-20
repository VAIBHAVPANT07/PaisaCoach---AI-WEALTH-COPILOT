"""
AI Engine for PaisaCoach
Handles: Financial Age Score, Idle Money Detection, EMI Trap, Salary Autopilot
Uses Claude API for NLP insights + rule-based ML scoring
"""
import json
import math
from decimal import Decimal
from datetime import date, timedelta
from django.conf import settings
from django.utils import timezone


# ─── Financial Age Score Algorithm ────────────────────────────────────────────
# Behavioral scoring inspired by behavioral finance research
# Score range: 18–70 (lower = financially immature, higher = wise)

def compute_financial_age_score(user):
    """
    Computes a 'Financial Age' score based on spending behavior.
    Returns dict with score, label, breakdown, and action items.
    """
    from core.models import Transaction, EMI, SavingsGoal

    score = 40  # baseline
    breakdown = {}

    transactions = Transaction.objects.filter(user=user)
    recent_txns = transactions.filter(date__gte=date.today() - timedelta(days=90))

    if not recent_txns.exists():
        return {
            'score': 25,
            'label': 'Uncharted',
            'color': '#94a3b8',
            'breakdown': {},
            'actions': ['Add your transactions to get your Financial Age Score.']
        }

    total_credit = sum(float(t.amount) for t in recent_txns.filter(transaction_type='credit'))
    total_debit = sum(float(t.amount) for t in recent_txns.filter(transaction_type='debit'))

    # 1. Savings Rate (0-20 pts)
    if total_credit > 0:
        savings_rate = (total_credit - total_debit) / total_credit
        if savings_rate >= 0.30:
            pts = 20
        elif savings_rate >= 0.20:
            pts = 15
        elif savings_rate >= 0.10:
            pts = 10
        elif savings_rate >= 0.05:
            pts = 5
        else:
            pts = 0
        score += pts
        breakdown['Savings Rate'] = {'points': pts, 'max': 20, 'value': f"{savings_rate*100:.1f}%"}

    # 2. Investment Behavior (0-15 pts)
    investment_txns = recent_txns.filter(category__in=['investment', 'fd'])
    if investment_txns.exists():
        inv_amount = sum(float(t.amount) for t in investment_txns)
        inv_ratio = inv_amount / total_credit if total_credit > 0 else 0
        pts = min(15, int(inv_ratio * 100))
        score += pts
        breakdown['Investing'] = {'points': pts, 'max': 15, 'value': f"₹{inv_amount:.0f} invested"}
    else:
        breakdown['Investing'] = {'points': 0, 'max': 15, 'value': 'No investments found'}

    # 3. EMI Burden (0 to -15 pts penalty)
    emis = EMI.objects.filter(user=user, is_active=True)
    monthly_income = float(user.profile.monthly_income) if user.profile.monthly_income else total_credit / 3
    if emis.exists() and monthly_income > 0:
        total_emi = sum(float(e.monthly_amount) for e in emis)
        emi_ratio = total_emi / monthly_income
        if emi_ratio > 0.5:
            pts = -15
        elif emi_ratio > 0.4:
            pts = -10
        elif emi_ratio > 0.3:
            pts = -5
        else:
            pts = 0
        score += pts
        breakdown['EMI Burden'] = {'points': pts, 'max': 0, 'value': f"{emi_ratio*100:.1f}% of income"}

    # 4. Category Diversity (0-10 pts) - diversified spending = mature
    categories_used = recent_txns.values_list('category', flat=True).distinct().count()
    pts = min(10, categories_used * 2)
    score += pts
    breakdown['Spending Diversity'] = {'points': pts, 'max': 10, 'value': f"{categories_used} categories"}

    # 5. Goals Existence (0-10 pts)
    goals = SavingsGoal.objects.filter(user=user)
    if goals.exists():
        pts = min(10, goals.count() * 5)
        score += pts
        breakdown['Goals Set'] = {'points': pts, 'max': 10, 'value': f"{goals.count()} goals"}
    else:
        breakdown['Goals Set'] = {'points': 0, 'max': 10, 'value': 'No savings goals'}

    # Clamp score
    score = max(18, min(70, score))

    # Label
    if score >= 60:
        label, color = 'Financial Sage', '#10b981'
    elif score >= 50:
        label, color = 'Growing Investor', '#3b82f6'
    elif score >= 40:
        label, color = 'Cautious Saver', '#f59e0b'
    elif score >= 30:
        label, color = 'Spending Freely', '#f97316'
    else:
        label, color = 'Money Novice', '#ef4444'

    # Action items
    actions = []
    if breakdown.get('Savings Rate', {}).get('points', 0) < 10:
        actions.append("Increase your savings rate — aim for at least 20% of income.")
    if breakdown.get('Investing', {}).get('points', 0) == 0:
        actions.append("Start investing — even ₹500/month in an FD beats 0.")
    if breakdown.get('EMI Burden', {}).get('points', 0) < 0:
        actions.append("Your EMI burden is high — consider prepaying the highest-interest loan first.")
    if breakdown.get('Goals Set', {}).get('points', 0) == 0:
        actions.append("Set at least one savings goal to build financial discipline.")

    return {
        'score': score,
        'label': label,
        'color': color,
        'breakdown': breakdown,
        'actions': actions
    }


# ─── Idle Money Detector ───────────────────────────────────────────────────────

def detect_idle_money(user):
    """
    Identifies money sitting idle in savings (not invested).
    Returns estimated idle amount and opportunity cost.
    """
    from core.models import Transaction

    thirty_days_ago = date.today() - timedelta(days=30)
    recent = Transaction.objects.filter(user=user, date__gte=thirty_days_ago)

    credits = sum(float(t.amount) for t in recent.filter(transaction_type='credit'))
    debits = sum(float(t.amount) for t in recent.filter(transaction_type='debit'))
    invested = sum(float(t.amount) for t in recent.filter(category__in=['investment', 'fd']))

    idle = max(0, credits - debits - invested)

    if idle < 1000:
        return None

    # Opportunity cost calculation
    savings_rate = 0.035   # typical savings account
    fd_rate = 0.075        # typical FD rate
    months = 6

    current_earnings = idle * (savings_rate / 12) * months
    fd_earnings = idle * (fd_rate / 12) * months
    opportunity_cost = fd_earnings - current_earnings

    return {
        'idle_amount': round(idle, 2),
        'opportunity_cost': round(opportunity_cost, 2),
        'fd_earnings': round(fd_earnings, 2),
        'current_earnings': round(current_earnings, 2),
        'months': months,
        'fd_rate': fd_rate * 100,
    }


# ─── EMI Trap Analyzer ─────────────────────────────────────────────────────────

def analyze_emi_trap(user):
    """
    Analyzes EMI burden and suggests which to prepay first (avalanche method).
    """
    from core.models import EMI

    emis = EMI.objects.filter(user=user, is_active=True)
    monthly_income = float(user.profile.monthly_income) if user.profile.monthly_income else 0

    if not emis.exists():
        return None

    total_monthly_emi = sum(float(e.monthly_amount) for e in emis)
    emi_ratio = (total_monthly_emi / monthly_income * 100) if monthly_income > 0 else 0

    # Avalanche method: sort by interest rate descending
    sorted_emis = sorted(emis, key=lambda e: float(e.interest_rate), reverse=True)

    danger = emi_ratio > 40
    warning = 30 < emi_ratio <= 40

    return {
        'total_monthly': round(total_monthly_emi, 2),
        'emi_ratio': round(emi_ratio, 1),
        'danger': danger,
        'warning': warning,
        'sorted_emis': [
            {
                'name': e.name,
                'monthly': float(e.monthly_amount),
                'rate': float(e.interest_rate),
                'remaining': e.remaining_months,
                'interest_cost': e.total_interest_cost(),
            } for e in sorted_emis
        ],
        'prepay_first': sorted_emis[0].name if sorted_emis else None,
    }


# ─── Salary Day Autopilot ──────────────────────────────────────────────────────

def salary_autopilot(user):
    """
    Suggests optimal salary split based on past 3 months of spending.
    Uses rule-based ML (50/30/20 adapted for Indian context).
    """
    from core.models import Transaction

    ninety_ago = date.today() - timedelta(days=90)
    txns = Transaction.objects.filter(user=user, date__gte=ninety_ago, transaction_type='debit')

    income = float(user.profile.monthly_income) if user.profile.monthly_income else 0
    if income == 0:
        return None

    # Category spending averages over 3 months
    category_totals = {}
    for t in txns:
        category_totals[t.category] = category_totals.get(t.category, 0) + float(t.amount)

    avg = {k: v / 3 for k, v in category_totals.items()}

    emi_monthly = avg.get('emi', 0)
    living = avg.get('food', 0) + avg.get('transport', 0) + avg.get('bills', 0) + avg.get('medical', 0)
    entertainment = avg.get('entertainment', 0) + avg.get('shopping', 0)

    # Suggested split
    emergency_fund = income * 0.05
    investments = income * 0.20
    remaining = income - emi_monthly - living - entertainment - emergency_fund

    return {
        'income': income,
        'suggested': {
            'EMIs': round(emi_monthly, 0),
            'Living Expenses': round(living, 0),
            'Entertainment': round(entertainment, 0),
            'Emergency Buffer': round(emergency_fund, 0),
            'Invest / Save': round(max(0, income - emi_monthly - living - entertainment - emergency_fund), 0),
        },
        'avg_spending': avg,
    }


# ─── Claude AI Insight Generator ──────────────────────────────────────────────

def generate_ai_insight(user, language='en'):
    """
    Calls Claude API to generate personalized financial insight.
    Falls back to rule-based insight if API key not set.
    """
    from core.models import Transaction

    idle = detect_idle_money(user)
    emi_data = analyze_emi_trap(user)
    score_data = compute_financial_age_score(user)

    # Build context for Claude
    context = {
        'financial_age': score_data['score'],
        'financial_label': score_data['label'],
        'idle_money': idle['idle_amount'] if idle else 0,
        'emi_ratio': emi_data['emi_ratio'] if emi_data else 0,
        'monthly_income': float(user.profile.monthly_income),
        'language': language,
    }

    api_key = settings.ANTHROPIC_API_KEY

    if not api_key:
        # Rule-based fallback
        if idle and idle['idle_amount'] > 5000:
            return f"You have ₹{idle['idle_amount']:,.0f} sitting idle. Moving it to a 6-month FD at {idle['fd_rate']}% could earn you ₹{idle['opportunity_cost']:,.0f} more than your savings account."
        elif emi_data and emi_data['danger']:
            return f"Your EMIs consume {emi_data['emi_ratio']}% of income — that's in the danger zone (>40%). Focus on prepaying '{emi_data['prepay_first']}' first to reduce interest burden."
        else:
            return f"Your Financial Age is {score_data['score']} ({score_data['label']}). {score_data['actions'][0] if score_data['actions'] else 'Keep up the good work!'}"

    try:
        import urllib.request
        import urllib.error

        lang_instruction = {
            'hi': 'Respond in Hindi.',
            'hinglish': 'Respond in Hinglish (Hindi-English mix, casual tone like a friend).',
            'en': 'Respond in clear, simple English.',
        }.get(language, 'Respond in English.')

        prompt = f"""You are PaisaCoach, a friendly AI financial advisor for Indians.

User's financial snapshot:
- Financial Age Score: {context['financial_age']} ({context['financial_label']})
- Idle money (not invested): ₹{context['idle_money']:,.0f}
- EMI to income ratio: {context['emi_ratio']}%
- Monthly income: ₹{context['monthly_income']:,.0f}

{lang_instruction}

Give ONE specific, actionable financial insight in 2-3 sentences. Be direct, empathetic, and use rupee amounts. No generic advice."""

        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}]
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data['content'][0]['text']

    except Exception:
        return f"Your Financial Age is {score_data['score']} ({score_data['label']}). {score_data['actions'][0] if score_data['actions'] else 'Add more transactions for deeper insights.'}"


# ─── Bank Statement PDF Parser ─────────────────────────────────────────────────

def parse_bank_statement(pdf_file):
    """
    Parses bank statement PDF to extract transactions.
    Returns list of transaction dicts.
    """
    try:
        import pdfplumber
        import re

        transactions = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                for line in lines:
                    # Match patterns like: 15/04/2024  UPI/Some Merchant  5000.00  Dr
                    match = re.search(
                        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}).*?([\d,]+\.?\d{0,2})\s*(Dr|Cr|CR|DR)',
                        line, re.IGNORECASE
                    )
                    if match:
                        amount_str = match.group(2).replace(',', '')
                        txn_type = 'debit' if match.group(3).upper() == 'DR' else 'credit'
                        # Extract description (between date and amount)
                        desc = line[match.start(1)+10:match.start(2)].strip()[:100]
                        transactions.append({
                            'date': match.group(1),
                            'title': desc or 'Bank Transaction',
                            'amount': float(amount_str),
                            'type': txn_type,
                        })

        return transactions[:100]  # Limit to 100 transactions

    except ImportError:
        return []
    except Exception:
        return []


# ─── Expense Optimization & Analysis ──────────────────────────────────────────

def analyze_expense_optimization(user):
    """
    Analyzes spending patterns and suggests specific cuts.
    Returns dict with categories, percentages, and savings tips.
    """
    from core.models import Transaction
    from decimal import Decimal
    
    transactions = Transaction.objects.filter(
        user=user,
        date__gte=date.today() - timedelta(days=90),
        transaction_type='debit'
    )
    
    if not transactions.exists():
        return None
    
    # Group by category
    spending = {}
    total_spent = Decimal(0)
    
    for txn in transactions:
        category = txn.get_category_display()
        spending[category] = spending.get(category, Decimal(0)) + Decimal(str(txn.amount))
        total_spent += Decimal(str(txn.amount))
    
    if total_spent == 0:
        return None
    
    # Calculate percentages and identify top spenders
    top_categories = sorted(
        [(cat, float((amt/total_spent)*100), float(amt)) for cat, amt in spending.items()],
        key=lambda x: x[2],
        reverse=True
    )[:5]
    
    # Generate smart suggestions
    suggestions = []
    
    # Tip 1: Food/Dining
    food_cat = next((c for c in top_categories if 'food' in c[0].lower()), None)
    if food_cat and food_cat[1] > 15:
        potential_save = int(food_cat[2] * 0.25)
        suggestions.append({
            'category': 'Food & Dining',
            'current': f"₹{int(food_cat[2])}/month",
            'action': f'Cook 2 meals/week at home → Save ₹{potential_save}/month',
            'impact': f'₹{potential_save*3}/quarter'
        })
    
    # Tip 2: Entertainment
    entertainment_cat = next((c for c in top_categories if 'entertainment' in c[0].lower()), None)
    if entertainment_cat and entertainment_cat[1] > 5:
        potential_save = int(entertainment_cat[2] * 0.40)
        suggestions.append({
            'category': 'Entertainment',
            'current': f"₹{int(entertainment_cat[2])}/month",
            'action': f'Skip 1-2 outings/month → Save ₹{potential_save}/month',
            'impact': f'₹{potential_save*3}/quarter'
        })
    
    # Tip 3: Shopping
    shopping_cat = next((c for c in top_categories if 'shopping' in c[0].lower()), None)
    if shopping_cat and shopping_cat[1] > 8:
        potential_save = int(shopping_cat[2] * 0.30)
        suggestions.append({
            'category': 'Shopping',
            'current': f"₹{int(shopping_cat[2])}/month",
            'action': f'Set shopping budget & plan purchases → Save ₹{potential_save}/month',
            'impact': f'₹{potential_save*3}/quarter'
        })
    
    # Tip 4: Transport
    transport_cat = next((c for c in top_categories if 'transport' in c[0].lower()), None)
    if transport_cat and transport_cat[1] > 10:
        potential_save = int(transport_cat[2] * 0.20)
        suggestions.append({
            'category': 'Transport',
            'current': f"₹{int(transport_cat[2])}/month",
            'action': f'Use public transport 2 days/week → Save ₹{potential_save}/month',
            'impact': f'₹{potential_save*3}/quarter'
        })
    
    total_monthly_save = sum(
        int(s['impact'].split('₹')[1].split('/')[0]) // 3 
        for s in suggestions
    )
    
    return {
        'top_categories': top_categories,
        'total_monthly': int(total_spent / 3),  # Average monthly
        'suggestions': suggestions[:3],  # Top 3 suggestions
        'total_potential_save': total_monthly_save,
        'breakdown': {cat: pct for cat, pct, _ in top_categories}
    }


def generate_chatbot_response(user_message, user, language='en'):
    """
    Generates chatbot response using Claude API (or fallback rules).
    Context-aware based on user's financial data.
    """
    from core.models import Transaction, EMI, SavingsGoal, UserProfile
    
    try:
        profile = UserProfile.objects.get(user=user)
    except:
        profile = None
    
    # Get user financial context
    transactions = Transaction.objects.filter(user=user, date__gte=date.today() - timedelta(days=90))
    emis = EMI.objects.filter(user=user)
    goals = SavingsGoal.objects.filter(user=user)
    
    # Calculate context
    total_debit = sum(float(t.amount) for t in transactions.filter(transaction_type='debit'))
    total_credit = sum(float(t.amount) for t in transactions.filter(transaction_type='credit'))
    avg_monthly_expense = int(total_debit / 3) if transactions.exists() else 0
    avg_monthly_income = int(total_credit / 3) if transactions.exists() else 0
    
    # Try Claude API first
    try:
        import anthropic
        
        # Check if API key is configured
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY.strip() == '':
            raise Exception('API key not configured')
        
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Calculate EMI burden safely
        total_emi = sum(float(e.monthly_amount) for e in emis)
        emi_burden = (total_emi / avg_monthly_income * 100) if avg_monthly_income > 0 else 0
        
        system_prompt = f"""You are PaisaCoach, an AI financial advisor for Indian users speaking {language.upper()}.
User Profile:
- Monthly Income: ₹{avg_monthly_income}
- Monthly Expenses: ₹{avg_monthly_expense}
- Active EMIs: {emis.count()}
- Savings Goals: {goals.count()}
- EMI Burden: {emi_burden:.1f}% of income

Provide practical, actionable financial advice. Use Indian context. Be conversational and friendly.
Keep responses under 200 words. Include specific amounts and timeframes."""
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        return message.content[0].text
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'Chatbot API unavailable, using fallback: {str(e)}')
        # Fallback: Rule-based responses
        return generate_fallback_response(user_message, avg_monthly_income, avg_monthly_expense, emis.count(), language)


def generate_fallback_response(message, monthly_income, monthly_expense, emi_count, language='en'):
    """
    Fallback rule-based chatbot responses when Claude API unavailable.
    """
    msg_lower = message.lower()
    
    # Expense cutting
    if any(word in msg_lower for word in ['save', 'cut', 'reduce', 'expense', 'spending']):
        potential_save = int(monthly_expense * 0.15)
        if language == 'hi':
            return f"""आपकी खर्च ₹{monthly_expense} प्रति माह है। 

💡 ये सुझाव आजमाएँ:
• खाना-पीना: घर पर 2 भोजन करें → बचत ₹{int(monthly_expense*0.08)}/माह
• मनोरंजन: 1-2 बार कम बाहर जाएँ → बचत ₹{int(monthly_expense*0.05)}/माह
• खरीदारी: योजना बनाकर खरीदें → बचत ₹{int(monthly_expense*0.03)}/माह

कुल बचत संभव: ₹{potential_save}/माह = ₹{potential_save*12}/साल 📈"""
        else:
            return f"""Your monthly expenses are ₹{monthly_expense}.

💡 Try these steps:
• Food & Dining: Cook 2 meals at home → Save ₹{int(monthly_expense*0.08)}/month
• Entertainment: Skip 1-2 outings → Save ₹{int(monthly_expense*0.05)}/month
• Shopping: Plan purchases → Save ₹{int(monthly_expense*0.03)}/month

Total potential savings: ₹{potential_save}/month = ₹{potential_save*12}/year 📈"""
    
    # Investment advice
    elif any(word in msg_lower for word in ['invest', 'fd', 'mutual', 'fund', 'return', 'growth']):
        if language == 'hi':
            return f"""आपकी मासिक आय ₹{monthly_income} है।

📊 निवेश सुझाव:
• FD (पूरी तरह सुरक्षित): 7.5% रिटर्न, ₹{int(monthly_income*0.1)}/माह
• Mutual Fund (संतुलित): 12% रिटर्न, ₹{int(monthly_income*0.05)}/माह  
• मिक्स: 60% FD + 40% MF = 9% औसत रिटर्न

₹{int(monthly_income*0.10)}/माह निवेश करें → 30 साल में ₹{int(monthly_income*0.10)*12*30*1.5}लाख! 🚀"""
        else:
            return f"""Your monthly income is ₹{monthly_income}.

📊 Investment recommendation:
• FD (Very Safe): 7.5% returns, invest ₹{int(monthly_income*0.1)}/month
• Mutual Fund (Balanced): 12% returns, invest ₹{int(monthly_income*0.05)}/month
• Mix Strategy: 60% FD + 40% MF = 9% average

Invest ₹{int(monthly_income*0.10)}/month → ₹{int(monthly_income*0.10)*12*30*1.5} in 30 years! 🚀"""
    
    # EMI & Loan help
    elif any(word in msg_lower for word in ['emi', 'loan', 'loan', 'debt', 'repay', 'borrow']):
        emi_burden = (emi_count * 3000 / monthly_income * 100) if monthly_income > 0 else 0
        if language == 'hi':
            return f"""आपके {emi_count} EMIs हैं।

⚠️ EMI बोझ: {emi_burden:.1f}% of income
{'✅ सुरक्षित है (20% से कम)' if emi_burden < 20 else '⚠️ चेतावनी (20-40%)' if emi_burden < 40 else '🚨 ख़तरा (40% से ज़्यादा)'}

💡 सुझाव:
• सबसे ज़्यादा ब्याज वाले EMI पहले चुकाएँ (avalanche method)
• अगर संभव हो तो प्री-पेमेंट करें
• नए कर्ज लेने से बचें

मदद के लिए EMI पेज देखें!"""
        else:
            return f"""You have {emi_count} active EMIs.

⚠️ EMI burden: {emi_burden:.1f}% of income
{'✅ Safe (under 20%)' if emi_burden < 20 else '⚠️ Warning (20-40%)' if emi_burden < 40 else '🚨 Danger (over 40%)'}

💡 Best practices:
• Pay highest interest EMI first (avalanche method)
• Pre-pay when possible to save on interest
• Avoid taking new loans

Check your EMI page for detailed analysis!"""
    
    # Budget help
    elif any(word in msg_lower for word in ['budget', 'planning', 'allocate', 'month']):
        if language == 'hi':
            return f"""आपके लिए 50-30-20 budget सुझाव:

💰 आय: ₹{monthly_income}/माह

📊 सुझाव विभाजन:
• जरूरत (50%): ₹{int(monthly_income*0.5)} - घर, खाना, transport
• चाहत (30%): ₹{int(monthly_income*0.3)} - मनोरंजन, शौक
• बचत (20%): ₹{int(monthly_income*0.2)} - FD, निवेश, emergency

आपका वर्तमान खर्च: ₹{monthly_expense} ({(monthly_expense/monthly_income*100):.0f}% of income)"""
        else:
            return f"""Here's a 50-30-20 budget for you:

💰 Your Income: ₹{monthly_income}/month

📊 Suggested allocation:
• Needs (50%): ₹{int(monthly_income*0.5)} - Housing, food, transport
• Wants (30%): ₹{int(monthly_income*0.3)} - Entertainment, hobbies
• Savings (20%): ₹{int(monthly_income*0.2)} - FD, investments, emergency

Your current spending: ₹{monthly_expense} ({(monthly_expense/monthly_income*100):.0f}% of income)"""
    
    # Default response
    else:
        if language == 'hi':
            return """नमस्ते! 👋 मैं PaisaCoach हूँ, आपका AI वित्तीय सलाहकार।

मुझसे पूछें:
• "मैं खर्च कहाँ से कम कर सकता हूँ?"
• "FD या Mutual Fund में निवेश करूँ?"
• "मेरे EMI बहुत हैं क्या?"
• "मासिक बजट कैसे बनाऊँ?"

आपकी खर्च और आय के आधार पर मैं specific सुझाव दूँगा! 💡"""
        else:
            return """Hello! 👋 I'm PaisaCoach, your AI financial advisor.

Ask me about:
• "Where can I cut expenses?"
• "Should I invest in FD or Mutual Fund?"
• "Are my EMIs too high?"
• "How do I plan my monthly budget?"

I'll give you personalized advice based on your spending! 💡"""
