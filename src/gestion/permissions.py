"""
Système de permissions pour SchoolPro
Gère les droits d'accès selon les rôles
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Etudiant, Enseignant, Classe, Note, Paiement, Bulletin


# ========== DÉFINITION DES RÔLES ==========

ROLES = {
    'admin': 'Administrateur',
    'professeur': 'Professeur',
    'collaborateur': 'Collaborateur/Secrétaire',
}


# ========== PERMISSIONS PAR RÔLE ==========

ROLE_PERMISSIONS = {
    'admin': {
        'etudiant': ['add', 'change', 'delete', 'view'],
        'enseignant': ['add', 'change', 'delete', 'view'],
        'classe': ['add', 'change', 'delete', 'view'],
        'note': ['add', 'change', 'delete', 'view'],
        'paiement': ['add', 'change', 'delete', 'view'],
        'bulletin': ['add', 'change', 'delete', 'view'],
        'user': ['add', 'change', 'delete', 'view'],
    },
    'professeur': {
        'etudiant': ['view'],
        'classe': ['view'],
        'note': ['add', 'change', 'view'],
        'bulletin': ['add', 'view'],
    },
    'collaborateur': {
        'etudiant': ['add', 'change', 'view'],
        'paiement': ['add', 'change', 'view'],
        'classe': ['view'],
    },
}


# ========== CRÉATION DES GROUPES ==========

def create_groups():
    """
    Crée les groupes de base et leur assigne les permissions
    À exécuter une seule fois lors de l'initialisation
    """
    
    for role_name, role_label in ROLES.items():
        # Créer ou récupérer le groupe
        group, created = Group.objects.get_or_create(name=role_name)
        
        if created:
            print(f"✅ Groupe '{role_label}' créé")
        
        # Assigner les permissions
        if role_name in ROLE_PERMISSIONS:
            permissions = ROLE_PERMISSIONS[role_name]
            
            for model_name, actions in permissions.items():
                # Mapper les noms de modèles
                model_map = {
                    'etudiant': Etudiant,
                    'enseignant': Enseignant,
                    'classe': Classe,
                    'note': Note,
                    'paiement': Paiement,
                    'bulletin': Bulletin,
                }
                
                if model_name in model_map:
                    model = model_map[model_name]
                    content_type = ContentType.objects.get_for_model(model)
                    
                    for action in actions:
                        codename = f"{action}_{model._meta.model_name}"
                        try:
                            perm = Permission.objects.get(
                                codename=codename,
                                content_type=content_type
                            )
                            group.permissions.add(perm)
                        except Permission.DoesNotExist:
                            print(f"⚠️ Permission {codename} introuvable")
    
    print("✅ Groupes et permissions configurés")


# ========== VÉRIFICATION DES RÔLES ==========

def get_user_role(user):
    """
    Retourne le rôle d'un utilisateur
    """
    if user.is_superuser or user.is_staff:
        return 'admin'
    
    try:
        Enseignant.objects.get(user=user)
        return 'professeur'
    except Enseignant.DoesNotExist:
        pass
    
    # Par défaut : collaborateur
    return 'collaborateur'


def is_admin(user):
    """Vérifie si l'utilisateur est admin"""
    return user.is_superuser or user.is_staff or user.groups.filter(name='admin').exists()


def is_professeur(user):
    """Vérifie si l'utilisateur est professeur"""
    try:
        Enseignant.objects.get(user=user)
        return True
    except Enseignant.DoesNotExist:
        return False


def is_collaborateur(user):
    """Vérifie si l'utilisateur est collaborateur"""
    return user.groups.filter(name='collaborateur').exists()


# ========== DÉCORATEURS DE PERMISSIONS ==========

def role_required(*roles):
    """
    Décorateur pour restreindre l'accès à certains rôles
    
    Usage:
        @role_required('admin', 'professeur')
        def ma_vue(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('gestion:login')
            
            user_role = get_user_role(request.user)
            
            if user_role not in roles:
                messages.error(request, "Vous n'avez pas accès à cette page.")
                return redirect('gestion:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux admins uniquement
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('gestion:login')
        
        if not is_admin(request.user):
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('gestion:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def professeur_required(view_func):
    """
    Décorateur pour restreindre l'accès aux professeurs uniquement
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('gestion:login')
        
        if not is_professeur(request.user):
            messages.error(request, "Accès réservé aux professeurs.")
            return redirect('gestion:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def collaborateur_required(view_func):
    """
    Décorateur pour restreindre l'accès aux collaborateurs uniquement
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('gestion:login')
        
        if not is_collaborateur(request.user):
            messages.error(request, "Accès réservé aux collaborateurs.")
            return redirect('gestion:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ========== VÉRIFICATION DE PERMISSIONS SPÉCIFIQUES ==========

def user_can_add(user, model_name):
    """Vérifie si l'utilisateur peut ajouter un objet"""
    role = get_user_role(user)
    return model_name in ROLE_PERMISSIONS.get(role, {}) and \
           'add' in ROLE_PERMISSIONS[role][model_name]


def user_can_change(user, model_name):
    """Vérifie si l'utilisateur peut modifier un objet"""
    role = get_user_role(user)
    return model_name in ROLE_PERMISSIONS.get(role, {}) and \
           'change' in ROLE_PERMISSIONS[role][model_name]


def user_can_delete(user, model_name):
    """Vérifie si l'utilisateur peut supprimer un objet"""
    role = get_user_role(user)
    return model_name in ROLE_PERMISSIONS.get(role, {}) and \
           'delete' in ROLE_PERMISSIONS[role][model_name]


def user_can_view(user, model_name):
    """Vérifie si l'utilisateur peut voir un objet"""
    role = get_user_role(user)
    return model_name in ROLE_PERMISSIONS.get(role, {}) and \
           'view' in ROLE_PERMISSIONS[role][model_name]


# ========== CONTEXTE POUR LES TEMPLATES ==========

def get_permissions_context(user):
    """
    Retourne un dictionnaire de permissions pour les templates
    """
    role = get_user_role(user)
    
    return {
        'user_role': role,
        'is_admin': is_admin(user),
        'is_professeur': is_professeur(user),
        'is_collaborateur': is_collaborateur(user),
        'can_add_etudiant': user_can_add(user, 'etudiant'),
        'can_change_etudiant': user_can_change(user, 'etudiant'),
        'can_delete_etudiant': user_can_delete(user, 'etudiant'),
        'can_view_etudiant': user_can_view(user, 'etudiant'),
        'can_add_note': user_can_add(user, 'note'),
        'can_change_note': user_can_change(user, 'note'),
        'can_add_paiement': user_can_add(user, 'paiement'),
        'can_change_paiement': user_can_change(user, 'paiement'),
    }