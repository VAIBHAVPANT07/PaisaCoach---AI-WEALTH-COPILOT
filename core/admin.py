from django.contrib import admin
from .models import Transaction, EMI, SavingsGoal, AIInsight, UserProfile, ChatMessage

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'monthly_income', 'language_preference', 'financial_age_score']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'amount', 'transaction_type', 'category', 'date']
    list_filter = ['transaction_type', 'category']

@admin.register(EMI)
class EMIAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'monthly_amount', 'interest_rate', 'remaining_months']

@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'target_amount', 'current_amount', 'target_date']

@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight_type', 'title', 'is_read', 'created_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'message', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['user__username', 'message']
