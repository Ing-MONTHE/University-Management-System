"""
Modèles de gestion des étudiants et enseignants
Contient : Etudiant, Enseignant, Inscription, Attribution
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from apps.academic.models import Filiere, Matiere, Departement, AnneeAcademique
import os

User = get_user_model()

# FONCTION HELPER - UPLOAD PHOTOS
def etudiant_photo_path(instance, filename):
    # Chemin pour les photos étudiants.
    ext = filename.split('.')[-1]
    filename = f"etudiant_{instance.matricule}.{ext}"
    return os.path.join('photos/etudiants/', filename)

def enseignant_photo_path(instance, filename):
    # Chemin pour les photos enseignants.
    ext = filename.split('.')[-1]
    filename = f"enseignant_{instance.matricule}.{ext}"
    return os.path.join('photos/enseignants/', filename)


def enseignant_cv_path(instance, filename):
    # Chemin pour les CV enseignants.
    ext = filename.split('.')[-1]
    filename = f"cv_{instance.matricule}.{ext}"
    return os.path.join('cv/enseignants/', filename)

# MODÈLE ETUDIANT
class Etudiant(models.Model):
    """
    Profil étudiant.
    Lié à un User pour l'authentification.
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
        verbose_name="Utilisateur"
    )
    
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Matricule",
        help_text="Ex: ETU2024001"
    )
    
    # Informations personnelles
    date_naissance = models.DateField(
        verbose_name="Date de naissance"
    )
    
    lieu_naissance = models.CharField(
        max_length=200,
        verbose_name="Lieu de naissance"
    )
    
    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES,
        verbose_name="Sexe"
    )
    
    nationalite = models.CharField(
        max_length=100,
        default="Camerounaise",
        verbose_name="Nationalité"
    )
    
    # Contact
    telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone"
    )
    
    email_personnel = models.EmailField(
        verbose_name="Email personnel"
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
        verbose_name="Téléphone du tuteur"
    )
    
    tuteur_email = models.EmailField(
        blank=True,
        verbose_name="Email du tuteur"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIF',
        verbose_name="Statut"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students_etudiants'
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['matricule']
    
    def __str__(self):
        return f"{self.matricule} - {self.user.get_full_name()}"
    
    def get_inscriptions_actives(self):
        # Inscriptions actives de l'étudiant.
        return self.inscriptions.filter(statut='INSCRIT')
    
    def get_filiere_actuelle(self):
        # Filière actuelle (dernière inscription active).
        inscription = self.inscriptions.filter(statut='INSCRIT').order_by('-date_inscription').first()
        return inscription.filiere if inscription else None
    
    @staticmethod
    def generer_matricule(annee):
        """
        Générer un matricule unique.
        Format: ETUYYYY### (ex: ETU2024001)
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

# MODÈLE ENSEIGNANT
class Enseignant(models.Model):
    """
    Profil enseignant.
    Lié à un User pour l'authentification.
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
        verbose_name="Utilisateur"
    )
    
    # RELATION: Enseignant → Departement (ManyToOne)
    departement = models.ForeignKey(
        Departement,
        on_delete=models.SET_NULL,
        null=True,
        related_name='enseignants',
        verbose_name="Département"
    )
    
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Matricule",
        help_text="Ex: ENS2024001"
    )
    
    specialite = models.CharField(
        max_length=200,
        verbose_name="Spécialité",
        help_text="Ex: Bases de données, Intelligence Artificielle"
    )
    
    grade = models.CharField(
        max_length=30,
        choices=GRADE_CHOICES,
        verbose_name="Grade"
    )
    
    # Informations personnelles
    date_naissance = models.DateField(
        verbose_name="Date de naissance"
    )
    
    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES,
        verbose_name="Sexe"
    )
    
    # Contact
    telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone"
    )
    
    email_personnel = models.EmailField(
        verbose_name="Email personnel"
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
        verbose_name="Date d'embauche"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIF',
        verbose_name="Statut"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students_enseignants'
        verbose_name = 'Enseignant'
        verbose_name_plural = 'Enseignants'
        ordering = ['matricule']
    
    def __str__(self):
        return f"{self.matricule} - {self.user.get_full_name()} ({self.grade})"
    
    def get_matieres_enseignees(self):
        # Matières enseignées actuellement.
        return self.attributions.filter(
            annee_academique__is_active=True
        ).values_list('matiere__nom', flat=True)
    
    @staticmethod
    def generer_matricule(annee):
        """
        Générer un matricule unique.
        Format: ENSYYYY### (ex: ENS2024001)
        """
        dernier = Enseignant.objects.filter(
            matricule__startswith=f'ENS{annee}'
        ).order_by('-matricule').first()
        
        if dernier:
            numero = int(dernier.matricule[-3:]) + 1
        else:
            numero = 1
        
        return f'ENS{annee}{numero:03d}'

# MODÈLE INSCRIPTION
class Inscription(models.Model):
    # Inscription d'un étudiant à une filière pour une année académique.
    
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
        verbose_name="Étudiant"
    )
    
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Filière"
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Année académique"
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
        verbose_name="Date d'inscription"
    )
    
    montant_inscription = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant de l'inscription",
        help_text="En FCFA"
    )
    
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Montant payé",
        help_text="En FCFA"
    )
    
    statut_paiement = models.CharField(
        max_length=20,
        choices=STATUT_PAIEMENT_CHOICES,
        default='IMPAYE',
        verbose_name="Statut du paiement"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='INSCRIT',
        verbose_name="Statut de l'inscription"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students_inscriptions'
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering = ['-date_inscription']
        unique_together = ['etudiant', 'filiere', 'annee_academique']
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.filiere.code} ({self.annee_academique.code})"
    
    def get_reste_a_payer(self):
        """Montant restant à payer."""
        return self.montant_inscription - self.montant_paye
    
    def est_solde(self):
        """Vérifier si l'inscription est soldée."""
        return self.montant_paye >= self.montant_inscription
    
    def save(self, *args, **kwargs):
        """Mise à jour automatique du statut de paiement."""
        if self.montant_paye >= self.montant_inscription:
            self.statut_paiement = 'COMPLET'
        elif self.montant_paye > 0:
            self.statut_paiement = 'PARTIEL'
        else:
            self.statut_paiement = 'IMPAYE'
        
        super().save(*args, **kwargs)

# MODÈLE ATTRIBUTION
class Attribution(models.Model):
    # Attribution d'un enseignant à une matière.
    
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
        verbose_name="Enseignant"
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='attributions',
        verbose_name="Matière"
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='attributions',
        verbose_name="Année académique"
    )
    
    type_enseignement = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        verbose_name="Type d'enseignement"
    )
    
    volume_horaire_assigne = models.PositiveIntegerField(
        verbose_name="Volume horaire assigné",
        help_text="Nombre d'heures"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students_attributions'
        verbose_name = 'Attribution'
        verbose_name_plural = 'Attributions'
        ordering = ['annee_academique', 'enseignant']
        unique_together = ['enseignant', 'matiere', 'annee_academique', 'type_enseignement']
    
    def __str__(self):
        return f"{self.enseignant.user.get_full_name()} - {self.matiere.code} ({self.type_enseignement})"
