from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Transaction
from core.ai_engine import compute_financial_age_score, detect_idle_money, analyze_emi_trap
from django.db.models import Sum
from datetime import date, timedelta
import json


@login_required
def analytics_view(request):
    user = request.user
    score_data = compute_financial_age_score(user)
    idle_data = detect_idle_money(user)
    emi_data = analyze_emi_trap(user)

    # Monthly trend - last 6 months
    months_data = []
    today = date.today()
    for i in range(5, -1, -1):
        m_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        if i > 0:
            m_end = (m_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            m_end = today
        txns = Transaction.objects.filter(user=user, date__gte=m_start, date__lte=m_end)
        income = float(txns.filter(transaction_type='credit').aggregate(s=Sum('amount'))['s'] or 0)
        expense = float(txns.filter(transaction_type='debit').aggregate(s=Sum('amount'))['s'] or 0)
        months_data.append({
            'month': m_start.strftime('%b'),
            'income': income,
            'expense': expense,
            'savings': income - expense,
        })

    return render(request, 'analytics/analytics.html', {
        'score_data': score_data,
        'idle_data': idle_data,
        'emi_data': emi_data,
        'months_data': json.dumps(months_data),
    })


@login_required
def api_chart_data(request):
    user = request.user
    period = request.GET.get('period', '30')
    days = int(period)
    start = date.today() - timedelta(days=days)

    txns = Transaction.objects.filter(user=user, date__gte=start, transaction_type='debit')
    cat_data = {}
    for t in txns:
        label = t.get_category_display()
        cat_data[label] = cat_data.get(label, 0) + float(t.amount)

    return JsonResponse({'categories': cat_data})
