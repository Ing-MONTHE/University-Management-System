from django.db import models
from apps.core.models import BaseModel, User
from apps.academic.models import AnneeAcademique, Filiere

# MODÈLE : RAPPORT
class Rapport(BaseModel):
    """
    Représente un rapport généré ou planifié.
    
    Types de rapports :
    - ACADEMIQUE : Rapports académiques (inscriptions, résultats, délibérations)
    - FINANCIER : Rapports financiers (paiements, bourses, recouvrement)
    - BIBLIOTHEQUE : Rapports bibliothèque (emprunts, retards)
    - PRESENCE : Rapports de présence (absences, justificatifs)
    - RESSOURCES : Rapports ressources (équipements, réservations, maintenances)
    - COMMUNICATIONS : Rapports communications (annonces, notifications, messages)
    - DOCUMENTS : Rapports documents (génération, délivrance)
    - GLOBAL : Rapports généraux (vue d'ensemble)
    
    Formats d'export :
    - PDF : Document PDF
    - EXCEL : Fichier Excel (.xlsx)
    - CSV : Fichier CSV
    - JSON : Données JSON
    
    Fréquences (pour rapports planifiés) :
    - UNIQUE : Une seule fois
    - QUOTIDIEN : Tous les jours
    - HEBDOMADAIRE : Toutes les semaines
    - MENSUEL : Tous les mois
    - TRIMESTRIEL : Tous les trimestres
    - ANNUEL : Tous les ans
    
    Relations :
    - Créé par un utilisateur
    - Peut être lié à une année académique
    - Peut être lié à une filière
    """
    
    # Choix de types de rapports
    class TypeRapport(models.TextChoices):
        """
        Types de rapports disponibles.
        """
        ACADEMIQUE = 'ACADEMIQUE', 'Académique'
        FINANCIER = 'FINANCIER', 'Financier'
        BIBLIOTHEQUE = 'BIBLIOTHEQUE', 'Bibliothèque'
        PRESENCE = 'PRESENCE', 'Présence'
        RESSOURCES = 'RESSOURCES', 'Ressources'
        COMMUNICATIONS = 'COMMUNICATIONS', 'Communications'
        DOCUMENTS = 'DOCUMENTS', 'Documents'
        GLOBAL = 'GLOBAL', 'Global'
    
    # Choix de formats
    class FormatExport(models.TextChoices):
        """
        Formats d'export disponibles.
        """
        PDF = 'PDF', 'PDF'
        EXCEL = 'EXCEL', 'Excel'
        CSV = 'CSV', 'CSV'
        JSON = 'JSON', 'JSON'
    
    # Choix de fréquences
    class FrequenceRapport(models.TextChoices):
        """
        Fréquences de génération automatique.
        """
        UNIQUE = 'UNIQUE', 'Unique'
        QUOTIDIEN = 'QUOTIDIEN', 'Quotidien'
        HEBDOMADAIRE = 'HEBDOMADAIRE', 'Hebdomadaire'
        MENSUEL = 'MENSUEL', 'Mensuel'
        TRIMESTRIEL = 'TRIMESTRIEL', 'Trimestriel'
        ANNUEL = 'ANNUEL', 'Annuel'
    
    # Informations générales
    titre = models.CharField(
        max_length=200,
        help_text="Titre du rapport"
    )
    description = models.TextField(
        blank=True,
        help_text="Description du rapport"
    )
    
    # Type et format
    type_rapport = models.CharField(
        max_length=20,
        choices=TypeRapport.choices,
        help_text="Type de rapport"
    )
    format_export = models.CharField(
        max_length=10,
        choices=FormatExport.choices,
        default=FormatExport.PDF,
        help_text="Format d'export"
    )
    
    # Période couverte
    date_debut = models.DateField(
        help_text="Date de début de la période couverte"
    )
    date_fin = models.DateField(
        help_text="Date de fin de la période couverte"
    )
    
    # Relations optionnelles
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports',
        help_text="Année académique concernée (si applicable)"
    )
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports',
        help_text="Filière concernée (si applicable)"
    )
    
    # Fichier généré
    fichier = models.FileField(
        upload_to='rapports/%Y/%m/',
        null=True,
        blank=True,
        help_text="Fichier du rapport généré"
    )
    
    # Génération
    genere = models.BooleanField(
        default=False,
        help_text="True si le rapport a été généré"
    )
    date_generation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de génération"
    )
    genere_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_generes',
        help_text="Utilisateur qui a généré le rapport"
    )
    
    # Planification (pour rapports automatiques)
    planifie = models.BooleanField(
        default=False,
        help_text="True si le rapport est planifié pour génération automatique"
    )
    frequence = models.CharField(
        max_length=20,
        choices=FrequenceRapport.choices,
        default=FrequenceRapport.UNIQUE,
        help_text="Fréquence de génération automatique"
    )
    prochaine_execution = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de la prochaine exécution planifiée"
    )
    
    # Paramètres personnalisés (JSON)
    parametres = models.JSONField(
        default=dict,
        blank=True,
        help_text="Paramètres personnalisés du rapport (filtres, options)"
    )
    
    class Meta:
        db_table = 'rapports'
        verbose_name = 'Rapport'
        verbose_name_plural = 'Rapports'
        ordering = ['-date_generation', '-created_at']
        indexes = [
            models.Index(fields=['type_rapport']),
            models.Index(fields=['genere']),
            models.Index(fields=['planifie']),
        ]
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_rapport_display()})"
    
    def generer_rapport(self, user):
        """
        Génère le rapport.
        
        Args:
            user (User): Utilisateur qui génère le rapport
        """
        from django.utils import timezone
        
        self.genere = True
        self.date_generation = timezone.now()
        self.genere_par = user
        self.save()
    
    def calculer_prochaine_execution(self):
        """
        Calcule la date de la prochaine exécution selon la fréquence.
        
        Returns:
            datetime: Date de la prochaine exécution
        """
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.planifie:
            return None
        
        maintenant = timezone.now()
        
        if self.frequence == 'QUOTIDIEN':
            return maintenant + timedelta(days=1)
        elif self.frequence == 'HEBDOMADAIRE':
            return maintenant + timedelta(weeks=1)
        elif self.frequence == 'MENSUEL':
            return maintenant + timedelta(days=30)
        elif self.frequence == 'TRIMESTRIEL':
            return maintenant + timedelta(days=90)
        elif self.frequence == 'ANNUEL':
            return maintenant + timedelta(days=365)
        
        return None

# MODÈLE : DASHBOARD
class Dashboard(BaseModel):
    """
    Représente un tableau de bord personnalisé.
    
    Types de dashboards :
    - GENERAL : Vue d'ensemble générale
    - ACADEMIQUE : Dashboard académique
    - FINANCIER : Dashboard financier
    - ETUDIANT : Dashboard étudiant
    - ENSEIGNANT : Dashboard enseignant
    - ADMINISTRATION : Dashboard administration
    
    Relations :
    - Créé par un utilisateur
    - Peut être partagé avec d'autres utilisateurs
    """
    
    # Choix de types de dashboards
    class TypeDashboard(models.TextChoices):
        """
        Types de dashboards.
        """
        GENERAL = 'GENERAL', 'Général'
        ACADEMIQUE = 'ACADEMIQUE', 'Académique'
        FINANCIER = 'FINANCIER', 'Financier'
        ETUDIANT = 'ETUDIANT', 'Étudiant'
        ENSEIGNANT = 'ENSEIGNANT', 'Enseignant'
        ADMINISTRATION = 'ADMINISTRATION', 'Administration'
    
    # Informations générales
    nom = models.CharField(
        max_length=200,
        help_text="Nom du dashboard"
    )
    description = models.TextField(
        blank=True,
        help_text="Description du dashboard"
    )
    
    # Type
    type_dashboard = models.CharField(
        max_length=20,
        choices=TypeDashboard.choices,
        help_text="Type de dashboard"
    )
    
    # Propriétaire
    proprietaire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards_proprietaire',
        help_text="Propriétaire du dashboard"
    )
    
    # Partage
    partage = models.BooleanField(
        default=False,
        help_text="True si le dashboard est partagé"
    )
    utilisateurs_partages = models.ManyToManyField(
        User,
        blank=True,
        related_name='dashboards_partages',
        help_text="Utilisateurs avec qui le dashboard est partagé"
    )
    
    # Configuration (JSON)
    configuration = models.JSONField(
        default=dict,
        help_text="Configuration du dashboard (widgets, layout, filtres)"
    )
    
    # Par défaut
    par_defaut = models.BooleanField(
        default=False,
        help_text="True si c'est le dashboard par défaut de l'utilisateur"
    )
    
    class Meta:
        db_table = 'dashboards'
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
        ordering = ['nom']
        unique_together = [['proprietaire', 'nom']]
    
    def __str__(self):
        return f"{self.nom} ({self.proprietaire.username})"

# MODÈLE : KPI (INDICATEUR CLÉ DE PERFORMANCE)
class KPI(BaseModel):
    """
    Représente un indicateur clé de performance (Key Performance Indicator).
    
    Catégories :
    - ACADEMIQUE : KPIs académiques (taux de réussite, moyenne, etc.)
    - FINANCIER : KPIs financiers (recouvrement, bourses, etc.)
    - BIBLIOTHEQUE : KPIs bibliothèque (taux d'emprunt, retards, etc.)
    - PRESENCE : KPIs présence (taux de présence, absences, etc.)
    - RESSOURCES : KPIs ressources (utilisation, maintenance, etc.)
    
    Types de valeurs :
    - NOMBRE : Valeur numérique simple (ex: 150)
    - POURCENTAGE : Pourcentage (ex: 75.5%)
    - MONTANT : Montant financier (ex: 1500000 FCFA)
    - RATIO : Ratio (ex: 3:1)
    
    Relations :
    - Peut être lié à une année académique
    - Peut être lié à une filière
    """
    
    # Choix de catégories
    class CategorieKPI(models.TextChoices):
        """
        Catégories de KPIs.
        """
        ACADEMIQUE = 'ACADEMIQUE', 'Académique'
        FINANCIER = 'FINANCIER', 'Financier'
        BIBLIOTHEQUE = 'BIBLIOTHEQUE', 'Bibliothèque'
        PRESENCE = 'PRESENCE', 'Présence'
        RESSOURCES = 'RESSOURCES', 'Ressources'
    
    # Choix de types de valeurs
    class TypeValeur(models.TextChoices):
        """
        Types de valeurs.
        """
        NOMBRE = 'NOMBRE', 'Nombre'
        POURCENTAGE = 'POURCENTAGE', 'Pourcentage'
        MONTANT = 'MONTANT', 'Montant'
        RATIO = 'RATIO', 'Ratio'
    
    # Informations générales
    nom = models.CharField(
        max_length=200,
        help_text="Nom du KPI"
    )
    description = models.TextField(
        blank=True,
        help_text="Description du KPI"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Code unique du KPI (ex: TAUX_REUSSITE)"
    )
    
    # Catégorie et type
    categorie = models.CharField(
        max_length=20,
        choices=CategorieKPI.choices,
        help_text="Catégorie du KPI"
    )
    type_valeur = models.CharField(
        max_length=20,
        choices=TypeValeur.choices,
        help_text="Type de valeur"
    )
    
    # Valeur actuelle
    valeur = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Valeur actuelle du KPI"
    )
    
    # Objectif
    objectif = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valeur objectif à atteindre"
    )
    
    # Période
    date_calcul = models.DateField(
        help_text="Date de calcul de la valeur"
    )
    
    # Relations optionnelles
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kpis',
        help_text="Année académique concernée"
    )
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kpis',
        help_text="Filière concernée"
    )
    
    # Actif
    actif = models.BooleanField(
        default=True,
        help_text="True si le KPI est actif"
    )
    
    class Meta:
        db_table = 'kpis'
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'
        ordering = ['categorie', 'nom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['categorie']),
            models.Index(fields=['actif']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    def calculer_taux_atteinte(self):
        """
        Calcule le taux d'atteinte de l'objectif.
        
        Returns:
            float: Taux d'atteinte en pourcentage (ou None si pas d'objectif)
        """
        if not self.objectif or self.objectif == 0:
            return None
        
        return float((self.valeur / self.objectif) * 100)
    
    def est_objectif_atteint(self):
        """
        Vérifie si l'objectif est atteint.
        
        Returns:
            bool: True si objectif atteint (ou None si pas d'objectif)
        """
        if not self.objectif:
            return None
        
        return self.valeur >= self.objectif
