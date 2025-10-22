from django.urls import path
from django.shortcuts import redirect
from . import views
from . import api_views

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
    
    # API Endpoints
    path('api/etudiants/', api_views.api_etudiants, name='api_etudiants'),
    path('api/etudiants/<int:etudiant_id>/', api_views.api_etudiant_detail, name='api_etudiant_detail'),
    path('api/etudiants/<int:etudiant_id>/moyennes/', api_views.api_moyennes, name='api_moyennes'),
    path('api/notes/', api_views.api_notes, name='api_notes'),
    path('api/notes/create/', api_views.api_note_create, name='api_note_create'),
    path('api/classes/', api_views.api_classes, name='api_classes'),
    path('api/paiements/', api_views.api_paiements, name='api_paiements'),
    path('api/statistiques/', api_views.api_statistiques, name='api_statistiques'),
    path('api/search/', api_views.api_search, name='api_search'),
    path('api/activites/', api_views.api_activites, name='api_activites'),
    
    # API Crédits
    path('api/credits/packages/', api_views.api_credits_packages, name='api_credits_packages'),
    path('api/credits/purchase/', api_views.api_credits_purchase, name='api_credits_purchase'),
    path('api/credits/callback/', api_views.api_credits_callback, name='api_credits_callback'),
    path('api/credits/status/', api_views.api_credits_status, name='api_credits_status'),
    
    # API Sauvegarde Cloud
    path('api/cloud/backup/', api_views.api_cloud_backup, name='api_cloud_backup'),
    path('api/cloud/backups/', api_views.api_cloud_backups_list, name='api_cloud_backups_list'),
    
    # API Bulletins PDF
    path('api/bulletins/generate/', api_views.api_generate_bulletin, name='api_generate_bulletin'),
    path('api/bulletins/preview/<int:etudiant_id>/<int:trimestre>/', api_views.api_bulletin_preview, name='api_bulletin_preview'),
    
    # Pages de gestion
    path('gestion/etudiants/', views.gestion_etudiants, name='gestion_etudiants'),
    path('gestion/enseignants/', views.gestion_enseignants, name='gestion_enseignants'),
    path('gestion/classes/', views.gestion_classes, name='gestion_classes'),
    path('gestion/notes/', views.gestion_notes, name='gestion_notes'),
    path('gestion/paiements/', views.gestion_paiements, name='gestion_paiements'),
    path('gestion/bulletins/', views.gestion_bulletins, name='gestion_bulletins'),
    path('gestion/parents/', views.gestion_parents, name='gestion_parents'),
    path('gestion/matieres/', views.gestion_matieres, name='gestion_matieres'),
    path('gestion/annees-scolaires/', views.gestion_annees_scolaires, name='gestion_annees_scolaires'),
    path('gestion/credits/', views.gestion_credits, name='gestion_credits'),
    path('gestion/backups/', views.gestion_backups, name='gestion_backups'),
    path('gestion/rapports/', views.gestion_rapports, name='gestion_rapports'),
    path('gestion/parametres/', views.gestion_parametres, name='gestion_parametres'),
]