"""
Formulaires Django pour SchoolPro
Gestion des données avec validation et interface utilisateur
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Etudiant, Enseignant, Classe, Note, Paiement, Bulletin,
    Parent, Matiere, AnneeScolaire, AssignationEtudiantClasse,
    AssignationClasseMatiereEnseignant, EmploiDuTemps, Depart
)
from django.core.exceptions import ValidationError
from datetime import date


# ========== FORMULAIRES D'AUTHENTIFICATION ==========

class CustomUserCreationForm(UserCreationForm):
    """Formulaire de création d'utilisateur avec champs supplémentaires"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


# ========== FORMULAIRES POUR LES ÉTUDIANTS ==========

class EtudiantForm(forms.ModelForm):
    """Formulaire pour créer/modifier un étudiant"""
    
    class Meta:
        model = Etudiant
        fields = [
            'first_name', 'last_name', 'sexe', 'date_naissance', 
            'lieu_naissance', 'adresse', 'photo', 'statut'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_date_naissance(self):
        """Valider que l'étudiant a au moins 3 ans"""
        date_naissance = self.cleaned_data.get('date_naissance')
        if date_naissance:
            today = date.today()
            age = today.year - date_naissance.year - ((today.month, today.day) < (date_naissance.month, date_naissance.day))
            if age < 3:
                raise ValidationError("L'étudiant doit avoir au moins 3 ans.")
        return date_naissance


# ========== FORMULAIRES POUR LES ENSEIGNANTS ==========

class EnseignantForm(forms.ModelForm):
    """Formulaire pour créer/modifier un enseignant"""
    
    class Meta:
        model = Enseignant
        fields = [
            'user', 'first_name', 'last_name', 'sexe', 
            'adresse', 'photo', 'photo_identite'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_identite': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ========== FORMULAIRES POUR LES CLASSES ==========

class ClasseForm(forms.ModelForm):
    """Formulaire pour créer/modifier une classe"""
    
    class Meta:
        model = Classe
        fields = ['nom', 'niveau', 'effectif', 'enseignant_principal', 'annee_scolaire', 'matieres']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),
            'effectif': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 50}),
            'enseignant_principal': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-control'}),
            'matieres': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


# ========== FORMULAIRES POUR LES NOTES ==========

class NoteForm(forms.ModelForm):
    """Formulaire pour créer/modifier une note"""
    
    class Meta:
        model = Note
        fields = ['etudiant', 'matiere', 'type', 'valeur', 'sur', 'date', 'trimestre']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'valeur': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 20, 'step': 0.25}),
            'sur': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'trimestre': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_valeur(self):
        """Valider que la note ne dépasse pas le maximum"""
        valeur = self.cleaned_data.get('valeur')
        sur = self.cleaned_data.get('sur', 20)
        if valeur and valeur > sur:
            raise ValidationError(f"La note ({valeur}) ne peut pas être supérieure au maximum ({sur}).")
        return valeur


# ========== FORMULAIRES POUR LES PAIEMENTS ==========

class PaiementForm(forms.ModelForm):
    """Formulaire pour créer/modifier un paiement"""
    
    class Meta:
        model = Paiement
        fields = ['etudiant', 'montant', 'type', 'date_paiement']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'date_paiement': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def clean_montant(self):
        """Valider que le montant est positif"""
        montant = self.cleaned_data.get('montant')
        if montant and montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        return montant


# ========== FORMULAIRES POUR LES PARENTS ==========

class ParentForm(forms.ModelForm):
    """Formulaire pour créer/modifier un parent"""
    
    class Meta:
        model = Parent
        fields = ['first_name', 'last_name', 'contact', 'email', 'profession', 'adresse']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+237 123 456 789'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ========== FORMULAIRES POUR LES MATIÈRES ==========

class MatiereForm(forms.ModelForm):
    """Formulaire pour créer/modifier une matière"""
    
    class Meta:
        model = Matiere
        fields = ['nom', 'coefficient', 'niveau']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control', 'min': 0.5, 'max': 5, 'step': 0.5}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),
        }


# ========== FORMULAIRES POUR LES ANNÉES SCOLAIRES ==========

class AnneeScolaireForm(forms.ModelForm):
    """Formulaire pour créer/modifier une année scolaire"""
    
    class Meta:
        model = AnneeScolaire
        fields = ['annee', 'date_debut', 'date_fin', 'is_active']
        widgets = {
            'annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2024-2025'}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        """Valider que la date de fin est après la date de début"""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin and date_fin <= date_debut:
            raise ValidationError("La date de fin doit être après la date de début.")
        
        return cleaned_data


# ========== FORMULAIRES POUR LES ASSIGNATIONS ==========

class AssignationEtudiantClasseForm(forms.ModelForm):
    """Formulaire pour assigner un étudiant à une classe"""
    
    class Meta:
        model = AssignationEtudiantClasse
        fields = ['etudiant', 'classe', 'annee_scolaire']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-control'}),
        }


class AssignationClasseMatiereEnseignantForm(forms.ModelForm):
    """Formulaire pour assigner une matière et un enseignant à une classe"""
    
    class Meta:
        model = AssignationClasseMatiereEnseignant
        fields = ['classe', 'matiere', 'enseignant']
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'enseignant': forms.Select(attrs={'class': 'form-control'}),
        }


# ========== FORMULAIRES POUR L'EMPLOI DU TEMPS ==========

class EmploiDuTempsForm(forms.ModelForm):
    """Formulaire pour créer/modifier un emploi du temps"""
    
    class Meta:
        model = EmploiDuTemps
        fields = ['classe', 'jour', 'heure_debut', 'heure_fin', 'matiere', 'enseignant', 'salle']
        widgets = {
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'jour': forms.Select(attrs={'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'enseignant': forms.Select(attrs={'class': 'form-control'}),
            'salle': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """Valider que l'heure de fin est après l'heure de début"""
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        
        if heure_debut and heure_fin and heure_fin <= heure_debut:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")
        
        return cleaned_data


# ========== FORMULAIRES POUR LES DÉPARTS ==========

class DepartForm(forms.ModelForm):
    """Formulaire pour enregistrer un départ"""
    
    class Meta:
        model = Depart
        fields = ['etudiant', 'enseignant', 'utilisateur', 'type_depart', 'date_depart', 'raison_detail', 'document_justificatif']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-control'}),
            'enseignant': forms.Select(attrs={'class': 'form-control'}),
            'utilisateur': forms.Select(attrs={'class': 'form-control'}),
            'type_depart': forms.Select(attrs={'class': 'form-control'}),
            'date_depart': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'raison_detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'document_justificatif': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """Valider qu'au moins un type de personne est sélectionné"""
        cleaned_data = super().clean()
        etudiant = cleaned_data.get('etudiant')
        enseignant = cleaned_data.get('enseignant')
        utilisateur = cleaned_data.get('utilisateur')
        
        if not any([etudiant, enseignant, utilisateur]):
            raise ValidationError("Veuillez sélectionner au moins une personne (étudiant, enseignant ou utilisateur).")
        
        return cleaned_data


# ========== FORMULAIRES DE RECHERCHE ==========

class SearchForm(forms.Form):
    """Formulaire de recherche générique"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...',
            'id': 'search-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        search_placeholder = kwargs.pop('placeholder', 'Rechercher...')
        super().__init__(*args, **kwargs)
        self.fields['search'].widget.attrs['placeholder'] = search_placeholder


# ========== FORMULAIRES POUR LES FILTRES ==========

class EtudiantFilterForm(forms.Form):
    """Formulaire de filtrage pour les étudiants"""
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=False,
        empty_label="Toutes les classes",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Etudiant.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sexe = forms.ChoiceField(
        choices=[('', 'Tous')] + Etudiant.SEXE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class NoteFilterForm(forms.Form):
    """Formulaire de filtrage pour les notes"""
    matiere = forms.ModelChoiceField(
        queryset=Matiere.objects.all(),
        required=False,
        empty_label="Toutes les matières",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    trimestre = forms.ChoiceField(
        choices=[('', 'Tous les trimestres')] + Note.TRIMESTRE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    type = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Note.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

