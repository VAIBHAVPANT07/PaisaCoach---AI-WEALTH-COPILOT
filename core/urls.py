from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('emis/', views.emis_view, name='emis'),
    path('goals/', views.goals_view, name='goals'),
    path('profile/', views.profile_view, name='profile'),
    path('upload-statement/', views.upload_statement, name='upload_statement'),
    path('learn/', views.learn, name='learn'),
    # API endpoints
    path('api/score/', views.api_financial_score, name='api_score'),
    path('api/insight/', views.api_ai_insight, name='api_insight'),
    path('api/idle/', views.api_idle_money, name='api_idle'),
    path('api/chatbot/', views.api_chatbot, name='api_chatbot'),
    path('api/expense-optimization/', views.api_expense_optimization, name='api_expense_optimization'),
]
