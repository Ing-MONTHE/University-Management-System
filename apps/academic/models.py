from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from decimal import Decimal
import re


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATORS PERSONNALISÉS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_code_faculte(value):
    """Valide le format du code faculté (2-20 caractères, lettres/chiffres/tirets)."""
    if not re.match(r'^[A-Z0-9-]{2,20}$', value):
        raise ValidationError(
            "Le code faculté doit contenir 2 à 20 caractères (lettres majuscules, chiffres, tirets).",
            code='code_faculte_invalid'
        )


def validate_code_matiere(value):
    """Valide le format du code matière (ex: INFO301, MATH205)."""
    if not re.match(r'^[A-Z]{2,10}[0-9]{2,4}$', value):
        raise ValidationError(
            "Le code matière doit être au format: LETTRES + CHIFFRES (ex: INFO301, MATH205).",
            code='code_matiere_invalid'
        )


def validate_annee_academique_code(value):
    """Valide le format du code année académique (ex: 2024-2025)."""
    if not re.match(r'^\d{4}-\d{4}$', value):
        raise ValidationError(
            "Le code année académique doit être au format YYYY-YYYY (ex: 2024-2025).",
            code='annee_academique_code_invalid'
        )
    
    # Vérifier que la deuxième année = première année + 1
    year1, year2 = map(int, value.split('-'))
    if year2 != year1 + 1:
        raise ValidationError(
            "La deuxième année doit être égale à la première année + 1.",
            code='annee_academique_years_invalid'
        )


def validate_telephone(value):
    """Valide le format du téléphone camerounais."""
    # Format: +237XXXXXXXXX ou 6XXXXXXXX ou 2XXXXXXXX
    if not re.match(r'^(\+237)?[62]\d{8}$', value.replace(' ', '')):
        raise ValidationError(
            "Format de téléphone invalide. Utilisez +237XXXXXXXXX ou 6XXXXXXXX.",
            code='telephone_invalid'
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE ANNEE ACADEMIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class AnneeAcademique(models.Model):
    """
    Année académique de l'université.
    
    Représente une année scolaire (ex: 2024-2025).
    Une seule année peut être active à la fois.
    
    Optimisations :
    - Index sur code (unique), is_active, date_debut
    - Validator pour format du code
    - Méthodes d'activation/désactivation
    - Propriétés calculées (durée, statut, etc.)
    """
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: 2024-2025",
        validators=[validate_annee_academique_code],
        db_index=True  # Index pour recherches rapides
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début",
        help_text="Premier jour de l'année académique",
        db_index=True  # Index pour filtrage par période
    )
    
    date_fin = models.DateField(
        verbose_name="Date de fin",
        help_text="Dernier jour de l'année académique",
        db_index=True
    )
    
    is_active = models.BooleanField(
        default=False,
        verbose_name="Active",
        help_text="Une seule année peut être active à la fois",
        db_index=True  # Index crucial pour filtrage
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'academic_annees_academiques'
        verbose_name = 'Année Académique'
        verbose_name_plural = 'Années Académiques'
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['is_active', '-date_debut'], name='acad_annee_active_debut_idx'),
            models.Index(fields=['code'], name='acad_annee_code_idx'),
        ]
    
    def __str__(self):
        return self.code
    
    def __repr__(self):
        return f"<AnneeAcademique {self.code} active={self.is_active}>"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def duree_jours(self):
        """Durée de l'année académique en jours."""
        return (self.date_fin - self.date_debut).days
    
    @property
    def est_en_cours(self):
        """Vérifie si l'année académique est en cours (aujourd'hui entre début et fin)."""
        today = timezone.now().date()
        return self.date_debut <= today <= self.date_fin
    
    @property
    def est_future(self):
        """Vérifie si l'année académique est dans le futur."""
        return self.date_debut > timezone.now().date()
    
    @property
    def est_passee(self):
        """Vérifie si l'année académique est passée."""
        return self.date_fin < timezone.now().date()
    
    @property
    def progression_pourcent(self):
        """Retourne le pourcentage de progression de l'année académique."""
        if self.est_future:
            return 0
        if self.est_passee:
            return 100
        
        today = timezone.now().date()
        total_jours = (self.date_fin - self.date_debut).days
        jours_ecoules = (today - self.date_debut).days
        return round((jours_ecoules / total_jours) * 100, 2) if total_jours > 0 else 0
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTHODES
    # ═══════════════════════════════════════════════════════════════════════
    
    def activate(self):
        """Activer cette année académique (désactive toutes les autres)."""
        # Désactiver toutes les autres années
        AnneeAcademique.objects.exclude(id=self.id).update(is_active=False)
        # Activer celle-ci
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
    
    def close(self):
        """Fermer (désactiver) cette année académique."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def get_inscriptions_count(self):
        """Nombre d'inscriptions pour cette année académique."""
        return self.inscriptions.count()
    
    def get_etudiants_count(self):
        """Nombre d'étudiants inscrits cette année."""
        return self.inscriptions.values('etudiant').distinct().count()
    
    @classmethod
    def get_active(cls):
        """Récupérer l'année académique active."""
        return cls.objects.filter(is_active=True).first()
    
    @classmethod
    def get_current(cls):
        """Récupérer l'année académique en cours (basé sur les dates)."""
        today = timezone.now().date()
        return cls.objects.filter(
            date_debut__lte=today,
            date_fin__gte=today
        ).first()


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE FACULTE
# ═══════════════════════════════════════════════════════════════════════════════

class Faculte(models.Model):
    """
    Faculté de l'université.
    
    Une faculté regroupe plusieurs départements.
    Ex: Faculté des Sciences et Techniques, Faculté de Médecine
    
    Optimisations :
    - Index sur code (unique), nom
    - Validators pour code, email, téléphone
    - Propriétés calculées (nombre de départements, étudiants)
    - Méthodes de statistiques
    """
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: FST, FDSP, FM",
        validators=[validate_code_faculte],
        db_index=True
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Faculté des Sciences et Techniques",
        db_index=True  # Index pour recherches et tri
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
        verbose_name="Email",
        validators=[EmailValidator(message="Format d'email invalide")]
    )
    
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone",
        validators=[validate_telephone]
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'academic_facultes'
        verbose_name = 'Faculté'
        verbose_name_plural = 'Facultés'
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code'], name='acad_fac_code_idx'),
            models.Index(fields=['nom'], name='acad_fac_nom_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def __repr__(self):
        return f"<Faculte {self.code} depts={self.departements_count}>"
    
    @property
    def departements_count(self):
        """Nombre de départements dans cette faculté."""
        return self.departements.count()
    
    @property
    def filieres_count(self):
        """Nombre total de filières dans cette faculté."""
        from django.db.models import Count
        return self.departements.aggregate(
            total=Count('filieres')
        )['total'] or 0
    
    def get_etudiants_count(self):
        """Nombre d'étudiants inscrits dans cette faculté."""
        from apps.students.models import Inscription
        return Inscription.objects.filter(
            filiere__departement__faculte=self,
            statut='INSCRIT'
        ).values('etudiant').distinct().count()


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE DEPARTEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class Departement(models.Model):
    """
    Département d'une faculté.
    
    Un département fait partie d'une faculté et regroupe plusieurs filières.
    Ex: Département d'Informatique, Département de Mathématiques
    
    Optimisations :
    - Index sur code (unique), faculte
    - Index composite (faculte, nom)
    - Propriétés calculées
    - Méthodes de statistiques
    """
    
    # RELATION: Departement → Faculte (ManyToOne)
    faculte = models.ForeignKey(
        Faculte,
        on_delete=models.CASCADE,
        related_name='departements',
        verbose_name="Faculté",
        db_index=True  # Index pour jointures
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: INFO, MATH, PHYS",
        validators=[validate_code_faculte],
        db_index=True
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Département d'Informatique",
        db_index=True
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
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'academic_departements'
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['faculte', 'nom']
        indexes = [
            models.Index(fields=['faculte', 'nom'], name='acad_dept_fac_nom_idx'),
            models.Index(fields=['code'], name='acad_dept_code_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def __repr__(self):
        return f"<Departement {self.code} faculte={self.faculte.code} filieres={self.filieres_count}>"
    
    @property
    def filieres_count(self):
        """Nombre de filières dans ce département."""
        return self.filieres.count()
    
    @property
    def filieres_actives_count(self):
        """Nombre de filières actives."""
        return self.filieres.filter(is_active=True).count()
    
    @property
    def enseignants_count(self):
        """Nombre d'enseignants dans ce département."""
        return self.enseignants.filter(statut='ACTIF').count()
    
    def get_etudiants_count(self):
        """Nombre d'étudiants dans ce département."""
        from apps.students.models import Inscription
        return Inscription.objects.filter(
            filiere__departement=self,
            statut='INSCRIT'
        ).values('etudiant').distinct().count()


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE FILIERE
# ═══════════════════════════════════════════════════════════════════════════════

class Filiere(models.Model):
    """
    Filière d'études (parcours de formation).
    
    Une filière appartient à un département et contient plusieurs matières.
    Ex: Licence 3 Informatique, Master 2 Mathématiques
    
    Optimisations :
    - Index sur code (unique), departement, cycle, is_active
    - Index composite (departement, cycle)
    - Validators pour montants
    - Propriétés calculées
    - Méthodes de statistiques
    """
    
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
        verbose_name="Département",
        db_index=True
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: L3-INFO, M2-MATH",
        db_index=True
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Licence 3 Informatique",
        db_index=True
    )
    
    cycle = models.CharField(
        max_length=20,
        choices=CYCLE_CHOICES,
        verbose_name="Cycle",
        db_index=True  # Index pour filtrage par cycle
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
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Frais d'inscription",
        help_text="Montant en FCFA"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        db_index=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'academic_filieres'
        verbose_name = 'Filière'
        verbose_name_plural = 'Filières'
        ordering = ['departement', 'cycle', 'nom']
        indexes = [
            models.Index(fields=['departement', 'cycle'], name='acad_fil_dept_cycle_idx'),
            models.Index(fields=['is_active', 'cycle'], name='acad_fil_active_cycle_idx'),
            models.Index(fields=['code'], name='acad_fil_code_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def __repr__(self):
        return f"<Filiere {self.code} cycle={self.cycle} active={self.is_active}>"
    
    @property
    def matieres_count(self):
        """Nombre de matières dans cette filière."""
        return self.matieres.count()
    
    @property
    def matieres_obligatoires_count(self):
        """Nombre de matières obligatoires."""
        return self.matieres.filter(is_optionnelle=False).count()
    
    @property
    def matieres_optionnelles_count(self):
        """Nombre de matières optionnelles."""
        return self.matieres.filter(is_optionnelle=True).count()
    
    @property
    def total_credits(self):
        """Total des crédits ECTS de la filière."""
        return self.matieres.filter(is_optionnelle=False).aggregate(
            total=Sum('credits')
        )['total'] or 0
    
    @property
    def total_heures(self):
        """Total des heures de la filière."""
        from django.db.models import F
        result = self.matieres.filter(is_optionnelle=False).aggregate(
            total=Sum(F('volume_horaire_cm') + F('volume_horaire_td') + F('volume_horaire_tp'))
        )
        return result['total'] or 0
    
    def get_etudiants_count(self, annee_academique=None):
        """Nombre d'étudiants inscrits dans cette filière."""
        from apps.students.models import Inscription
        qs = Inscription.objects.filter(filiere=self, statut='INSCRIT')
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        return qs.count()
    
    @classmethod
    def get_active(cls):
        """Récupérer toutes les filières actives."""
        return cls.objects.filter(is_active=True)
    
    @classmethod
    def get_by_cycle(cls, cycle):
        """Récupérer les filières d'un cycle."""
        return cls.objects.filter(cycle=cycle, is_active=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE MATIERE
# ═══════════════════════════════════════════════════════════════════════════════

class Matiere(models.Model):
    """
    Matière / Unité d'Enseignement.
    
    Une matière peut être enseignée dans plusieurs filières.
    Ex: Programmation Orientée Objet, Base de données, Algèbre linéaire
    
    Optimisations :
    - Index sur code (unique), semestre, is_optionnelle
    - Validators pour code matière
    - Propriétés calculées (volume horaire total)
    - Méthodes de statistiques
    """
    
    SEMESTRE_CHOICES = [
        (1, 'Semestre 1'),
        (2, 'Semestre 2'),
    ]
    
    # RELATION: Matiere ↔ Filiere (ManyToMany)
    filieres = models.ManyToManyField(
        Filiere,
        related_name='matieres',
        verbose_name="Filières"
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: INFO301, MATH205",
        validators=[validate_code_matiere],
        db_index=True
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Programmation Orientée Objet",
        db_index=True
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
        verbose_name="Semestre",
        db_index=True  # Index pour filtrage par semestre
    )
    
    is_optionnelle = models.BooleanField(
        default=False,
        verbose_name="Optionnelle",
        help_text="La matière est-elle optionnelle ?",
        db_index=True
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'academic_matieres'
        verbose_name = 'Matière'
        verbose_name_plural = 'Matières'
        ordering = ['semestre', 'nom']
        indexes = [
            models.Index(fields=['semestre', 'is_optionnelle'], name='acad_mat_sem_opt_idx'),
            models.Index(fields=['code'], name='acad_mat_code_idx'),
            models.Index(fields=['nom'], name='acad_mat_nom_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def __repr__(self):
        return f"<Matiere {self.code} credits={self.credits} opt={self.is_optionnelle}>"
    
    @property
    def volume_horaire_total(self):
        """Volume horaire total de la matière."""
        return self.volume_horaire_cm + self.volume_horaire_td + self.volume_horaire_tp
    
    @property
    def type_enseignement(self):
        """Type d'enseignement dominant."""
        if self.volume_horaire_tp > 0:
            return "Théorique et Pratique"
        elif self.volume_horaire_td > 0:
            return "Théorique avec TD"
        else:
            return "Cours Magistral"
    
    @property
    def filieres_count(self):
        """Nombre de filières où cette matière est enseignée."""
        return self.filieres.count()
    
    def get_enseignants(self, annee_academique=None):
        """Récupérer les enseignants de cette matière."""
        from apps.students.models import Attribution
        qs = Attribution.objects.filter(matiere=self)
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        return qs.select_related('enseignant', 'enseignant__user')
    
    @classmethod
    def get_by_semestre(cls, semestre):
        """Récupérer les matières d'un semestre."""
        return cls.objects.filter(semestre=semestre)
    
    @classmethod
    def get_obligatoires(cls):
        """Récupérer les matières obligatoires."""
        return cls.objects.filter(is_optionnelle=False)
    
    @classmethod
    def get_optionnelles(cls):
        """Récupérer les matières optionnelles."""
        return cls.objects.filter(is_optionnelle=True)
