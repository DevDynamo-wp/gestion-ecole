from django.db import models
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Sum
from datetime import datetime, timedelta
from .models import (
    Etudiant, Enseignant, Classe, Note, Paiement, 
    Bulletin, AnneeScolaire, Journal, Depart
)

# ========== AUTHENTIFICATION ==========

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('gestion:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Enregistrer l'action dans le journal
            Journal.objects.create(
                utilisateur=user,
                action='login',
                entite='utilisateur',
                description=f"{user.username} s'est connecté",
                adresse_ip=get_client_ip(request)
            )
            return redirect('gestion:dashboard')
        else:
            return render(request, 'gestion/login.html', {
                'error': 'Identifiants incorrects'
            })
    
    return render(request, 'gestion/login.html')


@login_required(login_url='gestion:login')
def logout_view(request):
    """Vue de déconnexion"""
    if request.user.is_authenticated:
        Journal.objects.create(
            utilisateur=request.user,
            action='logout',
            entite='utilisateur',
            description=f"{request.user.username} s'est déconnecté",
            adresse_ip=get_client_ip(request)
        )
    logout(request)
    return redirect('gestion:login')


# ========== DASHBOARD PRINCIPAL ==========

@login_required(login_url='gestion:login')
def dashboard(request):
    """Dashboard principal - Route vers le dashboard approprié selon le rôle"""
    user = request.user
    
    # Déterminer le rôle de l'utilisateur
    try:
        enseignant = Enseignant.objects.get(user=user)
        return dashboard_professeur(request, enseignant)
    except Enseignant.DoesNotExist:
        pass
    
    # Si admin
    if user.is_staff or user.is_superuser:
        return dashboard_admin(request)
    
    # Par défaut : collaborateur
    return dashboard_collaborateur(request)


# ========== DASHBOARD ADMIN ==========

@login_required(login_url='gestion:login')
def dashboard_admin(request):
    """Dashboard pour l'administrateur"""
    
    # Statistiques globales
    total_etudiants = Etudiant.objects.filter(is_active=True).count()
    total_enseignants = Enseignant.objects.filter(is_active=True).count()
    total_classes = Classe.objects.count()
    
    # Paiements
    total_paiements = Paiement.objects.count()
    paiements_ce_mois = Paiement.objects.filter(
        date_paiement__month=datetime.now().month,
        date_paiement__year=datetime.now().year
    ).count()
    
    montant_total_paiements = Paiement.objects.aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Activités récentes (derniers 10 jours)
    date_limite = datetime.now() - timedelta(days=10)
    activites = Journal.objects.filter(
        date_action__gte=date_limite
    ).order_by('-date_action')[:10]
    
    # Étudiants par classe
    etudiants_par_classe = Classe.objects.annotate(
        nb_etudiants=Count('assignationetudiantclasse')
    ).order_by('-nb_etudiants')[:5]
    
    # Taux de paiement
    etudiants_avec_paiement = Paiement.objects.filter(
        date_paiement__year=datetime.now().year
    ).values('etudiant').distinct().count()
    taux_paiement = (etudiants_avec_paiement / total_etudiants * 100) if total_etudiants > 0 else 0
    
    # Départs récents
    departures = Depart.objects.order_by('-date_depart')[:5]
    
    context = {
        'role': 'admin',
        'total_etudiants': total_etudiants,
        'total_enseignants': total_enseignants,
        'total_classes': total_classes,
        'total_paiements': total_paiements,
        'paiements_ce_mois': paiements_ce_mois,
        'montant_total_paiements': montant_total_paiements,
        'taux_paiement': round(taux_paiement, 1),
        'activites': activites,
        'etudiants_par_classe': etudiants_par_classe,
        'departures': departures,
    }
    
    return render(request, 'gestion/dashboard_admin.html', context)


# ========== DASHBOARD PROFESSEUR ==========

@login_required(login_url='gestion:login')
def dashboard_professeur(request, enseignant=None):
    """Dashboard pour l'enseignant"""
    
    # Si enseignant n'est pas fourni, le récupérer
    if enseignant is None:
        try:
            enseignant = Enseignant.objects.get(user=request.user)
        except Enseignant.DoesNotExist:
            return redirect('gestion:dashboard')
    
    # Classes enseignées
    classes = Classe.objects.filter(
        assignationclassematiereenseignant__enseignant=enseignant
    ).distinct()
    
    total_classes = classes.count()
    
    # Total d'étudiants
    total_etudiants = Etudiant.objects.filter(
        assignationetudiantclasse__classe__in=classes,
        is_active=True
    ).distinct().count()
    
    # Notes enregistrées
    notes_enregistrees = Note.objects.filter(
        matiere__assignationclassematiereenseignant__enseignant=enseignant
    ).count()
    
    # Bulletins générés
    bulletins_generes = Bulletin.objects.filter(
        classe__in=classes
    ).count()
    
    # Activités récentes de cet enseignant
    date_limite = datetime.now() - timedelta(days=7)
    activites = Journal.objects.filter(
        utilisateur=request.user,
        date_action__gte=date_limite
    ).order_by('-date_action')[:8]
    
    # Dernières notes enregistrées
    dernieres_notes = Note.objects.filter(
        matiere__assignationclassematiereenseignant__enseignant=enseignant
    ).order_by('-date_enregistrement')[:10]
    
    context = {
        'role': 'professeur',
        'enseignant': enseignant,
        'total_classes': total_classes,
        'total_etudiants': total_etudiants,
        'notes_enregistrees': notes_enregistrees,
        'bulletins_generes': bulletins_generes,
        'activites': activites,
        'dernieres_notes': dernieres_notes,
        'classes': classes[:10],
    }
    
    return render(request, 'gestion/dashboard_professeur.html', context)


# ========== DASHBOARD COLLABORATEUR ==========

@login_required(login_url='gestion:login')
def dashboard_collaborateur(request):
    """Dashboard pour le collaborateur/secrétaire"""
    
    # Statistiques de base
    total_etudiants = Etudiant.objects.filter(is_active=True).count()
    nouveaux_etudiants = Etudiant.objects.filter(
        is_active=True,
        statut='nouvel_inscrit',
        date_inscription__gte=datetime.now() - timedelta(days=30)
    ).count()
    
    # Paiements
    total_paiements_mois = Paiement.objects.filter(
        date_paiement__month=datetime.now().month,
        date_paiement__year=datetime.now().year
    ).count()
    
    montant_paiements_mois = Paiement.objects.filter(
        date_paiement__month=datetime.now().month,
        date_paiement__year=datetime.now().year
    ).aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Classes
    total_classes = Classe.objects.count()
    
    # Activités récentes (inscriptions, paiements)
    date_limite = datetime.now() - timedelta(days=7)
    activites = Journal.objects.filter(
        date_action__gte=date_limite,
        entite__in=['etudiant', 'paiement']
    ).order_by('-date_action')[:10]
    
    # Étudiants sans paiement ce mois
    etudiants_tous = Etudiant.objects.filter(is_active=True).values('id')
    etudiants_avec_paiement = Paiement.objects.filter(
        date_paiement__month=datetime.now().month,
        date_paiement__year=datetime.now().year
    ).values('etudiant_id').distinct()
    
    etudiants_sans_paiement = Etudiant.objects.filter(
        id__in=etudiants_tous
    ).exclude(
        id__in=etudiants_avec_paiement
    ).count()
    
    # Derniers paiements enregistrés
    derniers_paiements = Paiement.objects.order_by('-date_enregistrement')[:10]
    
    # Derniers étudiants inscrits
    derniers_etudiants = Etudiant.objects.order_by('-date_inscription')[:5]
    
    context = {
        'role': 'collaborateur',
        'total_etudiants': total_etudiants,
        'nouveaux_etudiants': nouveaux_etudiants,
        'total_paiements_mois': total_paiements_mois,
        'montant_paiements_mois': round(montant_paiements_mois, 2),
        'total_classes': total_classes,
        'etudiants_sans_paiement': etudiants_sans_paiement,
        'activites': activites,
        'derniers_paiements': derniers_paiements,
        'derniers_etudiants': derniers_etudiants,
    }
    
    return render(request, 'gestion/dashboard_collaborateur.html', context)


# ========== FONCTIONS UTILITAIRES ==========

def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ========== ERREURS ==========

def page_not_found(request, exception):
    """Page 404"""
    return render(request, 'gestion/404.html', status=404)


def server_error(request):
    """Page 500"""
    return render(request, 'gestion/500.html', status=500)