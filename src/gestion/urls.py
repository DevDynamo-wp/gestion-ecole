from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'gestion'

urlpatterns = [
    # Redirection de la racine vers login
    path('', lambda request: redirect('gestion:login'), name='home'),
    
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/professeur/', views.dashboard_professeur, name='dashboard_professeur'),
    path('dashboard/collaborateur/', views.dashboard_collaborateur, name='dashboard_collaborateur'),
]