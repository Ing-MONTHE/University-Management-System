from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from decimal import Decimal
from datetime import date
import os
import re

from apps.academic.models import Filiere, Matiere, Departement, AnneeAcademique

User = get_user_model()


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATORS PERSONNALISÉS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_matricule_etudiant(value):
    """
    Valide le format du matricule étudiant.
    Format: ETU + ANNÉE (4 chiffres) + NUMÉRO (3 chiffres)
    Exemple: ETU2024001
    """
    if not re.match(r'^ETU\d{4}\d{3}$', value):
        raise ValidationError(
            f"Le matricule doit être au format ETUYYYY### (ex: ETU2024001). '{value}' reçu.",
            code='matricule_etudiant_invalid',
            params={'value': value}
        )


def validate_matricule_enseignant(value):
    """
    Valide le format du matricule enseignant.
    Format: ENS + ANNÉE (4 chiffres) + NUMÉRO (3 chiffres)
    Exemple: ENS2024001
    """
    if not re.match(r'^ENS\d{4}\d{3}$', value):
        raise ValidationError(
            f"Le matricule doit être au format ENSYYYY### (ex: ENS2024001). '{value}' reçu.",
            code='matricule_enseignant_invalid',
            params={'value': value}
        )


def validate_telephone_cameroun(value):
    """
    Valide le format du téléphone camerounais.
    Formats acceptés:
    - +237XXXXXXXXX
    - 6XXXXXXXX (mobile)
    - 2XXXXXXXX (fixe)
    """
    clean_value = value.replace(' ', '').replace('-', '')
    
    if not re.match(r'^(\+237)?[62]\d{8}$', clean_value):
        raise ValidationError(
            "Format de téléphone invalide. Utilisez +237XXXXXXXXX, 6XXXXXXXX ou 2XXXXXXXX.",
            code='telephone_invalid'
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS HELPER - UPLOAD PATHS
# ═══════════════════════════════════════════════════════════════════════════════

def etudiant_photo_path(instance, filename):
    """Chemin pour les photos étudiants."""
    ext = filename.split('.')[-1]
    filename = f"etudiant_{instance.matricule}.{ext}"
    return os.path.join('photos/etudiants/', filename)


def enseignant_photo_path(instance, filename):
    """Chemin pour les photos enseignants."""
    ext = filename.split('.')[-1]
    filename = f"enseignant_{instance.matricule}.{ext}"
    return os.path.join('photos/enseignants/', filename)


def enseignant_cv_path(instance, filename):
    """Chemin pour les CV enseignants."""
    ext = filename.split('.')[-1]
    filename = f"cv_{instance.matricule}.{ext}"
    return os.path.join('cv/enseignants/', filename)


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE ETUDIANT
# ═══════════════════════════════════════════════════════════════════════════════

class Etudiant(models.Model):
    """
    Profil étudiant.
    
    Lié à un User pour l'authentification.
    Contient toutes les informations personnelles, académiques et administratives.
    
    Optimisations :
    - Index sur user, matricule, statut, date_naissance
    - Index composite (statut, date_naissance)
    - Validators pour matricule et téléphone
    - Properties pour âge, nom_complet
    - Méthodes pour inscriptions et filière actuelle
    """
    
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('SUSPENDU', 'Suspendu'),
        ('DIPLOME', 'Diplômé'),
        ('ABANDONNE', 'Abandon'),
    ]
    
    # RELATION: Etudiant ↔ User (OneToOne)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='etudiant',
        verbose_name="Utilisateur",
        db_index=True  # Index pour jointures
    )
    
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Matricule",
        help_text="Ex: ETU2024001",
        validators=[validate_matricule_etudiant],
        db_index=True  # Index pour recherches rapides
    )
    
    # Informations personnelles
    date_naissance = models.DateField(
        verbose_name="Date de naissance",
        db_index=True  # Index pour calcul d'âge et tri
    )
    
    lieu_naissance = models.CharField(
        max_length=200,
        verbose_name="Lieu de naissance"
    )
    
    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES,
        verbose_name="Sexe",
        db_index=True  # Index pour statistiques
    )
    
    nationalite = models.CharField(
        max_length=100,
        default="Camerounaise",
        verbose_name="Nationalité"
    )
    
    # Contact
    telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone",
        validators=[validate_telephone_cameroun]
    )
    
    email_personnel = models.EmailField(
        verbose_name="Email personnel",
        validators=[EmailValidator(message="Format d'email invalide")]
    )
    
    # Adresse
    adresse = models.TextField(
        verbose_name="Adresse complète"
    )
    
    ville = models.CharField(
        max_length=100,
        verbose_name="Ville"
    )
    
    pays = models.CharField(
        max_length=100,
        default="Cameroun",
        verbose_name="Pays"
    )
    
    # Photo
    photo = models.ImageField(
        upload_to=etudiant_photo_path,
        blank=True,
        null=True,
        verbose_name="Photo"
    )
    
    # Tuteur/Parent
    tuteur_nom = models.CharField(
        max_length=200,
        verbose_name="Nom du tuteur"
    )
    
    tuteur_telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone du tuteur",
        validators=[validate_telephone_cameroun]
    )
    
    tuteur_email = models.EmailField(
        blank=True,
        verbose_name="Email du tuteur",
        validators=[EmailValidator(message="Format d'email invalide")]
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIF',
        verbose_name="Statut",
        db_index=True  # Index pour filtrage
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'students_etudiants'
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['matricule']
        indexes = [
            # Index composite pour requêtes fréquentes
            models.Index(fields=['statut', 'date_naissance'], name='stud_etu_stat_birth_idx'),
            models.Index(fields=['sexe', 'statut'], name='stud_etu_sex_stat_idx'),
            models.Index(fields=['-created_at'], name='stud_etu_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.matricule} - {self.nom_complet}"
    
    def __repr__(self):
        return f"<Etudiant {self.matricule} statut={self.statut} age={self.age}>"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def nom_complet(self):
        """Retourne le nom complet de l'étudiant."""
        return self.user.get_full_name() or self.user.username
    
    @property
    def age(self):
        """Calcule l'âge de l'étudiant."""
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )
    
    @property
    def is_majeur(self):
        """Vérifie si l'étudiant est majeur."""
        return self.age >= 18
    
    @property
    def is_actif(self):
        """Vérifie si l'étudiant est actif."""
        return self.statut == 'ACTIF'
    
    @property
    def inscriptions_count(self):
        """Nombre total d'inscriptions."""
        return self.inscriptions.count()
    
    @property
    def inscriptions_actives_count(self):
        """Nombre d'inscriptions actives."""
        return self.inscriptions.filter(statut='INSCRIT').count()
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTHODES
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_inscriptions_actives(self):
        """Récupère toutes les inscriptions actives de l'étudiant."""
        return self.inscriptions.filter(statut='INSCRIT').select_related(
            'filiere',
            'annee_academique'
        )
    
    def get_filiere_actuelle(self):
        """
        Retourne la filière actuelle (dernière inscription active).
        
        Returns:
            Filiere ou None
        """
        inscription = self.inscriptions.filter(
            statut='INSCRIT'
        ).select_related('filiere').order_by('-date_inscription').first()
        
        return inscription.filiere if inscription else None
    
    def get_niveau_actuel(self):
        """Retourne le niveau actuel de l'étudiant."""
        inscription = self.inscriptions.filter(
            statut='INSCRIT'
        ).order_by('-date_inscription').first()
        
        return inscription.niveau if inscription else None
    
    def get_inscription_annee(self, annee_academique):
        """
        Récupère l'inscription pour une année académique spécifique.
        
        Args:
            annee_academique: Instance AnneeAcademique
            
        Returns:
            Inscription ou None
        """
        return self.inscriptions.filter(
            annee_academique=annee_academique
        ).select_related('filiere').first()
    
    def activer(self):
        """Active l'étudiant."""
        self.statut = 'ACTIF'
        self.save(update_fields=['statut', 'updated_at'])
    
    def suspendre(self):
        """Suspend l'étudiant."""
        self.statut = 'SUSPENDU'
        self.save(update_fields=['statut', 'updated_at'])
    
    def diplomer(self):
        """Marque l'étudiant comme diplômé."""
        self.statut = 'DIPLOME'
        self.save(update_fields=['statut', 'updated_at'])
    
    @staticmethod
    def generer_matricule(annee):
        """
        Générer un matricule unique.
        
        Format: ETUYYYY### (ex: ETU2024001)
        
        Args:
            annee (int): Année (ex: 2024)
            
        Returns:
            str: Matricule généré
        """
        # Trouver le dernier matricule de l'année
        dernier = Etudiant.objects.filter(
            matricule__startswith=f'ETU{annee}'
        ).order_by('-matricule').first()
        
        if dernier:
            # Extraire le numéro et incrémenter
            numero = int(dernier.matricule[-3:]) + 1
        else:
            numero = 1
        
        return f'ETU{annee}{numero:03d}'
    
    @classmethod
    def get_actifs(cls):
        """Récupère tous les étudiants actifs."""
        return cls.objects.filter(statut='ACTIF')
    
    @classmethod
    def get_par_filiere(cls, filiere, annee_academique=None):
        """
        Récupère les étudiants d'une filière.
        
        Args:
            filiere: Instance Filiere
            annee_academique: Instance AnneeAcademique (optionnel)
        """
        qs = cls.objects.filter(
            inscriptions__filiere=filiere,
            inscriptions__statut='INSCRIT'
        ).distinct()
        
        if annee_academique:
            qs = qs.filter(inscriptions__annee_academique=annee_academique)
        
        return qs.select_related('user')
    
    @classmethod
    def search(cls, query):
        """
        Recherche d'étudiants par matricule, nom ou email.
        
        Args:
            query (str): Terme de recherche
            
        Returns:
            QuerySet: Étudiants correspondants
        """
        return cls.objects.filter(
            Q(matricule__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(email_personnel__icontains=query)
        ).select_related('user')


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE ENSEIGNANT
# ═══════════════════════════════════════════════════════════════════════════════

class Enseignant(models.Model):
    """
    Profil enseignant.
    
    Lié à un User pour l'authentification.
    Rattaché à un département.
    
    Optimisations :
    - Index sur user, departement, matricule, grade, statut
    - Index composite (departement, grade)
    - Validators pour matricule et téléphone
    - Properties pour âge, ancienneté
    - Méthodes pour matières enseignées
    """
    
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    GRADE_CHOICES = [
        ('ASSISTANT', 'Assistant'),
        ('CHARGE_COURS', 'Chargé de cours'),
        ('MAITRE_ASSISTANT', 'Maître Assistant'),
        ('MAITRE_CONFERENCES', 'Maître de Conférences'),
        ('PROFESSEUR', 'Professeur'),
    ]
    
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('EN_CONGE', 'En congé'),
        ('RETIRE', 'Retraité'),
    ]
    
    # RELATION: Enseignant ↔ User (OneToOne)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='enseignant',
        verbose_name="Utilisateur",
        db_index=True
    )
    
    # RELATION: Enseignant → Departement (ManyToOne)
    departement = models.ForeignKey(
        Departement,
        on_delete=models.SET_NULL,
        null=True,
        related_name='enseignants',
        verbose_name="Département",
        db_index=True  # Index pour jointures et filtrage
    )
    
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Matricule",
        help_text="Ex: ENS2024001",
        validators=[validate_matricule_enseignant],
        db_index=True
    )
    
    specialite = models.CharField(
        max_length=200,
        verbose_name="Spécialité",
        help_text="Ex: Bases de données, Intelligence Artificielle"
    )
    
    grade = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        verbose_name="Grade",
        db_index=True  # Index pour filtrage et statistiques
    )
    
    # Informations personnelles
    date_naissance = models.DateField(
        verbose_name="Date de naissance",
        db_index=True
    )
    
    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES,
        verbose_name="Sexe",
        db_index=True
    )
    
    nationalite = models.CharField(
        max_length=100,
        default="Camerounaise",
        verbose_name="Nationalité"
    )
    
    # Contact
    telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone",
        validators=[validate_telephone_cameroun]
    )
    
    email_personnel = models.EmailField(
        verbose_name="Email personnel",
        validators=[EmailValidator(message="Format d'email invalide")]
    )
    
    # Adresse
    adresse = models.TextField(
        verbose_name="Adresse complète"
    )
    
    # Documents
    photo = models.ImageField(
        upload_to=enseignant_photo_path,
        blank=True,
        null=True,
        verbose_name="Photo"
    )
    
    cv = models.FileField(
        upload_to=enseignant_cv_path,
        blank=True,
        null=True,
        verbose_name="CV (PDF)",
        help_text="Curriculum Vitae"
    )
    
    # Emploi
    date_embauche = models.DateField(
        verbose_name="Date d'embauche",
        db_index=True  # Index pour calcul d'ancienneté
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIF',
        verbose_name="Statut",
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'students_enseignants'
        verbose_name = 'Enseignant'
        verbose_name_plural = 'Enseignants'
        ordering = ['matricule']
        indexes = [
            models.Index(fields=['departement', 'grade'], name='stud_ens_dept_grade_idx'),
            models.Index(fields=['statut', '-date_embauche'], name='stud_ens_stat_emb_idx'),
            models.Index(fields=['grade', 'statut'], name='stud_ens_grade_stat_idx'),
        ]
    
    def __str__(self):
        return f"{self.matricule} - {self.nom_complet} ({self.grade})"
    
    def __repr__(self):
        return f"<Enseignant {self.matricule} grade={self.grade} dept={self.departement_id}>"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def nom_complet(self):
        """Retourne le nom complet de l'enseignant."""
        return self.user.get_full_name() or self.user.username
    
    @property
    def age(self):
        """Calcule l'âge de l'enseignant."""
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )
    
    @property
    def anciennete_annees(self):
        """Calcule l'ancienneté en années."""
        today = date.today()
        return today.year - self.date_embauche.year - (
            (today.month, today.day) < (self.date_embauche.month, self.date_embauche.day)
        )
    
    @property
    def is_actif(self):
        """Vérifie si l'enseignant est actif."""
        return self.statut == 'ACTIF'
    
    @property
    def attributions_count(self):
        """Nombre d'attributions (toutes années confondues)."""
        return self.attributions.count()
    
    @property
    def attributions_actives_count(self):
        """Nombre d'attributions pour l'année active."""
        return self.attributions.filter(annee_academique__is_active=True).count()
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTHODES
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_matieres_enseignees(self, annee_academique=None):
        """
        Récupère les matières enseignées.
        
        Args:
            annee_academique: Instance AnneeAcademique (si None, année active)
            
        Returns:
            QuerySet de matières
        """
        qs = self.attributions.all()
        
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        else:
            qs = qs.filter(annee_academique__is_active=True)
        
        return qs.values_list('matiere__nom', flat=True).distinct()
    
    def get_volume_horaire_total(self, annee_academique=None):
        """
        Calcule le volume horaire total assigné.
        
        Args:
            annee_academique: Instance AnneeAcademique (si None, année active)
            
        Returns:
            int: Total des heures assignées
        """
        qs = self.attributions.all()
        
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        else:
            qs = qs.filter(annee_academique__is_active=True)
        
        result = qs.aggregate(total=Sum('volume_horaire_assigne'))
        return result['total'] or 0
    
    def activer(self):
        """Active l'enseignant."""
        self.statut = 'ACTIF'
        self.save(update_fields=['statut', 'updated_at'])
    
    def mettre_en_conge(self):
        """Met l'enseignant en congé."""
        self.statut = 'EN_CONGE'
        self.save(update_fields=['statut', 'updated_at'])
    
    def mettre_a_la_retraite(self):
        """Met l'enseignant à la retraite."""
        self.statut = 'RETIRE'
        self.save(update_fields=['statut', 'updated_at'])
    
    @staticmethod
    def generer_matricule(annee):
        """
        Générer un matricule unique.
        
        Format: ENSYYYY### (ex: ENS2024001)
        
        Args:
            annee (int): Année (ex: 2024)
            
        Returns:
            str: Matricule généré
        """
        dernier = Enseignant.objects.filter(
            matricule__startswith=f'ENS{annee}'
        ).order_by('-matricule').first()
        
        if dernier:
            numero = int(dernier.matricule[-3:]) + 1
        else:
            numero = 1
        
        return f'ENS{annee}{numero:03d}'
    
    @classmethod
    def get_actifs(cls):
        """Récupère tous les enseignants actifs."""
        return cls.objects.filter(statut='ACTIF')
    
    @classmethod
    def get_par_departement(cls, departement):
        """Récupère les enseignants d'un département."""
        return cls.objects.filter(
            departement=departement,
            statut='ACTIF'
        ).select_related('user', 'departement')
    
    @classmethod
    def get_par_grade(cls, grade):
        """Récupère les enseignants d'un grade spécifique."""
        return cls.objects.filter(
            grade=grade,
            statut='ACTIF'
        ).select_related('user', 'departement')


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE INSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════════

class Inscription(models.Model):
    """
    Inscription d'un étudiant à une filière pour une année académique.
    
    Optimisations :
    - Index sur etudiant, filiere, annee_academique, statut, statut_paiement
    - Index composites pour requêtes fréquentes
    - Validators sur montants
    - Properties pour calculs financiers
    - Méthode save() avec calcul auto du statut paiement
    """
    
    STATUT_PAIEMENT_CHOICES = [
        ('COMPLET', 'Paiement complet'),
        ('PARTIEL', 'Paiement partiel'),
        ('IMPAYE', 'Impayé'),
    ]
    
    STATUT_CHOICES = [
        ('INSCRIT', 'Inscrit'),
        ('ABANDONNE', 'Abandon'),
        ('TRANSFERE', 'Transféré'),
    ]
    
    # RELATIONS
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Étudiant",
        db_index=True
    )
    
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Filière",
        db_index=True
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Année académique",
        db_index=True
    )
    
    # Niveau d'études
    niveau = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        verbose_name="Niveau",
        help_text="Ex: 1 (L1), 2 (L2), 3 (L3)"
    )
    
    # Dates et paiement
    date_inscription = models.DateField(
        auto_now_add=True,
        verbose_name="Date d'inscription",
        db_index=True
    )
    
    montant_inscription = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant de l'inscription",
        help_text="En FCFA",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Montant payé",
        help_text="En FCFA",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    statut_paiement = models.CharField(
        max_length=20,
        choices=STATUT_PAIEMENT_CHOICES,
        default='IMPAYE',
        verbose_name="Statut du paiement",
        db_index=True  # Index pour filtrage
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='INSCRIT',
        verbose_name="Statut de l'inscription",
        db_index=True  # Index pour filtrage
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'students_inscriptions'
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering = ['-date_inscription']
        unique_together = ['etudiant', 'filiere', 'annee_academique']
        indexes = [
            models.Index(fields=['etudiant', 'annee_academique'], name='stud_insc_etu_annee_idx'),
            models.Index(fields=['filiere', 'statut'], name='stud_insc_fil_stat_idx'),
            models.Index(fields=['annee_academique', 'statut'], name='stud_insc_annee_stat_idx'),
            models.Index(fields=['statut_paiement', '-date_inscription'], name='stud_insc_paie_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.filiere.code} ({self.annee_academique.code})"
    
    def __repr__(self):
        return f"<Inscription etu={self.etudiant.matricule} fil={self.filiere.code} stat={self.statut}>"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def reste_a_payer(self):
        """Montant restant à payer."""
        return self.montant_inscription - self.montant_paye
    
    @property
    def est_solde(self):
        """Vérifie si l'inscription est soldée."""
        return self.montant_paye >= self.montant_inscription
    
    @property
    def taux_paiement_pourcent(self):
        """Taux de paiement en pourcentage."""
        if self.montant_inscription == 0:
            return 0
        return round((self.montant_paye / self.montant_inscription) * 100, 2)
    
    @property
    def is_actif(self):
        """Vérifie si l'inscription est active."""
        return self.statut == 'INSCRIT'
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTHODES
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_reste_a_payer(self):
        """Montant restant à payer (méthode)."""
        return self.reste_a_payer
    
    def save(self, *args, **kwargs):
        """
        Sauvegarde avec mise à jour automatique du statut de paiement.
        """
        # Calculer le statut de paiement
        if self.montant_paye >= self.montant_inscription:
            self.statut_paiement = 'COMPLET'
        elif self.montant_paye > 0:
            self.statut_paiement = 'PARTIEL'
        else:
            self.statut_paiement = 'IMPAYE'
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_actives(cls):
        """Récupère toutes les inscriptions actives."""
        return cls.objects.filter(statut='INSCRIT')
    
    @classmethod
    def get_par_annee(cls, annee_academique):
        """Récupère les inscriptions d'une année académique."""
        return cls.objects.filter(annee_academique=annee_academique)
    
    @classmethod
    def get_impayees(cls):
        """Récupère les inscriptions non soldées."""
        return cls.objects.filter(
            statut='INSCRIT',
            statut_paiement__in=['IMPAYE', 'PARTIEL']
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE ATTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════════

class Attribution(models.Model):
    """
    Attribution d'un enseignant à une matière.
    
    Définit qui enseigne quoi (CM, TD, TP) pour une année académique.
    
    Optimisations :
    - Index sur toutes les FK
    - Index composite (matiere, annee_academique)
    - Unique together pour éviter les doublons
    - Property pour heures assignées
    """
    
    TYPE_CHOICES = [
        ('CM', 'Cours Magistral'),
        ('TD', 'Travaux Dirigés'),
        ('TP', 'Travaux Pratiques'),
    ]
    
    # RELATIONS
    enseignant = models.ForeignKey(
        Enseignant,
        on_delete=models.CASCADE,
        related_name='attributions',
        verbose_name="Enseignant",
        db_index=True
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='attributions',
        verbose_name="Matière",
        db_index=True
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='attributions',
        verbose_name="Année académique",
        db_index=True
    )
    
    type_enseignement = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        verbose_name="Type d'enseignement",
        db_index=True  # Index pour filtrage
    )
    
    volume_horaire_assigne = models.PositiveIntegerField(
        verbose_name="Volume horaire assigné",
        help_text="Nombre d'heures"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'students_attributions'
        verbose_name = 'Attribution'
        verbose_name_plural = 'Attributions'
        ordering = ['annee_academique', 'enseignant']
        unique_together = ['enseignant', 'matiere', 'annee_academique', 'type_enseignement']
        indexes = [
            models.Index(fields=['matiere', 'annee_academique'], name='stud_attr_mat_annee_idx'),
            models.Index(fields=['enseignant', 'type_enseignement'], name='stud_attr_ens_type_idx'),
            models.Index(fields=['annee_academique', 'type_enseignement'], name='stud_attr_annee_type_idx'),
        ]
    
    def __str__(self):
        return f"{self.enseignant.nom_complet} - {self.matiere.code} ({self.type_enseignement})"
    
    def __repr__(self):
        return f"<Attribution ens={self.enseignant_id} mat={self.matiere.code} type={self.type_enseignement}>"
    
    @property
    def heures_assignees(self):
        """Alias pour volume_horaire_assigne."""
        return self.volume_horaire_assigne
    
    @classmethod
    def get_par_annee(cls, annee_academique):
        """Récupère les attributions d'une année académique."""
        return cls.objects.filter(annee_academique=annee_academique)
    
    @classmethod
    def get_par_enseignant(cls, enseignant, annee_academique=None):
        """Récupère les attributions d'un enseignant."""
        qs = cls.objects.filter(enseignant=enseignant)
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        return qs.select_related('matiere', 'annee_academique')
    
    @classmethod
    def get_par_matiere(cls, matiere, annee_academique=None):
        """Récupère les attributions d'une matière."""
        qs = cls.objects.filter(matiere=matiere)
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        return qs.select_related('enseignant__user', 'annee_academique')
