from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# ========== ANNÉE SCOLAIRE ==========
class AnneeScolaire(models.Model):
    annee = models.CharField(max_length=10, unique=True)  # ex: "2024-2025"
    date_debut = models.DateField()
    date_fin = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Année Scolaire"
        verbose_name_plural = "Années Scolaires"
    
    def __str__(self):
        return f"Année {self.annee}"


# ========== MATIÈRE ==========
class Matiere(models.Model):
    NIVEAU_CHOICES = [
        ('primaire', 'Primaire'),
        ('secondaire', 'Secondaire'),
    ]
    
    nom = models.CharField(max_length=100)
    coefficient = models.FloatField(default=1.0)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    
    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
    
    def __str__(self):
        return f"{self.nom} (Coef: {self.coefficient})"


# ========== ENSEIGNANT ==========
class Enseignant(models.Model):
    SEXE_CHOICES = [
        ('M', 'Homme'),
        ('F', 'Femme'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    adresse = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='enseignants/photos/', blank=True, null=True)
    photo_identite = models.ImageField(upload_to='enseignants/identites/', blank=True, null=True)
    date_embauche = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ========== CLASSE ==========
class Classe(models.Model):
    NIVEAU_CHOICES = [
        ('primaire', 'Primaire'),
        ('secondaire', 'Secondaire'),
    ]
    
    nom = models.CharField(max_length=50)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    effectif = models.IntegerField(default=0)
    enseignant_principal = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    matieres = models.ManyToManyField(Matiere, through='AssignationClasseMatiereEnseignant')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        unique_together = ('nom', 'annee_scolaire')
    
    def __str__(self):
        return f"Classe {self.nom} ({self.annee_scolaire})"


# ========== ASSIGNATION CLASSE-MATIÈRE-ENSEIGNANT ==========
class AssignationClasseMatiereEnseignant(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    date_assignation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Assignation Classe-Matière-Enseignant"
        verbose_name_plural = "Assignations Classe-Matière-Enseignant"
        unique_together = ('classe', 'matiere', 'enseignant')
    
    def __str__(self):
        return f"{self.classe} - {self.matiere} - {self.enseignant}"


# ========== PARENT ==========
class Parent(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    contact = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ========== ÉTUDIANT ==========
class Etudiant(models.Model):
    SEXE_CHOICES = [
        ('M', 'Homme'),
        ('F', 'Femme'),
    ]
    
    STATUT_CHOICES = [
        ('nouvel_inscrit', 'Nouvel inscrit'),
        ('reinscrit', 'Réinscrit'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='etudiants/photos/', blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='nouvel_inscrit')
    date_inscription = models.DateField(auto_now_add=True)
    parents = models.ManyToManyField(Parent, through='RelationEtudiantParent')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ========== RELATION ÉTUDIANT-PARENT ==========
class RelationEtudiantParent(models.Model):
    RELATION_CHOICES = [
        ('pere', 'Père'),
        ('mere', 'Mère'),
        ('tuteur', 'Tuteur'),
        ('autre', 'Autre'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES)
    
    class Meta:
        verbose_name = "Relation Étudiant-Parent"
        verbose_name_plural = "Relations Étudiant-Parent"
        unique_together = ('etudiant', 'parent')
    
    def __str__(self):
        return f"{self.etudiant} - {self.parent} ({self.relation})"


# ========== ASSIGNATION ÉTUDIANT-CLASSE ==========
class AssignationEtudiantClasse(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    date_assignation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Assignation Étudiant-Classe"
        verbose_name_plural = "Assignations Étudiant-Classe"
        unique_together = ('etudiant', 'classe', 'annee_scolaire')
    
    def __str__(self):
        return f"{self.etudiant} - {self.classe}"


# ========== NOTE/ÉVALUATION ==========
class Note(models.Model):
    TYPE_CHOICES = [
        ('interrogation', 'Interrogation'),
        ('devoir', 'Devoir'),
        ('examen', 'Examen'),
    ]
    
    TRIMESTRE_CHOICES = [
        (1, '1er Trimestre'),
        (2, '2e Trimestre'),
        (3, '3e Trimestre'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    valeur = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    sur = models.FloatField(default=20)
    date = models.DateField()
    trimestre = models.IntegerField(choices=TRIMESTRE_CHOICES)
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
    
    def __str__(self):
        return f"{self.etudiant} - {self.matiere}: {self.valeur}/{self.sur}"


# ========== BULLETIN ==========
class Bulletin(models.Model):
    TRIMESTRE_CHOICES = [
        (1, '1er Trimestre'),
        (2, '2e Trimestre'),
        (3, '3e Trimestre'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    trimestre = models.IntegerField(choices=TRIMESTRE_CHOICES)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    date_generation = models.DateTimeField(auto_now_add=True)
    fichier_pdf = models.FileField(upload_to='bulletins/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Bulletin"
        verbose_name_plural = "Bulletins"
        unique_together = ('etudiant', 'classe', 'trimestre', 'annee_scolaire')
    
    def __str__(self):
        return f"Bulletin {self.etudiant} - {self.trimestre} ({self.annee_scolaire})"


# ========== PAIEMENT ==========
class Paiement(models.Model):
    TYPE_CHOICES = [
        ('inscription', 'Inscription'),
        ('scolarite', 'Scolarité'),
        ('frais', 'Frais'),
        ('autre', 'Autre'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    recu_numero = models.CharField(max_length=50, unique=True)
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
    
    def __str__(self):
        return f"{self.etudiant} - {self.montant}€ ({self.type})"


# ========== CRÉDIT ==========
class Credit(models.Model):
    solde = models.IntegerField(default=0)
    date_activation = models.DateField(auto_now_add=True)
    date_expiration = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Crédit"
        verbose_name_plural = "Crédits"
    
    def __str__(self):
        return f"Crédit: {self.solde} (Exp: {self.date_expiration})"


# ========== EMPLOI DU TEMPS ==========
class EmploiDuTemps(models.Model):
    JOUR_CHOICES = [
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'),
    ]
    
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    jour = models.CharField(max_length=20, choices=JOUR_CHOICES)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    salle = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = "Emploi du Temps"
        verbose_name_plural = "Emplois du Temps"
    
    def __str__(self):
        return f"{self.classe} - {self.jour} {self.heure_debut}-{self.heure_fin} ({self.matiere})"


# ========== TYPE DE DÉPART ==========
class TypeDepart(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Type de Départ"
        verbose_name_plural = "Types de Départ"
    
    def __str__(self):
        return self.nom


# ========== HISTORIQUE DE DÉPART ==========
class Depart(models.Model):
    etudiant = models.OneToOneField(Etudiant, on_delete=models.CASCADE, null=True, blank=True)
    enseignant = models.OneToOneField(Enseignant, on_delete=models.CASCADE, null=True, blank=True)
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    type_depart = models.ForeignKey(TypeDepart, on_delete=models.SET_NULL, null=True)
    date_depart = models.DateField()
    raison_detail = models.TextField(blank=True, null=True)
    document_justificatif = models.FileField(upload_to='departures/', blank=True, null=True)
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='departures_enregistrees')
    
    class Meta:
        verbose_name = "Départ"
        verbose_name_plural = "Départs"
    
    def __str__(self):
        if self.etudiant:
            return f"Départ Étudiant: {self.etudiant} ({self.type_depart})"
        elif self.enseignant:
            return f"Départ Enseignant: {self.enseignant} ({self.type_depart})"
        elif self.utilisateur:
            return f"Départ Admin: {self.utilisateur} ({self.type_depart})"
        return f"Départ ({self.type_depart})"


# ========== JOURNAL D'ACTIVITÉ (LOGS) ==========
class Journal(models.Model):
    ACTION_CHOICES = [
        ('create', 'Créé'),
        ('update', 'Modifié'),
        ('delete', 'Supprimé'),
        ('login', 'Connecté'),
        ('logout', 'Déconnecté'),
        ('autre', 'Autre'),
    ]
    
    ENTITE_CHOICES = [
        ('etudiant', 'Étudiant'),
        ('enseignant', 'Enseignant'),
        ('classe', 'Classe'),
        ('note', 'Note'),
        ('paiement', 'Paiement'),
        ('bulletin', 'Bulletin'),
        ('utilisateur', 'Utilisateur'),
        ('autre', 'Autre'),
    ]
    
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entite = models.CharField(max_length=50, choices=ENTITE_CHOICES)
    entite_id = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date_action = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Journal"
        verbose_name_plural = "Journaux"
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.utilisateur} - {self.action} {self.entite} ({self.date_action})"