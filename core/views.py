from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Sum
from datetime import date, timedelta, datetime
import json

from .models import Transaction, EMI, SavingsGoal, AIInsight, UserProfile, ChatMessage
from .ai_engine import (
    compute_financial_age_score,
    detect_idle_money,
    analyze_emi_trap,
    salary_autopilot,
    generate_ai_insight,
    parse_bank_statement,
    analyze_expense_optimization,
    generate_chatbot_response,
)
from .forms import TransactionForm, EMIForm, SavingsGoalForm, ProfileForm


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


@login_required
def dashboard(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Date ranges
    today = date.today()
    month_start = today.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # Transactions this month
    month_txns = Transaction.objects.filter(user=user, date__gte=month_start)
    last_month_txns = Transaction.objects.filter(
        user=user, date__gte=last_month_start, date__lt=month_start
    )

    # Summaries
    income_this_month = float(month_txns.filter(transaction_type='credit').aggregate(s=Sum('amount'))['s'] or 0)
    expenses_this_month = float(month_txns.filter(transaction_type='debit').aggregate(s=Sum('amount'))['s'] or 0)
    savings_this_month = income_this_month - expenses_this_month

    income_last = float(last_month_txns.filter(transaction_type='credit').aggregate(s=Sum('amount'))['s'] or 0)
    expenses_last = float(last_month_txns.filter(transaction_type='debit').aggregate(s=Sum('amount'))['s'] or 0)

    # Income trend
    income_change = ((income_this_month - income_last) / income_last * 100) if income_last > 0 else 0
    expense_change = ((expenses_this_month - expenses_last) / expenses_last * 100) if expenses_last > 0 else 0

    # Category breakdown for chart
    cat_data = {}
    for t in month_txns.filter(transaction_type='debit'):
        cat_data[t.get_category_display()] = cat_data.get(t.get_category_display(), 0) + float(t.amount)

    # AI Features
    score_data = compute_financial_age_score(user)
    idle_data = detect_idle_money(user)
    emi_data = analyze_emi_trap(user)
    autopilot = salary_autopilot(user)

    # Latest AI insights
    insights = AIInsight.objects.filter(user=user, is_read=False)[:3]

    # Recent transactions
    recent_txns = Transaction.objects.filter(user=user)[:8]

    # Savings goals
    goals = SavingsGoal.objects.filter(user=user)[:4]

    context = {
        'profile': profile,
        'income_this_month': income_this_month,
        'expenses_this_month': expenses_this_month,
        'savings_this_month': savings_this_month,
        'income_change': round(income_change, 1),
        'expense_change': round(expense_change, 1),
        'cat_data': json.dumps(cat_data),
        'score_data': score_data,
        'idle_data': idle_data,
        'emi_data': emi_data,
        'autopilot': autopilot,
        'insights': insights,
        'recent_txns': recent_txns,
        'goals': goals,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def transactions(request):
    user = request.user
    txns = Transaction.objects.filter(user=user)

    # Filters
    cat = request.GET.get('category')
    txn_type = request.GET.get('type')
    if cat:
        txns = txns.filter(category=cat)
    if txn_type:
        txns = txns.filter(transaction_type=txn_type)

    form = TransactionForm()
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.user = user
            txn.save()
            messages.success(request, 'Transaction added!')
            return redirect('transactions')

    return render(request, 'core/transactions.html', {
        'txns': txns[:50],
        'form': form,
        'categories': Transaction.CATEGORY_CHOICES,
    })


@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.user = request.user
            txn.save()
            return JsonResponse({'success': True, 'message': 'Transaction added!'})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def delete_transaction(request, pk):
    txn = get_object_or_404(Transaction, pk=pk, user=request.user)
    txn.delete()
    messages.success(request, 'Transaction deleted.')
    return redirect('transactions')


@login_required
def emis_view(request):
    user = request.user
    emis = EMI.objects.filter(user=user, is_active=True)
    form = EMIForm()

    if request.method == 'POST':
        form = EMIForm(request.POST)
        if form.is_valid():
            emi = form.save(commit=False)
            emi.user = user
            emi.save()
            messages.success(request, 'EMI added!')
            return redirect('emis')

    emi_analysis = analyze_emi_trap(user)
    return render(request, 'core/emis.html', {
        'emis': emis,
        'form': form,
        'emi_analysis': emi_analysis,
    })


@login_required
def goals_view(request):
    user = request.user
    goals = SavingsGoal.objects.filter(user=user)
    form = SavingsGoalForm()

    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = user
            goal.save()
            messages.success(request, 'Goal created!')
            return redirect('goals')

    return render(request, 'core/goals.html', {'goals': goals, 'form': form})


@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    form = ProfileForm(instance=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')

    return render(request, 'core/profile.html', {'form': form, 'profile': profile})


@login_required
def api_financial_score(request):
    score_data = compute_financial_age_score(request.user)
    return JsonResponse(score_data)


@login_required
def api_ai_insight(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    lang = profile.language_preference
    insight = generate_ai_insight(user, language=lang)
    return JsonResponse({'insight': insight})


@login_required
def api_idle_money(request):
    data = detect_idle_money(request.user)
    return JsonResponse(data or {})


@login_required
def api_expense_optimization(request):
    """Returns expense optimization suggestions"""
    data = analyze_expense_optimization(request.user)
    return JsonResponse(data or {'error': 'No data available'})


@login_required
def api_chatbot(request):
    """Chatbot endpoint - accepts user message and returns AI response"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'error': 'Empty message'}, status=400)
            
            if len(user_message) > 500:
                return JsonResponse({'error': 'Message too long'}, status=400)
            
            # Get user language preference
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            language = profile.language_preference or 'en'
            
            # Generate response
            response_text = generate_chatbot_response(user_message, request.user, language)

            if not response_text or not str(response_text).strip():
                return JsonResponse({'error': 'Failed to generate response'}, status=500)
            
            # Save conversation
            ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=response_text,
                category='general'
            )
            
            return JsonResponse({
                'response': response_text,
                'timestamp': timezone.now().isoformat()
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Chatbot error: {str(e)}', exc_info=True)
            return JsonResponse({'error': 'Server error. Please try again.'}, status=500)
    
    # GET: Fetch conversation history
    messages = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:10]
    return JsonResponse({
        'conversations': [{
            'user_message': msg.message,
            'bot_response': msg.response,
            'timestamp': msg.created_at.isoformat(),
            'category': msg.category
        } for msg in reversed(messages)]
    })


@login_required
def upload_statement(request):
    if request.method == 'POST' and request.FILES.get('statement'):
        pdf = request.FILES['statement']
        transactions = parse_bank_statement(pdf)
        if transactions:
            created = 0
            for t in transactions:
                try:
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y']:
                        try:
                            d = datetime.strptime(t['date'], fmt).date()
                            break
                        except ValueError:
                            d = date.today()
                    Transaction.objects.create(
                        user=request.user,
                        title=t['title'],
                        amount=t['amount'],
                        transaction_type=t['type'],
                        date=d,
                        category='other',
                    )
                    created += 1
                except Exception:
                    continue
            messages.success(request, f'Imported {created} transactions from your bank statement!')
        else:
            messages.warning(request, 'Could not parse transactions. Try adding manually.')
        return redirect('transactions')
    return render(request, 'core/upload_statement.html')


# ─── Financial Literacy Hub ───────────────────────────────────────────────────

@login_required
def learn(request):
    """Financial literacy hub"""
    section = request.GET.get('section', 'overview')
    
    learning_modules = {
        'overview': {
            'title': 'Welcome to PaisaCoach Learn',
            'description': 'Master your finances with bite-sized lessons',
            'topics': ['budgeting', 'investing', 'debt-management', 'saving'],
        },
        'budgeting': {
            'title': 'Budgeting 101',
            'description': 'Learn to manage your money effectively',
            'lessons': [
                {
                    'title': '50-30-20 Rule',
                    'content': '50% for needs, 30% for wants, 20% for savings. This simple rule helps you allocate your income wisely.',
                    'icon': '📊'
                },
                {
                    'title': 'Track Your Spending',
                    'content': 'Keep a record of every transaction. PaisaCoach automatically categorizes your spending by food, transport, bills, etc.',
                    'icon': '📝'
                },
                {
                    'title': 'Set Monthly Limits',
                    'content': 'Decide how much you want to spend in each category and stick to it. Use PaisaCoach to monitor progress.',
                    'icon': '🎯'
                },
            ]
        },
        'investing': {
            'title': 'Investment Basics',
            'description': 'Grow your wealth with smart investments',
            'lessons': [
                {
                    'title': 'Fixed Deposit (FD)',
                    'content': '✅ Safest option (guaranteed returns)\n✅ Current rates: 6.5-7.5% p.a.\n⏰ Lock-in period: 3 months to 5+ years\n💡 Best for: Risk-averse investors',
                    'icon': '🏛️'
                },
                {
                    'title': 'Mutual Funds',
                    'content': '📈 Growth potential: 10-15% p.a.\n🎯 Invest in stocks/bonds/gold\n📊 Professional management\n💡 Best for: Long-term wealth building',
                    'icon': '📈'
                },
                {
                    'title': 'Savings Account vs FD',
                    'content': 'Savings Account: 3.5% returns\nFixed Deposit: 7.5% returns\n\nInvesting ₹5,000/month in FD instead of savings: ₹10,80,000 extra in 30 years! 🚀',
                    'icon': '⚖️'
                },
                {
                    'title': 'The Power of Compound Interest',
                    'content': 'Start investing early. ₹5,000/month at 12% returns:\n- After 5 years: ₹3.8 lakhs\n- After 10 years: ₹10 lakhs\n- After 20 years: ₹47 lakhs\n- After 30 years: ₹1.5 crores 🤯',
                    'icon': '💰'
                },
            ]
        },
        'debt-management': {
            'title': 'EMI & Debt Management',
            'description': 'Use loans wisely and become debt-free',
            'lessons': [
                {
                    'title': 'EMI Danger Zones',
                    'content': '✅ Safe: EMI < 20% of income\n⚠️ Warning: EMI 20-40% of income\n🚨 Danger: EMI > 40% of income\n\nWhen EMI is too high, your quality of life suffers.',
                    'icon': '🚨'
                },
                {
                    'title': 'Avalanche Method (Smart Repayment)',
                    'content': 'Pay off loans with HIGHEST interest rates first.\n\nExample:\n- Car Loan: 12% interest\n- Personal Loan: 15% interest\n- Home Loan: 7% interest\n\nPay extra on Personal Loan first to save the most interest! 💡',
                    'icon': '📉'
                },
                {
                    'title': 'Pre-payment Benefits',
                    'content': 'Pre-pay your high-interest loans to save lakhs in interest.\n\nExample: ₹10 lakh personal loan at 15%\n- Regular: 60 months, ₹3.1 lakh interest\n- Pre-pay ₹3,000 extra/month: 40 months, ₹1.6 lakh interest\n- Savings: ₹1.5 lakhs! 🎉',
                    'icon': '✂️'
                },
            ]
        },
        'saving': {
            'title': 'Smart Saving Tips',
            'description': 'Build wealth with consistent saving habits',
            'lessons': [
                {
                    'title': 'Emergency Fund (3-6 Months)',
                    'content': 'Save 3-6 months of expenses in a liquid account.\n\nYour monthly expense: ₹50,000\nEmergency fund needed: ₹1.5-3 lakhs\n\nThis fund protects you during job loss, medical emergency, etc.',
                    'icon': '🛡️'
                },
                {
                    'title': 'Automate Your Savings',
                    'content': 'Set up auto-transfers on salary day. What you don\'t see, you don\'t spend.\n\n💡 Start small: Even ₹2,000/month becomes ₹7.2 lakhs in 30 years!',
                    'icon': '⚙️'
                },
                {
                    'title': 'Cut Unnecessary Expenses',
                    'content': 'Track subscriptions: Netflix, Gym, Streaming apps\nSave on food: Cook at home vs eating out\nReduce shopping: Use a list, set limits\n\nPotential monthly savings: ₹5,000-10,000 💰',
                    'icon': '✂️'
                },
            ]
        },
    }

    if section not in learning_modules:
        section = 'overview'

    current_section = learning_modules[section]
    nav_modules = [
        {
            'key': key,
            'title': value.get('title', key.title()),
        }
        for key, value in learning_modules.items()
        if key != 'overview'
    ]
    
    return render(request, 'core/learn.html', {
        'section': section,
        'current_section': current_section,
        'modules': list(learning_modules.keys()),
        'all_modules': learning_modules,
        'nav_modules': nav_modules,
    })
