from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    savings_goal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    language_preference = models.CharField(max_length=10, default='en',
        choices=[('en', 'English'), ('hi', 'Hindi'), ('hinglish', 'Hinglish')])
    financial_age_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food & Dining'),
        ('transport', 'Transport'),
        ('shopping', 'Shopping'),
        ('bills', 'Bills & Utilities'),
        ('emi', 'EMI / Loan'),
        ('investment', 'Investment'),
        ('salary', 'Salary / Income'),
        ('fd', 'Fixed Deposit'),
        ('medical', 'Medical'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]
    TYPE_CHOICES = [('credit', 'Credit'), ('debit', 'Debit')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField(default=timezone.now)
    note = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"


class EMI(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emis')
    name = models.CharField(max_length=200)
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # annual %
    tenure_months = models.IntegerField()
    remaining_months = models.IntegerField()
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_interest_cost(self):
        total_paid = float(self.monthly_amount) * self.tenure_months
        return round(total_paid - float(self.principal), 2)

    def __str__(self):
        return f"{self.name} - ₹{self.monthly_amount}/mo"


class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def progress_percent(self):
        if self.target_amount == 0:
            return 0
        return min(100, round((float(self.current_amount) / float(self.target_amount)) * 100, 1))

    def __str__(self):
        return f"{self.name} - {self.progress_percent}%"


class AIInsight(models.Model):
    INSIGHT_TYPES = [
        ('idle_money', 'Idle Money Alert'),
        ('emi_trap', 'EMI Trap Warning'),
        ('salary_plan', 'Salary Day Plan'),
        ('general', 'General Insight'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_insights')
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=300)
    body = models.TextField()
    action_label = models.CharField(max_length=100, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.insight_type}: {self.title[:50]}"


class ChatMessage(models.Model):
    """Stores chatbot conversations for financial advice"""
    CATEGORY_CHOICES = [
        ('expense_cutting', 'Expense Optimization'),
        ('investment', 'Investment Advice'),
        ('budget', 'Budget Help'),
        ('emi_help', 'EMI & Loans'),
        ('savings', 'Savings Tips'),
        ('general', 'General Question'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField(help_text="User's question or message")
    response = models.TextField(help_text="AI-generated response")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_helpful = models.BooleanField(null=True, blank=True, help_text="User feedback on response")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"
