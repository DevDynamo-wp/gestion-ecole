"""
Utilitaires pour SchoolPro
Fonctions de calcul, validation et traitement des données
"""

from django.db.models import Avg, Sum, Count
from django.utils import timezone
from datetime import date, timedelta
import uuid
from .models import Note, Etudiant, Classe, Paiement, Bulletin


# ========== CALCULS DE MOYENNES ==========

def calculer_moyenne_etudiant(etudiant_id, matiere_id=None, trimestre=None, annee_scolaire=None):
    """
    Calcule la moyenne d'un étudiant
    Args:
        etudiant_id: ID de l'étudiant
        matiere_id: ID de la matière (optionnel)
        trimestre: Numéro du trimestre (optionnel)
        annee_scolaire: Année scolaire (optionnel)
    Returns:
        dict: Moyenne et détails
    """
    try:
        # Base queryset
        notes = Note.objects.filter(etudiant_id=etudiant_id)
        
        # Filtres optionnels
        if matiere_id:
            notes = notes.filter(matiere_id=matiere_id)
        if trimestre:
            notes = notes.filter(trimestre=trimestre)
        if annee_scolaire:
            notes = notes.filter(etudiant__assignationetudiantclasse__annee_scolaire=annee_scolaire)
        
        if not notes.exists():
            return {
                'moyenne': 0,
                'total_notes': 0,
                'coefficient_total': 0,
                'details': []
            }
        
        # Calcul par matière
        matieres = {}
        for note in notes:
            matiere = note.matiere
            if matiere.id not in matieres:
                matieres[matiere.id] = {
                    'nom': matiere.nom,
                    'coefficient': matiere.coefficient,
                    'notes': [],
                    'total_sur': 0
                }
            
            # Convertir la note sur 20
            note_sur_20 = (note.valeur / note.sur) * 20
            matieres[matiere.id]['notes'].append(note_sur_20)
            matieres[matiere.id]['total_sur'] += note.sur
        
        # Calcul des moyennes par matière
        details = []
        somme_ponderee = 0
        coefficient_total = 0
        
        for matiere_id, data in matieres.items():
            if data['notes']:
                moyenne_matiere = sum(data['notes']) / len(data['notes'])
                details.append({
                    'matiere': data['nom'],
                    'moyenne': round(moyenne_matiere, 2),
                    'coefficient': data['coefficient'],
                    'nb_notes': len(data['notes']),
                    'notes': [round(n, 2) for n in data['notes']]
                })
                
                somme_ponderee += moyenne_matiere * data['coefficient']
                coefficient_total += data['coefficient']
        
        # Moyenne générale
        moyenne_generale = somme_ponderee / coefficient_total if coefficient_total > 0 else 0
        
        return {
            'moyenne': round(moyenne_generale, 2),
            'total_notes': len(notes),
            'coefficient_total': coefficient_total,
            'details': details
        }
    
    except Exception as e:
        return {
            'moyenne': 0,
            'total_notes': 0,
            'coefficient_total': 0,
            'details': [],
            'error': str(e)
        }


def calculer_moyenne_classe(classe_id, matiere_id=None, trimestre=None):
    """
    Calcule la moyenne d'une classe
    Args:
        classe_id: ID de la classe
        matiere_id: ID de la matière (optionnel)
        trimestre: Numéro du trimestre (optionnel)
    Returns:
        dict: Moyenne de la classe et statistiques
    """
    try:
        # Récupérer les étudiants de la classe
        etudiants = Etudiant.objects.filter(
            assignationetudiantclasse__classe_id=classe_id,
            is_active=True
        )
        
        if not etudiants.exists():
            return {
                'moyenne_classe': 0,
                'nb_etudiants': 0,
                'moyennes_etudiants': []
            }
        
        moyennes_etudiants = []
        somme_moyennes = 0
        nb_etudiants_avec_notes = 0
        
        for etudiant in etudiants:
            resultat = calculer_moyenne_etudiant(
                etudiant.id, 
                matiere_id=matiere_id, 
                trimestre=trimestre
            )
            
            if resultat['moyenne'] > 0:
                moyennes_etudiants.append({
                    'etudiant_id': etudiant.id,
                    'nom': f"{etudiant.first_name} {etudiant.last_name}",
                    'moyenne': resultat['moyenne'],
                    'nb_notes': resultat['total_notes']
                })
                
                somme_moyennes += resultat['moyenne']
                nb_etudiants_avec_notes += 1
        
        # Moyenne de la classe
        moyenne_classe = somme_moyennes / nb_etudiants_avec_notes if nb_etudiants_avec_notes > 0 else 0
        
        return {
            'moyenne_classe': round(moyenne_classe, 2),
            'nb_etudiants': len(etudiants),
            'nb_etudiants_avec_notes': nb_etudiants_avec_notes,
            'moyennes_etudiants': moyennes_etudiants
        }
    
    except Exception as e:
        return {
            'moyenne_classe': 0,
            'nb_etudiants': 0,
            'nb_etudiants_avec_notes': 0,
            'moyennes_etudiants': [],
            'error': str(e)
        }


def generer_bulletin_etudiant(etudiant_id, trimestre, annee_scolaire):
    """
    Génère un bulletin pour un étudiant
    Args:
        etudiant_id: ID de l'étudiant
        trimestre: Numéro du trimestre
        annee_scolaire: Année scolaire
    Returns:
        dict: Données du bulletin
    """
    try:
        etudiant = Etudiant.objects.get(id=etudiant_id, is_active=True)
        
        # Récupérer la classe de l'étudiant
        assignation = etudiant.assignationetudiantclasse_set.filter(
            annee_scolaire=annee_scolaire
        ).first()
        
        if not assignation:
            return {'error': 'Étudiant non assigné à une classe'}
        
        classe = assignation.classe
        
        # Calculer les moyennes par matière
        matieres = classe.matiere.all()
        details_bulletin = []
        
        for matiere in matieres:
            resultat = calculer_moyenne_etudiant(
                etudiant_id,
                matiere_id=matiere.id,
                trimestre=trimestre
            )
            
            details_bulletin.append({
                'matiere': matiere.nom,
                'coefficient': matiere.coefficient,
                'moyenne': resultat['moyenne'],
                'nb_notes': resultat['total_notes'],
                'appreciation': get_appreciation(resultat['moyenne'])
            })
        
        # Moyenne générale
        resultat_general = calculer_moyenne_etudiant(
            etudiant_id,
            trimestre=trimestre
        )
        
        # Statistiques de la classe
        stats_classe = calculer_moyenne_classe(classe.id, trimestre=trimestre)
        
        # Rang dans la classe (simulation simple)
        rang = calculer_rang_etudiant(etudiant_id, classe.id, trimestre)
        
        return {
            'etudiant': {
                'id': etudiant.id,
                'nom': f"{etudiant.first_name} {etudiant.last_name}",
                'date_naissance': etudiant.date_naissance,
                'sexe': etudiant.get_sexe_display()
            },
            'classe': {
                'nom': classe.nom,
                'niveau': classe.get_niveau_display(),
                'enseignant_principal': f"{classe.enseignant_principal.first_name} {classe.enseignant_principal.last_name}" if classe.enseignant_principal else None
            },
            'trimestre': trimestre,
            'annee_scolaire': annee_scolaire.annee,
            'moyenne_generale': resultat_general['moyenne'],
            'rang_classe': rang,
            'moyenne_classe': stats_classe['moyenne_classe'],
            'details_matiere': details_bulletin,
            'appreciation_generale': get_appreciation(resultat_general['moyenne']),
            'date_generation': timezone.now()
        }
    
    except Etudiant.DoesNotExist:
        return {'error': 'Étudiant non trouvé'}
    except Exception as e:
        return {'error': str(e)}


# ========== FONCTIONS UTILITAIRES ==========

def get_appreciation(moyenne):
    """Retourne une appréciation basée sur la moyenne"""
    if moyenne >= 16:
        return "Excellent"
    elif moyenne >= 14:
        return "Très bien"
    elif moyenne >= 12:
        return "Bien"
    elif moyenne >= 10:
        return "Assez bien"
    elif moyenne >= 8:
        return "Passable"
    elif moyenne >= 6:
        return "Insuffisant"
    else:
        return "Très insuffisant"


def calculer_rang_etudiant(etudiant_id, classe_id, trimestre):
    """Calcule le rang d'un étudiant dans sa classe"""
    try:
        # Récupérer tous les étudiants de la classe avec leurs moyennes
        etudiants = Etudiant.objects.filter(
            assignationetudiantclasse__classe_id=classe_id,
            is_active=True
        )
        
        moyennes = []
        for etudiant in etudiants:
            resultat = calculer_moyenne_etudiant(etudiant.id, trimestre=trimestre)
            if resultat['moyenne'] > 0:
                moyennes.append({
                    'etudiant_id': etudiant.id,
                    'moyenne': resultat['moyenne']
                })
        
        # Trier par moyenne décroissante
        moyennes.sort(key=lambda x: x['moyenne'], reverse=True)
        
        # Trouver le rang
        for i, etudiant_data in enumerate(moyennes):
            if etudiant_data['etudiant_id'] == etudiant_id:
                return i + 1
        
        return len(moyennes) + 1
    
    except Exception:
        return 0


def generer_numero_recu():
    """Génère un numéro de reçu unique"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"REC-{timestamp}-{unique_id}"


def calculer_statistiques_paiements(etudiant_id=None, date_debut=None, date_fin=None):
    """Calcule les statistiques des paiements"""
    try:
        paiements = Paiement.objects.all()
        
        # Filtres
        if etudiant_id:
            paiements = paiements.filter(etudiant_id=etudiant_id)
        if date_debut:
            paiements = paiements.filter(date_paiement__gte=date_debut)
        if date_fin:
            paiements = paiements.filter(date_paiement__lte=date_fin)
        
        # Calculs
        stats = paiements.aggregate(
            total_paiements=Count('id'),
            montant_total=Sum('montant'),
            montant_moyen=Avg('montant')
        )
        
        # Par type de paiement
        paiements_par_type = {}
        for type_choice in Paiement.TYPE_CHOICES:
            type_paiements = paiements.filter(type=type_choice[0])
            paiements_par_type[type_choice[1]] = {
                'count': type_paiements.count(),
                'montant': float(type_paiements.aggregate(Sum('montant'))['montant__sum'] or 0)
            }
        
        return {
            'total_paiements': stats['total_paiements'] or 0,
            'montant_total': float(stats['montant_total'] or 0),
            'montant_moyen': float(stats['montant_moyen'] or 0),
            'paiements_par_type': paiements_par_type
        }
    
    except Exception as e:
        return {
            'total_paiements': 0,
            'montant_total': 0,
            'montant_moyen': 0,
            'paiements_par_type': {},
            'error': str(e)
        }


def valider_note(valeur, sur=20):
    """Valide une note"""
    if valeur < 0 or valeur > sur:
        return False, f"La note doit être comprise entre 0 et {sur}"
    
    # Vérifier que la note est un multiple de 0.25
    if valeur % 0.25 != 0:
        return False, "La note doit être un multiple de 0.25"
    
    return True, "Note valide"


def calculer_age(date_naissance):
    """Calcule l'âge à partir de la date de naissance"""
    today = date.today()
    return today.year - date_naissance.year - ((today.month, today.day) < (date_naissance.month, date_naissance.day))


def formater_montant(montant):
    """Formate un montant en devise locale"""
    return f"{montant:,.2f} FCFA"


def est_trimestre_valide(trimestre):
    """Vérifie si le trimestre est valide"""
    return trimestre in [1, 2, 3]


def get_trimestre_actuel():
    """Retourne le trimestre actuel basé sur la date"""
    mois_actuel = timezone.now().month
    
    if mois_actuel in [9, 10, 11, 12]:
        return 1  # Premier trimestre
    elif mois_actuel in [1, 2, 3, 4]:
        return 2  # Deuxième trimestre
    elif mois_actuel in [5, 6, 7, 8]:
        return 3  # Troisième trimestre
    
    return 1  # Par défaut


def calculer_progression_etudiant(etudiant_id, matiere_id=None):
    """Calcule la progression d'un étudiant sur les trimestres"""
    try:
        etudiant = Etudiant.objects.get(id=etudiant_id, is_active=True)
        
        progression = []
        for trimestre in [1, 2, 3]:
            resultat = calculer_moyenne_etudiant(
                etudiant_id,
                matiere_id=matiere_id,
                trimestre=trimestre
            )
            
            progression.append({
                'trimestre': trimestre,
                'moyenne': resultat['moyenne'],
                'nb_notes': resultat['total_notes']
            })
        
        # Calculer la tendance
        moyennes = [p['moyenne'] for p in progression if p['moyenne'] > 0]
        if len(moyennes) >= 2:
            if moyennes[-1] > moyennes[-2]:
                tendance = "En progression"
            elif moyennes[-1] < moyennes[-2]:
                tendance = "En régression"
            else:
                tendance = "Stable"
        else:
            tendance = "Insufficient de données"
        
        return {
            'progression': progression,
            'tendance': tendance,
            'moyenne_annuelle': sum(moyennes) / len(moyennes) if moyennes else 0
        }
    
    except Exception as e:
        return {
            'progression': [],
            'tendance': "Erreur",
            'moyenne_annuelle': 0,
            'error': str(e)
        }


def generer_rapport_classe(classe_id, trimestre=None):
    """Génère un rapport complet pour une classe"""
    try:
        classe = Classe.objects.get(id=classe_id)
        
        # Statistiques de base
        etudiants = Etudiant.objects.filter(
            assignationetudiantclasse__classe=classe,
            is_active=True
        )
        
        # Calculs des moyennes
        stats_classe = calculer_moyenne_classe(classe_id, trimestre=trimestre)
        
        # Répartition par niveau
        repartition_notes = {
            'excellent': 0,  # >= 16
            'tres_bien': 0,  # >= 14
            'bien': 0,       # >= 12
            'assez_bien': 0, # >= 10
            'passable': 0,   # >= 8
            'insuffisant': 0 # < 8
        }
        
        for etudiant_data in stats_classe['moyennes_etudiants']:
            moyenne = etudiant_data['moyenne']
            if moyenne >= 16:
                repartition_notes['excellent'] += 1
            elif moyenne >= 14:
                repartition_notes['tres_bien'] += 1
            elif moyenne >= 12:
                repartition_notes['bien'] += 1
            elif moyenne >= 10:
                repartition_notes['assez_bien'] += 1
            elif moyenne >= 8:
                repartition_notes['passable'] += 1
            else:
                repartition_notes['insuffisant'] += 1
        
        return {
            'classe': {
                'nom': classe.nom,
                'niveau': classe.get_niveau_display(),
                'effectif': len(etudiants)
            },
            'statistiques': stats_classe,
            'repartition_notes': repartition_notes,
            'trimestre': trimestre or get_trimestre_actuel()
        }
    
    except Exception as e:
        return {
            'error': str(e)
        }
