from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.students.models import Etudiant, Inscription
from apps.academic.models import Filiere, AnneeAcademique

# MODÈLE : FRAIS DE SCOLARITÉ
class FraisScolarite(BaseModel):
    """
    Définit les frais de scolarité pour une filière et une année académique.
    
    Les frais peuvent varier selon :
    - La filière (Licence, Master, etc.)
    - Le niveau (L1, L2, L3, M1, M2)
    - L'année académique
    
    Exemple : Licence Informatique L1 2025-2026 = 500,000 FCFA
    
    Relations :
    - Liée à une filière
    - Liée à une année académique
    """
    
    # Relations
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.PROTECT,
        related_name='frais_scolarite',
        help_text="Filière concernée"
    )
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.PROTECT,
        related_name='frais_scolarite',
        help_text="Année académique concernée"
    )
    
    # Niveau d'études
    niveau = models.CharField(
        max_length=10,
        help_text="Niveau d'études (ex: L1, L2, L3, M1, M2)"
    )
    
    # Montants
    montant_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Montant total des frais de scolarité (en FCFA)"
    )
    
    # Nombre de tranches autorisées
    nombre_tranches = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Nombre de tranches de paiement autorisées (1-12)"
    )
    
    # Dates limites
    date_limite_paiement = models.DateField(
        help_text="Date limite pour le paiement complet"
    )
    
    # Statut
    actif = models.BooleanField(
        default=True,
        help_text="True si ces frais sont actifs pour l'année en cours"
    )
    
    # Notes
    description = models.TextField(
        blank=True,
        help_text="Description détaillée des frais (inclus/exclus)"
    )
    
    class Meta:
        db_table = 'frais_scolarite'
        verbose_name = 'Frais de scolarité'
        verbose_name_plural = 'Frais de scolarité'
        ordering = ['-annee_academique', 'filiere', 'niveau']
        # Contrainte : un seul tarif par filière/niveau/année
        unique_together = [['filiere', 'annee_academique', 'niveau']]
        indexes = [
            models.Index(fields=['filiere', 'annee_academique']),
            models.Index(fields=['actif']),
        ]
    
    def __str__(self):
        return f"{self.filiere.nom} {self.niveau} - {self.annee_academique.nom} : {self.montant_total} FCFA"
    
    def montant_par_tranche(self):
        """
        Calcule le montant de chaque tranche de paiement.
        
        Formule : montant_total / nombre_tranches
        
        Returns:
            Decimal: Montant par tranche (arrondi à 2 décimales)
        """
        return round(self.montant_total / self.nombre_tranches, 2)

# MODÈLE : PAIEMENT
class Paiement(BaseModel):
    """
    Enregistre un paiement effectué par un étudiant.
    
    Un paiement peut être :
    - Un paiement de scolarité
    - Un paiement partiel (tranche)
    - Un paiement complet
    
    Modes de paiement supportés :
    - Espèces
    - Virement bancaire
    - Mobile Money (Orange Money, MTN MoMo, etc.)
    - Chèque
    
    Relations :
    - Liée à une inscription (étudiant + année académique)
    """
    
    # Choix de modes de paiement
    class ModePaiement(models.TextChoices):
        """
        Modes de paiement acceptés.
        
        - ESPECES : Paiement en cash
        - VIREMENT : Virement bancaire
        - MOBILE_MONEY : Mobile Money (Orange, MTN)
        - CHEQUE : Paiement par chèque
        - AUTRE : Autre mode
        """
        ESPECES = 'ESPECES', 'Espèces'
        VIREMENT = 'VIREMENT', 'Virement bancaire'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
        CHEQUE = 'CHEQUE', 'Chèque'
        AUTRE = 'AUTRE', 'Autre'
    
    # Choix de statuts de paiement
    class StatutPaiement(models.TextChoices):
        """
        Statuts du paiement.
        
        - EN_ATTENTE : Paiement en attente de validation
        - VALIDE : Paiement confirmé et validé
        - REJETE : Paiement rejeté (chèque sans provision, etc.)
        - ANNULE : Paiement annulé
        """
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        VALIDE = 'VALIDE', 'Validé'
        REJETE = 'REJETE', 'Rejeté'
        ANNULE = 'ANNULE', 'Annulé'
    
    # Relations
    inscription = models.ForeignKey(
        Inscription,
        on_delete=models.PROTECT,
        related_name='paiements',
        help_text="Inscription concernée (étudiant + année académique)"
    )
    
    # Montant et mode
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Montant payé (en FCFA)"
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=ModePaiement.choices,
        help_text="Mode de paiement utilisé"
    )
    
    # Date et référence
    date_paiement = models.DateField(
        help_text="Date à laquelle le paiement a été effectué"
    )
    numero_recu = models.CharField(
        max_length=50,
        unique=True,
        help_text="Numéro unique du reçu de paiement (généré automatiquement)"
    )
    reference_transaction = models.CharField(
        max_length=100,
        blank=True,
        help_text="Référence de la transaction (virement, mobile money, chèque)"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=StatutPaiement.choices,
        default=StatutPaiement.EN_ATTENTE,
        help_text="Statut actuel du paiement"
    )
    
    # Validation
    valide_par = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_valides',
        help_text="Utilisateur qui a validé le paiement"
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de validation"
    )
    
    # Notes
    observations = models.TextField(
        blank=True,
        help_text="Observations sur le paiement"
    )
    
    class Meta:
        db_table = 'paiements'
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-date_paiement']
        indexes = [
            models.Index(fields=['numero_recu']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_paiement']),
        ]
    
    def __str__(self):
        return f"Reçu {self.numero_recu} - {self.inscription.etudiant} : {self.montant} FCFA"
    
    def save(self, *args, **kwargs):
        """
        Génère automatiquement un numéro de reçu unique avant sauvegarde.
        
        Format : REC-YYYY-XXXXXX
        Exemple : REC-2026-000123
        """
        if not self.numero_recu:
            from django.utils import timezone
            annee = timezone.now().year
            
            # Récupérer le dernier numéro de reçu de l'année
            dernier_paiement = Paiement.objects.filter(
                numero_recu__startswith=f'REC-{annee}-'
            ).order_by('-numero_recu').first()
            
            if dernier_paiement:
                # Extraire le numéro et incrémenter
                dernier_numero = int(dernier_paiement.numero_recu.split('-')[-1])
                nouveau_numero = dernier_numero + 1
            else:
                # Premier reçu de l'année
                nouveau_numero = 1
            
            # Générer le numéro de reçu
            self.numero_recu = f'REC-{annee}-{nouveau_numero:06d}'
        
        super().save(*args, **kwargs)
    
    def valider(self, user):
        """
        Valide le paiement.
        
        Args:
            user (User): Utilisateur qui valide le paiement
        """
        from django.utils import timezone
        
        self.statut = self.StatutPaiement.VALIDE
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save()

# MODÈLE : BOURSE
class Bourse(BaseModel):
    """
    Représente une bourse ou exonération accordée à un étudiant.
    
    Types de bourses :
    - TOTALE : Exonération complète des frais
    - PARTIELLE : Réduction d'un certain pourcentage
    - MONTANT_FIXE : Réduction d'un montant fixe
    
    Sources :
    - Gouvernement
    - Université
    - Entreprise privée
    - ONG
    
    Relations :
    - Liée à un étudiant
    - Liée à une année académique
    """
    
    # Choix de types de bourses
    class TypeBourse(models.TextChoices):
        """
        Types de bourses disponibles.
        
        - TOTALE : 100% des frais pris en charge
        - PARTIELLE : Pourcentage des frais pris en charge
        - MONTANT_FIXE : Montant fixe déduit des frais
        """
        TOTALE = 'TOTALE', 'Bourse totale (100%)'
        PARTIELLE = 'PARTIELLE', 'Bourse partielle (%)'
        MONTANT_FIXE = 'MONTANT_FIXE', 'Montant fixe'
    
    # Choix de sources de financement
    class SourceFinancement(models.TextChoices):
        """
        Sources de financement de la bourse.
        """
        GOUVERNEMENT = 'GOUVERNEMENT', 'Gouvernement'
        UNIVERSITE = 'UNIVERSITE', 'Université'
        ENTREPRISE = 'ENTREPRISE', 'Entreprise privée'
        ONG = 'ONG', 'ONG'
        AUTRE = 'AUTRE', 'Autre'
    
    # Choix de statuts de bourse
    class StatutBourse(models.TextChoices):
        """
        Statuts de la bourse.
        
        - EN_COURS : Bourse active
        - SUSPENDUE : Bourse temporairement suspendue
        - TERMINEE : Bourse arrivée à terme
        - ANNULEE : Bourse annulée
        """
        EN_COURS = 'EN_COURS', 'En cours'
        SUSPENDUE = 'SUSPENDUE', 'Suspendue'
        TERMINEE = 'TERMINEE', 'Terminée'
        ANNULEE = 'ANNULEE', 'Annulée'
    
    # Relations
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='bourses',
        help_text="Étudiant bénéficiaire"
    )
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.PROTECT,
        related_name='bourses',
        help_text="Année académique concernée"
    )
    
    # Type et montant
    type_bourse = models.CharField(
        max_length=20,
        choices=TypeBourse.choices,
        help_text="Type de bourse"
    )
    
    # Pourcentage (pour bourse partielle)
    pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Pourcentage de réduction (si bourse partielle, 0-100)"
    )
    
    # Montant fixe (pour bourse à montant fixe)
    montant_fixe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Montant fixe de la bourse (en FCFA)"
    )
    
    # Source et statut
    source_financement = models.CharField(
        max_length=20,
        choices=SourceFinancement.choices,
        help_text="Source de financement de la bourse"
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutBourse.choices,
        default=StatutBourse.EN_COURS,
        help_text="Statut actuel de la bourse"
    )
    
    # Dates
    date_debut = models.DateField(
        help_text="Date de début de la bourse"
    )
    date_fin = models.DateField(
        help_text="Date de fin de la bourse"
    )
    
    # Informations complémentaires
    nom_organisme = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nom de l'organisme financeur"
    )
    reference_decision = models.CharField(
        max_length=100,
        blank=True,
        help_text="Référence de la décision d'attribution"
    )
    conditions = models.TextField(
        blank=True,
        help_text="Conditions de maintien de la bourse"
    )
    observations = models.TextField(
        blank=True,
        help_text="Observations diverses"
    )
    
    class Meta:
        db_table = 'bourses'
        verbose_name = 'Bourse'
        verbose_name_plural = 'Bourses'
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['etudiant', 'annee_academique']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"Bourse {self.get_type_bourse_display()} - {self.etudiant} ({self.annee_academique.nom})"
    
    def calculer_montant_reduction(self, montant_total):
        """
        Calcule le montant de réduction selon le type de bourse.
        
        Args:
            montant_total (Decimal): Montant total des frais de scolarité
        
        Returns:
            Decimal: Montant de la réduction
        """
        if self.type_bourse == 'TOTALE':
            return montant_total
        elif self.type_bourse == 'PARTIELLE' and self.pourcentage:
            return round((montant_total * self.pourcentage) / 100, 2)
        elif self.type_bourse == 'MONTANT_FIXE' and self.montant_fixe:
            # Ne pas dépasser le montant total
            return min(self.montant_fixe, montant_total)
        return Decimal('0.00')
    
    def est_active(self):
        """
        Vérifie si la bourse est actuellement active.
        
        Returns:
            bool: True si active, False sinon
        """
        from django.utils import timezone
        date_actuelle = timezone.now().date()
        
        return (
            self.statut == 'EN_COURS' and
            self.date_debut <= date_actuelle <= self.date_fin
        )

# MODÈLE : FACTURE
class Facture(BaseModel):
    """
    Génère une facture pour les frais de scolarité d'un étudiant.
    
    Une facture est générée automatiquement lors de l'inscription.
    Elle détaille :
    - Les frais de scolarité
    - Les bourses/exonérations
    - Le montant net à payer
    - Les paiements effectués
    - Le solde restant
    
    Relations :
    - Liée à une inscription
    - Peut être liée à une ou plusieurs bourses
    """
    
    # Choix de statuts de facture
    class StatutFacture(models.TextChoices):
        """
        Statuts de la facture.
        
        - IMPAYEE : Aucun paiement effectué
        - PARTIELLE : Paiements partiels effectués
        - SOLDEE : Totalement payée
        - ANNULEE : Facture annulée
        """
        IMPAYEE = 'IMPAYEE', 'Impayée'
        PARTIELLE = 'PARTIELLE', 'Partiellement payée'
        SOLDEE = 'SOLDEE', 'Soldée'
        ANNULEE = 'ANNULEE', 'Annulée'
    
    # Relations
    inscription = models.OneToOneField(
        Inscription,
        on_delete=models.PROTECT,
        related_name='facture',
        help_text="Inscription concernée"
    )
    
    # Numérotation
    numero_facture = models.CharField(
        max_length=50,
        unique=True,
        help_text="Numéro unique de la facture (généré automatiquement)"
    )
    
    # Montants
    montant_brut = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Montant total des frais de scolarité (avant réductions)"
    )
    montant_reduction = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Montant total des réductions (bourses, exonérations)"
    )
    montant_net = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Montant net à payer (brut - réductions)"
    )
    montant_paye = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Montant total déjà payé"
    )
    solde = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Solde restant à payer (net - payé)"
    )
    
    # Dates
    date_emission = models.DateField(
        auto_now_add=True,
        help_text="Date de génération de la facture"
    )
    date_echeance = models.DateField(
        help_text="Date limite de paiement"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=StatutFacture.choices,
        default=StatutFacture.IMPAYEE,
        help_text="Statut actuel de la facture"
    )
    
    # Notes
    observations = models.TextField(
        blank=True,
        help_text="Observations sur la facture"
    )
    
    class Meta:
        db_table = 'factures'
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-date_emission']
        indexes = [
            models.Index(fields=['numero_facture']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"Facture {self.numero_facture} - {self.inscription.etudiant}"
    
    def save(self, *args, **kwargs):
        """
        Génère automatiquement un numéro de facture unique avant sauvegarde.
        
        Format : FACT-YYYY-XXXXXX
        Exemple : FACT-2026-000456
        """
        if not self.numero_facture:
            from django.utils import timezone
            annee = timezone.now().year
            
            # Récupérer le dernier numéro de facture de l'année
            derniere_facture = Facture.objects.filter(
                numero_facture__startswith=f'FACT-{annee}-'
            ).order_by('-numero_facture').first()
            
            if derniere_facture:
                dernier_numero = int(derniere_facture.numero_facture.split('-')[-1])
                nouveau_numero = dernier_numero + 1
            else:
                nouveau_numero = 1
            
            self.numero_facture = f'FACT-{annee}-{nouveau_numero:06d}'
        
        # Calculer automatiquement le solde
        self.solde = self.montant_net - self.montant_paye
        
        # Mettre à jour le statut automatiquement
        if self.solde == 0:
            self.statut = self.StatutFacture.SOLDEE
        elif self.montant_paye > 0:
            self.statut = self.StatutFacture.PARTIELLE
        else:
            self.statut = self.StatutFacture.IMPAYEE
        
        super().save(*args, **kwargs)
    
    def enregistrer_paiement(self, montant):
        """
        Enregistre un nouveau paiement et met à jour le solde.
        
        Args:
            montant (Decimal): Montant du paiement
        """
        self.montant_paye += montant
        self.save()
    
    def calculer_taux_paiement(self):
        """
        Calcule le taux de paiement en pourcentage.
        
        Returns:
            float: Pourcentage payé (0-100)
        """
        if self.montant_net == 0:
            return 100.0
        return round((float(self.montant_paye) / float(self.montant_net)) * 100, 2)
    
    def est_en_retard(self):
        """
        Vérifie si la facture est en retard de paiement.
        
        Returns:
            bool: True si en retard, False sinon
        """
        from django.utils import timezone
        return (
            self.statut != 'SOLDEE' and
            timezone.now().date() > self.date_echeance
        )
