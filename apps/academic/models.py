# Modèles de la structure académique
# Contient : AnneeAcademique, Faculte, Departement, Filiere, Matiere

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# MODÈLE ANNEE ACADEMIQUE
class AnneeAcademique(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: 2024-2025"
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début",
        help_text="Premier jour de l'année académique"
    )
    
    date_fin = models.DateField(
        verbose_name="Date de fin",
        help_text="Dernier jour de l'année académique"
    )
    
    is_active = models.BooleanField(
        default=False,
        verbose_name="Active",
        help_text="Une seule année peut être active à la fois"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_annees_academiques'
        verbose_name = 'Année Académique'
        verbose_name_plural = 'Années Académiques'
        ordering = ['-date_debut']
    
    def __str__(self):
        return self.code
    
    def activate(self):
        # Désactiver toutes les autres années
        AnneeAcademique.objects.exclude(id=self.id).update(is_active=False)
        # Activer celle-ci
        self.is_active = True
        self.save()
    
    def close(self):
        # Fermer (désactiver) cette année académique.
        self.is_active = False
        self.save()

# MODÈLE FACULTE
class Faculte(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: FST, FDSP, FM"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Faculté des Sciences et Techniques"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    doyen = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Doyen",
        help_text="Nom du doyen de la faculté"
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name="Email"
    )
    
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_facultes'
        verbose_name = 'Faculté'
        verbose_name_plural = 'Facultés'
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def get_departements_count(self):
        # Nombre de départements dans cette faculté.
        return self.departements.count()
    
    def get_etudiants_count(self):
        # Nombre d'étudiants dans cette faculté.
        # Sera implémenté au Sprint 3
        return 0

# MODÈLE DEPARTEMENT
class Departement(models.Model):
    
    # RELATION: Departement → Faculte (ManyToOne)
    faculte = models.ForeignKey(
        Faculte,
        on_delete=models.CASCADE,
        related_name='departements',
        verbose_name="Faculté"
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: INFO, MATH, PHYS"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Département d'Informatique"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    chef_departement = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Chef de département"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_departements'
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['faculte', 'nom']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def get_filieres_count(self):
        # Nombre de filières dans ce département.
        return self.filieres.count()

# MODÈLE FILIERE
class Filiere(models.Model):
    CYCLE_CHOICES = [
        ('LICENCE', 'Licence'),
        ('MASTER', 'Master'),
        ('DOCTORAT', 'Doctorat'),
        ('DUT', 'DUT'),
        ('BTS', 'BTS'),
    ]
    
    # RELATION: Filiere → Departement (ManyToOne)
    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        related_name='filieres',
        verbose_name="Département"
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: L3-INFO, M2-MATH"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Licence 3 Informatique"
    )
    
    cycle = models.CharField(
        max_length=20,
        choices=CYCLE_CHOICES,
        verbose_name="Cycle"
    )
    
    duree_annees = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        verbose_name="Durée (années)",
        help_text="Nombre d'années d'études"
    )
    
    frais_inscription = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Frais d'inscription",
        help_text="Montant en FCFA"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_filieres'
        verbose_name = 'Filière'
        verbose_name_plural = 'Filières'
        ordering = ['departement', 'cycle', 'nom']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def get_matieres_count(self):
        # Nombre de matières dans cette filière.
        return self.matieres.count()

# MODÈLE MATIERE
class Matiere(models.Model):
    
    SEMESTRE_CHOICES = [
        (1, 'Semestre 1'),
        (2, 'Semestre 2'),
    ]
    
    # RELATION: Matiere ↔ Filiere (ManyToMany)
    # Une matière peut être enseignée dans plusieurs filières
    filieres = models.ManyToManyField(
        Filiere,
        related_name='matieres',
        verbose_name="Filières"
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: INFO301, MATH205"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Programmation Orientée Objet"
    )
    
    coefficient = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Coefficient",
        help_text="Poids de la matière dans la moyenne"
    )
    
    credits = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        verbose_name="Crédits ECTS",
        help_text="Nombre de crédits européens"
    )
    
    volume_horaire_cm = models.PositiveIntegerField(
        default=0,
        verbose_name="Volume horaire CM",
        help_text="Cours Magistraux (heures)"
    )
    
    volume_horaire_td = models.PositiveIntegerField(
        default=0,
        verbose_name="Volume horaire TD",
        help_text="Travaux Dirigés (heures)"
    )
    
    volume_horaire_tp = models.PositiveIntegerField(
        default=0,
        verbose_name="Volume horaire TP",
        help_text="Travaux Pratiques (heures)"
    )
    
    semestre = models.IntegerField(
        choices=SEMESTRE_CHOICES,
        default=1,
        verbose_name="Semestre"
    )
    
    is_optionnelle = models.BooleanField(
        default=False,
        verbose_name="Optionnelle",
        help_text="La matière est-elle optionnelle ?"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_matieres'
        verbose_name = 'Matière'
        verbose_name_plural = 'Matières'
        ordering = ['semestre', 'nom']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def get_volume_horaire_total(self):
        # Volume horaire total.
        return self.volume_horaire_cm + self.volume_horaire_td + self.volume_horaire_tp
