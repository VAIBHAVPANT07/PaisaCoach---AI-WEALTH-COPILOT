from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('load-demo/', views.load_demo_data, name='load_demo'),
    path('clear-demo/', views.clear_demo_data, name='clear_demo'),
]
