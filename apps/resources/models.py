from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel, User
from apps.schedule.models import Salle

# MODÈLE : ÉQUIPEMENT
class Equipement(BaseModel):
    """
    Représente un équipement ou matériel de l'université.
    
    Types d'équipements :
    - INFORMATIQUE : Ordinateurs, projecteurs, imprimantes
    - AUDIOVISUEL : Caméras, micros, enceintes
    - MOBILIER : Tables, chaises, tableaux
    - SPORTIF : Ballons, filets, équipements de sport
    - SCIENTIFIQUE : Microscopes, équipements de laboratoire
    - AUTRE : Autres équipements
    
    États :
    - DISPONIBLE : Équipement disponible pour réservation
    - RESERVE : Équipement actuellement réservé
    - EN_MAINTENANCE : Équipement en maintenance
    - HORS_SERVICE : Équipement hors service (panne)
    
    Relations :
    - Peut être lié à une salle (emplacement par défaut)
    """
    
    # Choix de catégories d'équipements
    class CategorieEquipement(models.TextChoices):
        """
        Catégories d'équipements.
        
        - INFORMATIQUE : Matériel informatique
        - AUDIOVISUEL : Matériel audiovisuel
        - MOBILIER : Mobilier et aménagement
        - SPORTIF : Équipements sportifs
        - SCIENTIFIQUE : Équipements de laboratoire
        - AUTRE : Autres équipements
        """
        INFORMATIQUE = 'INFORMATIQUE', 'Informatique'
        AUDIOVISUEL = 'AUDIOVISUEL', 'Audiovisuel'
        MOBILIER = 'MOBILIER', 'Mobilier'
        SPORTIF = 'SPORTIF', 'Sportif'
        SCIENTIFIQUE = 'SCIENTIFIQUE', 'Scientifique'
        AUTRE = 'AUTRE', 'Autre'
    
    # Choix d'états
    class EtatEquipement(models.TextChoices):
        """
        États de l'équipement.
        
        - DISPONIBLE : Disponible pour réservation
        - RESERVE : Actuellement réservé
        - EN_MAINTENANCE : En cours de maintenance
        - HORS_SERVICE : Hors service (panne)
        """
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        RESERVE = 'RESERVE', 'Réservé'
        EN_MAINTENANCE = 'EN_MAINTENANCE', 'En maintenance'
        HORS_SERVICE = 'HORS_SERVICE', 'Hors service'
    
    # Informations générales
    nom = models.CharField(
        max_length=200,
        help_text="Nom de l'équipement"
    )
    description = models.TextField(
        blank=True,
        help_text="Description détaillée de l'équipement"
    )
    reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Référence unique de l'équipement (code-barres, numéro série)"
    )
    
    # Catégorie et état
    categorie = models.CharField(
        max_length=20,
        choices=CategorieEquipement.choices,
        help_text="Catégorie de l'équipement"
    )
    etat = models.CharField(
        max_length=20,
        choices=EtatEquipement.choices,
        default=EtatEquipement.DISPONIBLE,
        help_text="État actuel de l'équipement"
    )
    
    # Emplacement
    salle = models.ForeignKey(
        Salle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipements_inventaire',
        help_text="Salle où se trouve l'équipement (emplacement par défaut)"
    )
    
    # Quantité et stock
    quantite_disponible = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Quantité disponible en stock"
    )
    quantite_totale = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantité totale (disponible + réservée + en maintenance)"
    )
    
    # Informations d'achat
    date_acquisition = models.DateField(
        null=True,
        blank=True,
        help_text="Date d'achat de l'équipement"
    )
    valeur_acquisition = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Valeur d'achat (en FCFA)"
    )
    
    # Maintenance
    dernier_entretien = models.DateField(
        null=True,
        blank=True,
        help_text="Date du dernier entretien/maintenance"
    )
    prochain_entretien = models.DateField(
        null=True,
        blank=True,
        help_text="Date du prochain entretien prévu"
    )
    
    # Réservabilité
    reservable = models.BooleanField(
        default=True,
        help_text="True si l'équipement peut être réservé"
    )
    
    # Notes
    observations = models.TextField(
        blank=True,
        help_text="Observations diverses"
    )
    
    class Meta:
        db_table = 'equipements'
        verbose_name = 'Équipement'
        verbose_name_plural = 'Équipements'
        ordering = ['nom']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['categorie']),
            models.Index(fields=['etat']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.reference})"
    
    def est_disponible(self):
        """
        Vérifie si l'équipement est disponible pour réservation.
        
        Returns:
            bool: True si disponible
        """
        return self.etat == 'DISPONIBLE' and self.quantite_disponible > 0 and self.reservable
    
    def changer_etat(self, nouvel_etat):
        """
        Change l'état de l'équipement.
        
        Args:
            nouvel_etat (str): Nouvel état
        """
        self.etat = nouvel_etat
        self.save()
    
    def reserver(self, quantite=1):
        """
        Réserve une certaine quantité de l'équipement.
        
        Args:
            quantite (int): Quantité à réserver
        
        Returns:
            bool: True si réservation réussie, False sinon
        """
        if self.quantite_disponible >= quantite:
            self.quantite_disponible -= quantite
            
            # Changer l'état si tout est réservé
            if self.quantite_disponible == 0:
                self.etat = 'RESERVE'
            
            self.save()
            return True
        return False
    
    def liberer(self, quantite=1):
        """
        Libère une certaine quantité de l'équipement.
        
        Args:
            quantite (int): Quantité à libérer
        """
        self.quantite_disponible = min(
            self.quantite_disponible + quantite,
            self.quantite_totale
        )
        
        # Remettre disponible si au moins 1 exemplaire dispo
        if self.quantite_disponible > 0 and self.etat == 'RESERVE':
            self.etat = 'DISPONIBLE'
        
        self.save()

# MODÈLE : RÉSERVATION
class Reservation(BaseModel):
    """
    Représente une réservation de salle ou d'équipement.
    
    Types de réservations :
    - SALLE : Réservation de salle uniquement
    - EQUIPEMENT : Réservation d'équipement uniquement
    - SALLE_EQUIPEMENT : Réservation salle + équipements
    
    Statuts :
    - EN_ATTENTE : Demande en attente de validation
    - VALIDEE : Réservation confirmée
    - REJETEE : Demande rejetée
    - ANNULEE : Réservation annulée
    - TERMINEE : Réservation terminée (passée)
    
    Relations :
    - Demandée par un utilisateur
    - Validée par un utilisateur
    - Peut concerner une salle
    - Peut concerner des équipements
    """
    
    # Choix de types de réservation
    class TypeReservation(models.TextChoices):
        """
        Types de réservations.
        
        - SALLE : Réservation de salle uniquement
        - EQUIPEMENT : Réservation d'équipement uniquement
        - SALLE_EQUIPEMENT : Réservation combinée
        """
        SALLE = 'SALLE', 'Salle'
        EQUIPEMENT = 'EQUIPEMENT', 'Équipement'
        SALLE_EQUIPEMENT = 'SALLE_EQUIPEMENT', 'Salle + Équipement'
    
    # Choix de statuts
    class StatutReservation(models.TextChoices):
        """
        Statuts de la réservation.
        
        - EN_ATTENTE : En attente de validation
        - VALIDEE : Réservation confirmée
        - REJETEE : Demande rejetée
        - ANNULEE : Réservation annulée
        - TERMINEE : Réservation passée
        """
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        VALIDEE = 'VALIDEE', 'Validée'
        REJETEE = 'REJETEE', 'Rejetée'
        ANNULEE = 'ANNULEE', 'Annulée'
        TERMINEE = 'TERMINEE', 'Terminée'
    
    # Demandeur
    demandeur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations',
        help_text="Utilisateur qui fait la demande de réservation"
    )
    
    # Type de réservation
    type_reservation = models.CharField(
        max_length=20,
        choices=TypeReservation.choices,
        help_text="Type de réservation"
    )
    
    # Ressources réservées
    salle = models.ForeignKey(
        Salle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations',
        help_text="Salle réservée (si applicable)"
    )
    
    # Période de réservation
    date_debut = models.DateTimeField(
        help_text="Date et heure de début de la réservation"
    )
    date_fin = models.DateTimeField(
        help_text="Date et heure de fin de la réservation"
    )
    
    # Motif
    motif = models.CharField(
        max_length=200,
        help_text="Motif de la réservation (ex: réunion, cours, événement)"
    )
    description = models.TextField(
        blank=True,
        help_text="Description détaillée de l'activité prévue"
    )
    
    # Nombre de participants
    nombre_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Nombre de participants attendus"
    )
    
    # Statut et validation
    statut = models.CharField(
        max_length=20,
        choices=StatutReservation.choices,
        default=StatutReservation.EN_ATTENTE,
        help_text="Statut actuel de la réservation"
    )
    
    valide_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations_validees',
        help_text="Utilisateur qui a validé/rejeté la réservation"
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de validation/rejet"
    )
    commentaire_validation = models.TextField(
        blank=True,
        help_text="Commentaire lors de la validation/rejet"
    )
    
    class Meta:
        db_table = 'reservations'
        verbose_name = 'Réservation'
        verbose_name_plural = 'Réservations'
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['demandeur']),
            models.Index(fields=['salle', 'date_debut']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"Réservation {self.get_type_reservation_display()} - {self.demandeur.username} ({self.date_debut.date()})"
    
    def valider(self, user, commentaire=''):
        """
        Valide la réservation.
        
        Args:
            user (User): Utilisateur qui valide
            commentaire (str): Commentaire optionnel
        """
        from django.utils import timezone
        
        self.statut = self.StatutReservation.VALIDEE
        self.valide_par = user
        self.date_validation = timezone.now()
        self.commentaire_validation = commentaire
        self.save()
    
    def rejeter(self, user, commentaire):
        """
        Rejette la réservation.
        
        Args:
            user (User): Utilisateur qui rejette
            commentaire (str): Motif du rejet (obligatoire)
        """
        from django.utils import timezone
        
        self.statut = self.StatutReservation.REJETEE
        self.valide_par = user
        self.date_validation = timezone.now()
        self.commentaire_validation = commentaire
        self.save()
    
    def annuler(self):
        """
        Annule la réservation.
        """
        self.statut = self.StatutReservation.ANNULEE
        self.save()
    
    def calculer_duree(self):
        """
        Calcule la durée de la réservation en heures.
        
        Returns:
            float: Durée en heures
        """
        delta = self.date_fin - self.date_debut
        return delta.total_seconds() / 3600

# MODÈLE : RÉSERVATION ÉQUIPEMENT
class ReservationEquipement(BaseModel):
    """
    Représente un équipement réservé dans une réservation.
    
    Permet de gérer les équipements multiples dans une réservation.
    
    Relations :
    - Liée à une réservation
    - Liée à un équipement
    """
    
    # Relations
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='equipements_reserves',
        help_text="Réservation concernée"
    )
    equipement = models.ForeignKey(
        Equipement,
        on_delete=models.CASCADE,
        related_name='reservations',
        help_text="Équipement réservé"
    )
    
    # Quantité
    quantite = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantité réservée"
    )
    
    # Retour
    retourne = models.BooleanField(
        default=False,
        help_text="True si l'équipement a été retourné"
    )
    date_retour = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure du retour"
    )
    etat_retour = models.TextField(
        blank=True,
        help_text="État de l'équipement au retour"
    )
    
    class Meta:
        db_table = 'reservations_equipements'
        verbose_name = 'Réservation d\'équipement'
        verbose_name_plural = 'Réservations d\'équipements'
        ordering = ['reservation', 'equipement']
        unique_together = [['reservation', 'equipement']]
    
    def __str__(self):
        return f"{self.equipement.nom} x{self.quantite} - Réservation #{self.reservation.id}"
    
    def marquer_retour(self, etat_retour=''):
        """
        Marque l'équipement comme retourné.
        
        Args:
            etat_retour (str): État au retour
        """
        from django.utils import timezone
        
        self.retourne = True
        self.date_retour = timezone.now()
        self.etat_retour = etat_retour
        self.save()
        
        # Libérer l'équipement
        self.equipement.liberer(self.quantite)

# MODÈLE : MAINTENANCE
class Maintenance(BaseModel):
    """
    Représente une maintenance (préventive ou corrective) d'un équipement.
    
    Types de maintenance :
    - PREVENTIVE : Maintenance planifiée (entretien régulier)
    - CORRECTIVE : Réparation suite à une panne
    - URGENTE : Intervention urgente
    
    Statuts :
    - PLANIFIEE : Maintenance planifiée (future)
    - EN_COURS : Maintenance en cours d'exécution
    - TERMINEE : Maintenance terminée
    - ANNULEE : Maintenance annulée
    
    Relations :
    - Liée à un équipement
    - Technicien assigné (optionnel)
    """
    
    # Choix de types de maintenance
    class TypeMaintenance(models.TextChoices):
        """
        Types de maintenance.
        
        - PREVENTIVE : Entretien préventif planifié
        - CORRECTIVE : Réparation après panne
        - URGENTE : Intervention urgente
        """
        PREVENTIVE = 'PREVENTIVE', 'Préventive'
        CORRECTIVE = 'CORRECTIVE', 'Corrective'
        URGENTE = 'URGENTE', 'Urgente'
    
    # Choix de statuts
    class StatutMaintenance(models.TextChoices):
        """
        Statuts de la maintenance.
        
        - PLANIFIEE : Planifiée pour plus tard
        - EN_COURS : En cours d'exécution
        - TERMINEE : Terminée avec succès
        - ANNULEE : Annulée
        """
        PLANIFIEE = 'PLANIFIEE', 'Planifiée'
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINEE = 'TERMINEE', 'Terminée'
        ANNULEE = 'ANNULEE', 'Annulée'
    
    # Équipement concerné
    equipement = models.ForeignKey(
        Equipement,
        on_delete=models.CASCADE,
        related_name='maintenances',
        help_text="Équipement concerné par la maintenance"
    )
    
    # Type et statut
    type_maintenance = models.CharField(
        max_length=20,
        choices=TypeMaintenance.choices,
        help_text="Type de maintenance"
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutMaintenance.choices,
        default=StatutMaintenance.PLANIFIEE,
        help_text="Statut actuel de la maintenance"
    )
    
    # Dates
    date_planifiee = models.DateField(
        help_text="Date planifiée pour la maintenance"
    )
    date_debut = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de début effectif"
    )
    date_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de fin"
    )
    
    # Technicien
    technicien = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenances_assignees',
        help_text="Technicien assigné à la maintenance"
    )
    
    # Description
    description = models.TextField(
        help_text="Description de la maintenance/panne"
    )
    
    # Intervention
    travaux_effectues = models.TextField(
        blank=True,
        help_text="Description des travaux effectués"
    )
    pieces_remplacees = models.TextField(
        blank=True,
        help_text="Liste des pièces remplacées"
    )
    
    # Coûts
    cout_main_oeuvre = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Coût de la main d'œuvre (en FCFA)"
    )
    cout_pieces = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Coût des pièces (en FCFA)"
    )
    
    # Observations
    observations = models.TextField(
        blank=True,
        help_text="Observations diverses"
    )
    
    class Meta:
        db_table = 'maintenances'
        verbose_name = 'Maintenance'
        verbose_name_plural = 'Maintenances'
        ordering = ['-date_planifiee']
        indexes = [
            models.Index(fields=['equipement', 'date_planifiee']),
            models.Index(fields=['type_maintenance']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"Maintenance {self.get_type_maintenance_display()} - {self.equipement.nom} ({self.date_planifiee})"
    
    def demarrer(self):
        """
        Démarre la maintenance.
        
        Change l'état de l'équipement en EN_MAINTENANCE.
        """
        from django.utils import timezone
        
        self.statut = self.StatutMaintenance.EN_COURS
        self.date_debut = timezone.now()
        self.save()
        
        # Changer l'état de l'équipement
        self.equipement.changer_etat('EN_MAINTENANCE')
    
    def terminer(self, travaux, pieces='', observations=''):
        """
        Termine la maintenance.
        
        Args:
            travaux (str): Travaux effectués
            pieces (str): Pièces remplacées
            observations (str): Observations
        """
        from django.utils import timezone
        
        self.statut = self.StatutMaintenance.TERMINEE
        self.date_fin = timezone.now()
        self.travaux_effectues = travaux
        self.pieces_remplacees = pieces
        self.observations = observations
        self.save()
        
        # Remettre l'équipement disponible
        self.equipement.changer_etat('DISPONIBLE')
        
        # Mettre à jour la date de dernier entretien
        self.equipement.dernier_entretien = self.date_fin.date()
        self.equipement.save()
    
    def annuler(self):
        """
        Annule la maintenance.
        """
        self.statut = self.StatutMaintenance.ANNULEE
        self.save()
    
    def calculer_cout_total(self):
        """
        Calcule le coût total de la maintenance.
        
        Returns:
            Decimal: Coût total (main d'œuvre + pièces)
        """
        main_oeuvre = self.cout_main_oeuvre or Decimal('0.00')
        pieces = self.cout_pieces or Decimal('0.00')
        return main_oeuvre + pieces
