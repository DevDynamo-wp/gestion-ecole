"""
API Views pour SchoolPro
Endpoints JSON pour communication interne et AJAX
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Count, Sum
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta
from .models import (
    Etudiant, Enseignant, Classe, Note, Paiement, Bulletin,
    Parent, Matiere, AnneeScolaire, AssignationEtudiantClasse,
    EmploiDuTemps, Journal, Depart
)
from .permissions import get_user_role, is_admin, is_professeur, is_collaborateur


# ========== API POUR LES ÉTUDIANTS ==========

@login_required
@require_http_methods(["GET"])
def api_etudiants(request):
    """API pour lister les étudiants avec filtres et pagination"""
    try:
        # Filtres
        search = request.GET.get('search', '')
        classe_id = request.GET.get('classe')
        statut = request.GET.get('statut')
        sexe = request.GET.get('sexe')
        page = request.GET.get('page', 1)
        
        # Base queryset
        queryset = Etudiant.objects.filter(is_active=True)
        
        # Application des filtres
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search) |
                Q(lieu_naissance__icontains=search)
            )
        
        if classe_id:
            queryset = queryset.filter(assignationetudiantclasse__classe_id=classe_id)
        
        if statut:
            queryset = queryset.filter(statut=statut)
        
        if sexe:
            queryset = queryset.filter(sexe=sexe)
        
        # Pagination
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(page)
        
        # Sérialisation
        etudiants = []
        for etudiant in page_obj:
            etudiants.append({
                'id': etudiant.id,
                'first_name': etudiant.first_name,
                'last_name': etudiant.last_name,
                'sexe': etudiant.get_sexe_display(),
                'date_naissance': etudiant.date_naissance.strftime('%d/%m/%Y'),
                'statut': etudiant.get_statut_display(),
                'date_inscription': etudiant.date_inscription.strftime('%d/%m/%Y'),
                'photo': etudiant.photo.url if etudiant.photo else None,
            })
        
        return JsonResponse({
            'success': True,
            'data': etudiants,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_etudiant_detail(request, etudiant_id):
    """API pour obtenir les détails d'un étudiant"""
    try:
        etudiant = Etudiant.objects.get(id=etudiant_id, is_active=True)
        
        # Récupérer les classes de l'étudiant
        classes = AssignationEtudiantClasse.objects.filter(etudiant=etudiant)
        classes_data = []
        for assignation in classes:
            classes_data.append({
                'classe': assignation.classe.nom,
                'annee_scolaire': assignation.annee_scolaire.annee,
                'date_assignation': assignation.date_assignation.strftime('%d/%m/%Y')
            })
        
        # Récupérer les notes récentes
        notes_recentes = Note.objects.filter(etudiant=etudiant).order_by('-date')[:10]
        notes_data = []
        for note in notes_recentes:
            notes_data.append({
                'matiere': note.matiere.nom,
                'type': note.get_type_display(),
                'valeur': note.valeur,
                'sur': note.sur,
                'date': note.date.strftime('%d/%m/%Y'),
                'trimestre': note.get_trimestre_display()
            })
        
        # Récupérer les paiements
        paiements = Paiement.objects.filter(etudiant=etudiant).order_by('-date_paiement')[:5]
        paiements_data = []
        for paiement in paiements:
            paiements_data.append({
                'montant': float(paiement.montant),
                'type': paiement.get_type_display(),
                'date_paiement': paiement.date_paiement.strftime('%d/%m/%Y'),
                'recu_numero': paiement.recu_numero
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'etudiant': {
                    'id': etudiant.id,
                    'first_name': etudiant.first_name,
                    'last_name': etudiant.last_name,
                    'sexe': etudiant.get_sexe_display(),
                    'date_naissance': etudiant.date_naissance.strftime('%d/%m/%Y'),
                    'lieu_naissance': etudiant.lieu_naissance,
                    'adresse': etudiant.adresse,
                    'statut': etudiant.get_statut_display(),
                    'date_inscription': etudiant.date_inscription.strftime('%d/%m/%Y'),
                    'photo': etudiant.photo.url if etudiant.photo else None,
                },
                'classes': classes_data,
                'notes_recentes': notes_data,
                'paiements': paiements_data
            }
        })
    
    except Etudiant.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Étudiant non trouvé'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES NOTES ==========

@login_required
@require_http_methods(["GET"])
def api_notes(request):
    """API pour lister les notes avec filtres"""
    try:
        # Filtres
        etudiant_id = request.GET.get('etudiant')
        matiere_id = request.GET.get('matiere')
        trimestre = request.GET.get('trimestre')
        type_note = request.GET.get('type')
        
        # Base queryset
        queryset = Note.objects.all()
        
        # Application des filtres
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        
        if matiere_id:
            queryset = queryset.filter(matiere_id=matiere_id)
        
        if trimestre:
            queryset = queryset.filter(trimestre=trimestre)
        
        if type_note:
            queryset = queryset.filter(type=type_note)
        
        # Sérialisation
        notes = []
        for note in queryset.order_by('-date')[:50]:  # Limite à 50 notes
            notes.append({
                'id': note.id,
                'etudiant': f"{note.etudiant.first_name} {note.etudiant.last_name}",
                'matiere': note.matiere.nom,
                'type': note.get_type_display(),
                'valeur': note.valeur,
                'sur': note.sur,
                'pourcentage': round((note.valeur / note.sur) * 100, 1),
                'date': note.date.strftime('%d/%m/%Y'),
                'trimestre': note.get_trimestre_display()
            })
        
        return JsonResponse({'success': True, 'data': notes})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_note_create(request):
    """API pour créer une nouvelle note"""
    try:
        data = json.loads(request.body)
        
        # Validation des données
        required_fields = ['etudiant_id', 'matiere_id', 'type', 'valeur', 'sur', 'date', 'trimestre']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        # Création de la note
        note = Note.objects.create(
            etudiant_id=data['etudiant_id'],
            matiere_id=data['matiere_id'],
            type=data['type'],
            valeur=data['valeur'],
            sur=data['sur'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            trimestre=data['trimestre']
        )
        
        # Enregistrer dans le journal
        Journal.objects.create(
            utilisateur=request.user,
            action='create',
            entite='note',
            entite_id=note.id,
            description=f"Note ajoutée: {note.valeur}/{note.sur} en {note.matiere.nom}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Note créée avec succès',
            'data': {
                'id': note.id,
                'etudiant': f"{note.etudiant.first_name} {note.etudiant.last_name}",
                'matiere': note.matiere.nom,
                'valeur': note.valeur,
                'sur': note.sur
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES STATISTIQUES ==========

@login_required
def api_statistiques(request):
    """API pour obtenir les statistiques générales"""
    try:
        user_role = get_user_role(request.user)
        
        # Statistiques de base
        stats = {
            'total_etudiants': Etudiant.objects.filter(is_active=True).count(),
            'total_enseignants': Enseignant.objects.filter(is_active=True).count(),
            'total_classes': Classe.objects.count(),
            'total_matiere': Matiere.objects.count(),
        }
        
        # Statistiques par genre
        stats['etudiants_par_sexe'] = {
            'masculin': Etudiant.objects.filter(is_active=True, sexe='M').count(),
            'feminin': Etudiant.objects.filter(is_active=True, sexe='F').count(),
        }
        
        # Statistiques des notes
        notes_stats = Note.objects.aggregate(
            total_notes=Count('id'),
            moyenne_generale=Avg('valeur')
        )
        stats['notes'] = notes_stats
        
        # Statistiques des paiements
        paiements_stats = Paiement.objects.aggregate(
            total_paiements=Count('id'),
            montant_total=Sum('montant')
        )
        stats['paiements'] = paiements_stats
        
        # Activités récentes
        activites = Journal.objects.order_by('-date_action')[:10]
        stats['activites_recentes'] = []
        for activite in activites:
            stats['activites_recentes'].append({
                'utilisateur': activite.utilisateur.username if activite.utilisateur else 'Système',
                'action': activite.get_action_display(),
                'entite': activite.get_entite_display(),
                'description': activite.description,
                'date': activite.date_action.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({'success': True, 'data': stats})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CLASSES ==========

@login_required
@require_http_methods(["GET"])
def api_classes(request):
    """API pour lister les classes"""
    try:
        classes = []
        for classe in Classe.objects.all():
            # Compter les étudiants
            nb_etudiants = AssignationEtudiantClasse.objects.filter(classe=classe).count()
            
            classes.append({
                'id': classe.id,
                'nom': classe.nom,
                'niveau': classe.get_niveau_display(),
                'effectif': nb_etudiants,
                'enseignant_principal': f"{classe.enseignant_principal.first_name} {classe.enseignant_principal.last_name}" if classe.enseignant_principal else None,
                'annee_scolaire': classe.annee_scolaire.annee,
                'matieres_count': classe.matiere.count()
            })
        
        return JsonResponse({'success': True, 'data': classes})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES PAIEMENTS ==========

@login_required
@require_http_methods(["GET"])
def api_paiements(request):
    """API pour lister les paiements avec filtres"""
    try:
        # Filtres
        etudiant_id = request.GET.get('etudiant')
        type_paiement = request.GET.get('type')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        # Base queryset
        queryset = Paiement.objects.all()
        
        # Application des filtres
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        
        if type_paiement:
            queryset = queryset.filter(type=type_paiement)
        
        if date_debut:
            queryset = queryset.filter(date_paiement__gte=datetime.strptime(date_debut, '%Y-%m-%d').date())
        
        if date_fin:
            queryset = queryset.filter(date_paiement__lte=datetime.strptime(date_fin, '%Y-%m-%d').date())
        
        # Sérialisation
        paiements = []
        for paiement in queryset.order_by('-date_paiement')[:100]:
            paiements.append({
                'id': paiement.id,
                'etudiant': f"{paiement.etudiant.first_name} {paiement.etudiant.last_name}",
                'montant': float(paiement.montant),
                'type': paiement.get_type_display(),
                'date_paiement': paiement.date_paiement.strftime('%d/%m/%Y'),
                'recu_numero': paiement.recu_numero,
                'date_enregistrement': paiement.date_enregistrement.strftime('%d/%m/%Y %H:%M')
            })
        
        return JsonResponse({'success': True, 'data': paiements})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES MOYENNES ==========

@login_required
@require_http_methods(["GET"])
def api_moyennes(request, etudiant_id):
    """API pour calculer les moyennes d'un étudiant"""
    try:
        etudiant = Etudiant.objects.get(id=etudiant_id, is_active=True)
        
        # Récupérer toutes les notes de l'étudiant
        notes = Note.objects.filter(etudiant=etudiant)
        
        # Calculer les moyennes par matière et trimestre
        moyennes = {}
        
        for note in notes:
            matiere_nom = note.matiere.nom
            trimestre = note.trimestre
            
            if matiere_nom not in moyennes:
                moyennes[matiere_nom] = {}
            
            if trimestre not in moyennes[matiere_nom]:
                moyennes[matiere_nom][trimestre] = {
                    'notes': [],
                    'coefficient': note.matiere.coefficient
                }
            
            # Calculer la note pondérée
            note_ponderee = (note.valeur / note.sur) * 20
            moyennes[matiere_nom][trimestre]['notes'].append(note_ponderee)
        
        # Calculer les moyennes finales
        resultats = []
        for matiere, trimestres in moyennes.items():
            for trimestre, data in trimestres.items():
                if data['notes']:
                    moyenne = sum(data['notes']) / len(data['notes'])
                    resultats.append({
                        'matiere': matiere,
                        'trimestre': f"Trimestre {trimestre}",
                        'moyenne': round(moyenne, 2),
                        'coefficient': data['coefficient'],
                        'nb_notes': len(data['notes'])
                    })
        
        # Calculer la moyenne générale
        if resultats:
            moyenne_generale = sum(r['moyenne'] * r['coefficient'] for r in resultats) / sum(r['coefficient'] for r in resultats)
        else:
            moyenne_generale = 0
        
        return JsonResponse({
            'success': True,
            'data': {
                'etudiant': f"{etudiant.first_name} {etudiant.last_name}",
                'moyennes_par_matiere': resultats,
                'moyenne_generale': round(moyenne_generale, 2)
            }
        })
    
    except Etudiant.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Étudiant non trouvé'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES RECHERCHES ==========

@login_required
@require_http_methods(["GET"])
def api_search(request):
    """API de recherche globale"""
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'success': False, 'error': 'Requête trop courte'})
        
        results = {
            'etudiants': [],
            'enseignants': [],
            'classes': [],
            'matieres': []
        }
        
        # Recherche dans les étudiants
        etudiants = Etudiant.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query),
            is_active=True
        )[:10]
        
        for etudiant in etudiants:
            results['etudiants'].append({
                'id': etudiant.id,
                'nom': f"{etudiant.first_name} {etudiant.last_name}",
                'type': 'Étudiant'
            })
        
        # Recherche dans les enseignants
        enseignants = Enseignant.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query),
            is_active=True
        )[:10]
        
        for enseignant in enseignants:
            results['enseignants'].append({
                'id': enseignant.id,
                'nom': f"{enseignant.first_name} {enseignant.last_name}",
                'type': 'Enseignant'
            })
        
        # Recherche dans les classes
        classes = Classe.objects.filter(nom__icontains=query)[:10]
        
        for classe in classes:
            results['classes'].append({
                'id': classe.id,
                'nom': classe.nom,
                'niveau': classe.get_niveau_display(),
                'type': 'Classe'
            })
        
        # Recherche dans les matières
        matieres = Matiere.objects.filter(nom__icontains=query)[:10]
        
        for matiere in matieres:
            results['matieres'].append({
                'id': matiere.id,
                'nom': matiere.nom,
                'niveau': matiere.get_niveau_display(),
                'type': 'Matière'
            })
        
        return JsonResponse({'success': True, 'data': results})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES ACTIVITÉS ==========

@login_required
@require_http_methods(["GET"])
def api_activites(request):
    """API pour lister les activités récentes"""
    try:
        # Filtres
        action = request.GET.get('action')
        entite = request.GET.get('entite')
        limit = int(request.GET.get('limit', 20))
        
        # Base queryset
        queryset = Journal.objects.all()
        
        # Application des filtres
        if action:
            queryset = queryset.filter(action=action)
        
        if entite:
            queryset = queryset.filter(entite=entite)
        
        # Sérialisation
        activites = []
        for activite in queryset.order_by('-date_action')[:limit]:
            activites.append({
                'id': activite.id,
                'utilisateur': activite.utilisateur.username if activite.utilisateur else 'Système',
                'action': activite.get_action_display(),
                'entite': activite.get_entite_display(),
                'description': activite.description,
                'date_action': activite.date_action.strftime('%d/%m/%Y %H:%M'),
                'adresse_ip': activite.adresse_ip
            })
        
        return JsonResponse({'success': True, 'data': activites})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES CRÉDITS ==========

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_credits_packages(request):
    """API pour obtenir les packages de crédits disponibles"""
    try:
        from .credits import credit_manager
        
        packages = credit_manager.get_available_packages()
        
        return JsonResponse({
            'success': True,
            'data': packages
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_credits_purchase(request):
    """API pour initier un achat de crédits"""
    try:
        from .credits import credit_manager
        
        data = json.loads(request.body)
        
        required_fields = ['package_type', 'duration_months', 'price', 'provider', 'user_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        result = credit_manager.initiate_payment(
            package_type=data['package_type'],
            duration_months=data['duration_months'],
            price=data['price'],
            provider=data['provider'],
            user_email=data['user_email']
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_credits_callback(request):
    """API callback pour les paiements de crédits"""
    try:
        from .credits import credit_manager
        
        provider = request.POST.get('provider', '')
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', '')
        
        if status == 'success':
            result = credit_manager.verify_and_activate_credit(transaction_id, provider)
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Paiement échoué'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_credits_status(request):
    """API pour vérifier le statut des crédits"""
    try:
        from .credits import credit_manager
        
        result = credit_manager.check_credit_status()
        
        # Récupération des crédits actifs
        from .models import Credit
        active_credits = Credit.objects.filter(is_active=True)
        
        credits_data = []
        for credit in active_credits:
            credits_data.append({
                'id': credit.id,
                'solde': credit.solde,
                'date_activation': credit.date_activation.strftime('%d/%m/%Y'),
                'date_expiration': credit.date_expiration.strftime('%d/%m/%Y'),
                'jours_restants': (credit.date_expiration - timezone.now()).days
            })
        
        return JsonResponse({
            'success': True,
            'credits': credits_data,
            'verification_result': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LA SAUVEGARDE CLOUD ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_cloud_backup(request):
    """API pour effectuer une sauvegarde cloud"""
    try:
        from .cloud_backup import cloud_backup_manager
        
        data = json.loads(request.body)
        provider = data.get('provider', 'both')
        backup_type = data.get('type', 'full')
        
        result = cloud_backup_manager.backup_to_cloud(
            provider=provider,
            backup_type=backup_type
        )
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_cloud_backups_list(request):
    """API pour lister les sauvegardes cloud"""
    try:
        from .cloud_backup import OneDriveBackup, GoogleDriveBackup
        
        provider = request.GET.get('provider', 'onedrive')
        
        if provider == 'onedrive':
            backup_service = OneDriveBackup()
        elif provider == 'google_drive':
            backup_service = GoogleDriveBackup()
        else:
            return JsonResponse({'success': False, 'error': 'Provider non supporté'})
        
        result = backup_service.list_backups()
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== API POUR LES BULLETINS PDF ==========

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_generate_bulletin(request):
    """API pour générer un bulletin PDF"""
    try:
        from .pdf_generator import generate_bulletin_response
        
        data = json.loads(request.body)
        
        required_fields = ['etudiant_id', 'trimestre', 'annee_scolaire_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Champ manquant: {field}'})
        
        etudiant_id = data['etudiant_id']
        trimestre = data['trimestre']
        annee_scolaire_id = data['annee_scolaire_id']
        include_chart = data.get('include_chart', True)
        
        # Récupération de l'année scolaire
        from .models import AnneeScolaire
        annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        # Génération du bulletin
        response = generate_bulletin_response(
            etudiant_id=etudiant_id,
            trimestre=trimestre,
            annee_scolaire=annee_scolaire,
            include_chart=include_chart
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_bulletin_preview(request, etudiant_id, trimestre):
    """API pour prévisualiser un bulletin"""
    try:
        from .utils import generer_bulletin_etudiant
        from .models import AnneeScolaire
        
        annee_scolaire_id = request.GET.get('annee_scolaire_id')
        if not annee_scolaire_id:
            annee_scolaire = AnneeScolaire.objects.filter(is_active=True).first()
        else:
            annee_scolaire = AnneeScolaire.objects.get(id=annee_scolaire_id)
        
        result = generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
