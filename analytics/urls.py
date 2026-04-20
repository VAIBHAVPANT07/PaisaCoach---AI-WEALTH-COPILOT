from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_view, name='analytics'),
    path('api/chart/', views.api_chart_data, name='api_chart'),
]
