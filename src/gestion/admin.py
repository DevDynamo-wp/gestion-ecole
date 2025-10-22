from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    AnneeScolaire, Matiere, Enseignant, Classe, AssignationClasseMatiereEnseignant,
    Parent, Etudiant, RelationEtudiantParent, AssignationEtudiantClasse,
    Note, Bulletin, Paiement, Credit, EmploiDuTemps, TypeDepart, Depart, Journal
)


# ========== ADMIN PERSONNALISÉ POUR LES UTILISATEURS ==========
@admin.register(Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'sexe', 'date_embauche', 'is_active')
    list_filter = ('sexe', 'is_active', 'date_embauche')
    search_fields = ('first_name', 'last_name', 'user__username')
    readonly_fields = ('date_embauche',)
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('user', 'first_name', 'last_name', 'sexe', 'adresse')
        }),
        ('Photos', {
            'fields': ('photo', 'photo_identite'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_active', 'date_embauche')
        }),
    )


# ========== ADMIN POUR LES ÉTUDIANTS ==========
@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'sexe', 'statut', 'date_inscription', 'is_active')
    list_filter = ('sexe', 'statut', 'is_active', 'date_inscription')
    search_fields = ('first_name', 'last_name', 'lieu_naissance')
    readonly_fields = ('date_inscription',)
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'sexe', 'date_naissance', 'lieu_naissance', 'adresse')
        }),
        ('Photo', {
            'fields': ('photo',),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('statut', 'is_active', 'date_inscription')
        }),
    )
    # filter_horizontal ne peut pas être utilisé avec des modèles intermédiaires


# ========== ADMIN POUR LES CLASSES ==========
@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau', 'effectif', 'enseignant_principal', 'annee_scolaire')
    list_filter = ('niveau', 'annee_scolaire')
    search_fields = ('nom', 'enseignant_principal__first_name', 'enseignant_principal__last_name')
    # filter_horizontal ne peut pas être utilisé avec des modèles intermédiaires


# ========== ADMIN POUR LES NOTES ==========
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'matiere', 'type', 'valeur', 'sur', 'date', 'trimestre')
    list_filter = ('type', 'trimestre', 'date', 'matiere')
    search_fields = ('etudiant__first_name', 'etudiant__last_name', 'matiere__nom')
    date_hierarchy = 'date'
    readonly_fields = ('date_enregistrement',)


# ========== ADMIN POUR LES PAIEMENTS ==========
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'montant', 'type', 'date_paiement', 'recu_numero')
    list_filter = ('type', 'date_paiement')
    search_fields = ('etudiant__first_name', 'etudiant__last_name', 'recu_numero')
    date_hierarchy = 'date_paiement'
    readonly_fields = ('recu_numero', 'date_enregistrement')


# ========== ADMIN POUR LES BULLETINS ==========
@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'classe', 'trimestre', 'annee_scolaire', 'date_generation')
    list_filter = ('trimestre', 'annee_scolaire', 'date_generation')
    search_fields = ('etudiant__first_name', 'etudiant__last_name', 'classe__nom')
    readonly_fields = ('date_generation',)


# ========== ADMIN POUR LES PARENTS ==========
@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'contact', 'email', 'profession')
    search_fields = ('first_name', 'last_name', 'email', 'contact')


# ========== ADMIN POUR LES MATIÈRES ==========
@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'coefficient', 'niveau')
    list_filter = ('niveau',)
    search_fields = ('nom',)


# ========== ADMIN POUR LES ANNÉES SCOLAIRES ==========
@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ('annee', 'date_debut', 'date_fin', 'is_active')
    list_filter = ('is_active',)


# ========== ADMIN POUR LES CRÉDITS ==========
@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ('solde', 'date_activation', 'date_expiration', 'is_active')
    list_filter = ('is_active', 'date_activation', 'date_expiration')
    readonly_fields = ('date_activation',)


# ========== ADMIN POUR L'EMPLOI DU TEMPS ==========
@admin.register(EmploiDuTemps)
class EmploiDuTempsAdmin(admin.ModelAdmin):
    list_display = ('classe', 'jour', 'heure_debut', 'heure_fin', 'matiere', 'enseignant')
    list_filter = ('jour', 'classe', 'matiere')
    search_fields = ('classe__nom', 'enseignant__first_name', 'enseignant__last_name')


# ========== ADMIN POUR LES DÉPARTS ==========
@admin.register(Depart)
class DepartAdmin(admin.ModelAdmin):
    list_display = ('get_personne', 'type_depart', 'date_depart', 'enregistre_par')
    list_filter = ('type_depart', 'date_depart')
    search_fields = ('etudiant__first_name', 'etudiant__last_name', 'enseignant__first_name', 'enseignant__last_name')
    readonly_fields = ('date_enregistrement',)
    
    def get_personne(self, obj):
        if obj.etudiant:
            return f"Étudiant: {obj.etudiant}"
        elif obj.enseignant:
            return f"Enseignant: {obj.enseignant}"
        elif obj.utilisateur:
            return f"Admin: {obj.utilisateur}"
        return "Inconnu"
    get_personne.short_description = "Personne"


# ========== ADMIN POUR LE JOURNAL ==========
@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'action', 'entite', 'description', 'date_action')
    list_filter = ('action', 'entite', 'date_action')
    search_fields = ('utilisateur__username', 'description')
    readonly_fields = ('date_action', 'adresse_ip')
    date_hierarchy = 'date_action'


# ========== ADMIN POUR LES TYPES DE DÉPART ==========
@admin.register(TypeDepart)
class TypeDepartAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description')


# ========== ADMIN POUR LES ASSIGNATIONS ==========
@admin.register(AssignationClasseMatiereEnseignant)
class AssignationClasseMatiereEnseignantAdmin(admin.ModelAdmin):
    list_display = ('classe', 'matiere', 'enseignant', 'date_assignation')
    list_filter = ('classe', 'matiere', 'date_assignation')
    search_fields = ('classe__nom', 'matiere__nom', 'enseignant__first_name')


@admin.register(AssignationEtudiantClasse)
class AssignationEtudiantClasseAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'classe', 'annee_scolaire', 'date_assignation')
    list_filter = ('classe', 'annee_scolaire', 'date_assignation')
    search_fields = ('etudiant__first_name', 'etudiant__last_name', 'classe__nom')


# ========== ADMIN POUR LES RELATIONS ÉTUDIANT-PARENT ==========
@admin.register(RelationEtudiantParent)
class RelationEtudiantParentAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'parent', 'relation')
    list_filter = ('relation',)
    search_fields = ('etudiant__first_name', 'etudiant__last_name', 'parent__first_name', 'parent__last_name')


# ========== CONFIGURATION DU SITE ADMIN ==========
admin.site.site_header = "SchoolPro - Administration"
admin.site.site_title = "SchoolPro Admin"
admin.site.index_title = "Gestion de l'École"
