from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from core.models import UserProfile, Transaction, EMI, SavingsGoal, AIInsight
from datetime import date, timedelta
import random


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to PaisaCoach, {user.username}! 🎉')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@require_POST
def load_demo_data(request):
    """Load sample data for demo/testing purposes."""
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.monthly_income = 65000
    profile.savings_goal = 200000
    profile.save()

    # Clear existing
    Transaction.objects.filter(user=user).delete()

    today = date.today()
    sample_data = [
        # Credits
        ('Salary - Company', 65000, 'credit', 'salary', today.replace(day=1)),
        # Debits
        ('Zomato - Food Order', 450, 'debit', 'food', today - timedelta(days=1)),
        ('Ola Cab - Office', 280, 'debit', 'transport', today - timedelta(days=2)),
        ('Netflix Subscription', 649, 'debit', 'entertainment', today - timedelta(days=3)),
        ('Big Bazaar Groceries', 2100, 'debit', 'shopping', today - timedelta(days=4)),
        ('Electricity Bill', 1800, 'debit', 'bills', today - timedelta(days=5)),
        ('Home Loan EMI', 18000, 'debit', 'emi', today - timedelta(days=2)),
        ('Car Loan EMI', 8500, 'debit', 'emi', today - timedelta(days=2)),
        ('Swiggy - Dinner', 380, 'debit', 'food', today - timedelta(days=6)),
        ('Amazon Shopping', 1599, 'debit', 'shopping', today - timedelta(days=7)),
        ('Mobile Recharge', 599, 'debit', 'bills', today - timedelta(days=8)),
        ('Gym Membership', 1200, 'debit', 'entertainment', today - timedelta(days=9)),
        ('Medical - Pharmacy', 560, 'debit', 'medical', today - timedelta(days=10)),
        ('Petrol Fill', 2000, 'debit', 'transport', today - timedelta(days=11)),
        ('SIP - Mutual Fund', 3000, 'debit', 'investment', today - timedelta(days=3)),
    ]

    for title, amount, txn_type, category, txn_date in sample_data:
        Transaction.objects.create(
            user=user,
            title=title,
            amount=amount,
            transaction_type=txn_type,
            category=category,
            date=txn_date,
        )

    messages.success(request, '✅ Demo data loaded! Explore your personalized dashboard.')
    return redirect('dashboard')


@require_POST
def clear_demo_data(request):
    """Remove demo/user-generated financial records and reset demo profile values."""
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user

    Transaction.objects.filter(user=user).delete()
    EMI.objects.filter(user=user).delete()
    SavingsGoal.objects.filter(user=user).delete()
    AIInsight.objects.filter(user=user).delete()

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.monthly_income = 0
    profile.savings_goal = 0
    profile.financial_age_score = 0
    profile.save(update_fields=['monthly_income', 'savings_goal', 'financial_age_score', 'updated_at'])

    messages.success(request, 'Demo data cleared. Your account is now reset.')
    return redirect('profile')
