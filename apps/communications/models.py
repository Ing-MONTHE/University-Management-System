from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel, User

# MODÈLE : ANNONCE
class Annonce(BaseModel):
    """
    Représente une annonce ou actualité de l'université.
    
    Les annonces sont des communications officielles diffusées
    à tous les utilisateurs ou à des groupes spécifiques.
    
    Types d'annonces :
    - GENERALE : Annonce pour tout le monde
    - ETUDIANTS : Seulement pour les étudiants
    - ENSEIGNANTS : Seulement pour les enseignants
    - ADMINISTRATION : Seulement pour l'administration
    - URGENTE : Annonce urgente (priorité haute)
    
    Relations :
    - Créée par un utilisateur (auteur)
    """
    
    # Choix de types d'annonces
    class TypeAnnonce(models.TextChoices):
        """
        Types d'annonces selon le public cible.
        
        - GENERALE : Tout le monde
        - ETUDIANTS : Étudiants uniquement
        - ENSEIGNANTS : Enseignants uniquement
        - ADMINISTRATION : Personnel administratif
        - URGENTE : Annonce urgente (alerte)
        """
        GENERALE = 'GENERALE', 'Générale'
        ETUDIANTS = 'ETUDIANTS', 'Étudiants'
        ENSEIGNANTS = 'ENSEIGNANTS', 'Enseignants'
        ADMINISTRATION = 'ADMINISTRATION', 'Administration'
        URGENTE = 'URGENTE', 'Urgente'
    
    # Choix de statuts
    class StatutAnnonce(models.TextChoices):
        """
        Statuts de publication de l'annonce.
        
        - BROUILLON : Annonce en cours de rédaction
        - PUBLIEE : Annonce publiée et visible
        - ARCHIVEE : Annonce archivée (non visible)
        """
        BROUILLON = 'BROUILLON', 'Brouillon'
        PUBLIEE = 'PUBLIEE', 'Publiée'
        ARCHIVEE = 'ARCHIVEE', 'Archivée'
    
    # Auteur
    auteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='annonces',
        help_text="Utilisateur qui a créé l'annonce"
    )
    
    # Contenu
    titre = models.CharField(
        max_length=200,
        help_text="Titre de l'annonce"
    )
    contenu = models.TextField(
        help_text="Contenu complet de l'annonce"
    )
    
    # Type et priorité
    type_annonce = models.CharField(
        max_length=20,
        choices=TypeAnnonce.choices,
        default=TypeAnnonce.GENERALE,
        help_text="Public cible de l'annonce"
    )
    est_prioritaire = models.BooleanField(
        default=False,
        help_text="True si l'annonce doit être mise en avant"
    )
    
    # Publication
    statut = models.CharField(
        max_length=20,
        choices=StatutAnnonce.choices,
        default=StatutAnnonce.BROUILLON,
        help_text="Statut de publication"
    )
    date_publication = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de publication"
    )
    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date d'expiration de l'annonce (optionnel)"
    )
    
    # Pièce jointe (optionnel)
    piece_jointe = models.FileField(
        upload_to='annonces/%Y/%m/',
        null=True,
        blank=True,
        help_text="Document joint à l'annonce (PDF, image, etc.)"
    )
    
    class Meta:
        db_table = 'annonces'
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'
        ordering = ['-date_publication', '-created_at']
        indexes = [
            models.Index(fields=['type_annonce']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_publication']),
        ]
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_annonce_display()})"
    
    def publier(self):
        """
        Publie l'annonce.
        
        Change le statut à PUBLIEE et enregistre la date de publication.
        """
        from django.utils import timezone
        
        self.statut = self.StatutAnnonce.PUBLIEE
        self.date_publication = timezone.now()
        self.save()
    
    def archiver(self):
        """
        Archive l'annonce (la rend invisible).
        """
        self.statut = self.StatutAnnonce.ARCHIVEE
        self.save()
    
    def est_expiree(self):
        """
        Vérifie si l'annonce a expiré.
        
        Returns:
            bool: True si expirée, False sinon
        """
        from django.utils import timezone
        
        if not self.date_expiration:
            return False
        
        return timezone.now() > self.date_expiration

# MODÈLE : NOTIFICATION
class Notification(BaseModel):
    """
    Représente une notification envoyée à un utilisateur.
    
    Les notifications sont des messages courts envoyés automatiquement
    ou manuellement pour informer les utilisateurs d'événements.
    
    Types de notifications :
    - INFO : Information générale
    - SUCCES : Confirmation d'action réussie
    - ALERTE : Alerte importante
    - ERREUR : Erreur à corriger
    
    Canaux de notification :
    - APP : Notification dans l'application (push)
    - EMAIL : Notification par email
    - SMS : Notification par SMS
    
    Relations :
    - Liée à un utilisateur destinataire
    """
    
    # Choix de types de notifications
    class TypeNotification(models.TextChoices):
        """
        Types de notifications selon l'importance.
        
        - INFO : Information standard
        - SUCCES : Confirmation (action réussie)
        - ALERTE : Avertissement important
        - ERREUR : Problème à résoudre
        """
        INFO = 'INFO', 'Information'
        SUCCES = 'SUCCES', 'Succès'
        ALERTE = 'ALERTE', 'Alerte'
        ERREUR = 'ERREUR', 'Erreur'
    
    # Choix de canaux
    class CanalNotification(models.TextChoices):
        """
        Canaux de diffusion de la notification.
        
        - APP : Notification dans l'application (push)
        - EMAIL : Notification par email
        - SMS : Notification par SMS
        """
        APP = 'APP', 'Application'
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
    
    # Destinataire
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Utilisateur destinataire de la notification"
    )
    
    # Contenu
    titre = models.CharField(
        max_length=200,
        help_text="Titre court de la notification"
    )
    message = models.TextField(
        help_text="Message complet de la notification"
    )
    
    # Type et canal
    type_notification = models.CharField(
        max_length=20,
        choices=TypeNotification.choices,
        default=TypeNotification.INFO,
        help_text="Type de notification"
    )
    canal = models.CharField(
        max_length=20,
        choices=CanalNotification.choices,
        default=CanalNotification.APP,
        help_text="Canal de diffusion"
    )
    
    # Statut de lecture
    est_lue = models.BooleanField(
        default=False,
        help_text="True si la notification a été lue"
    )
    date_lecture = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de lecture"
    )
    
    # Lien optionnel (pour redirection)
    lien = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL de redirection (optionnel)"
    )
    
    # Métadonnées pour l'envoi
    envoyee = models.BooleanField(
        default=False,
        help_text="True si la notification a été envoyée"
    )
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure d'envoi"
    )
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['destinataire', 'est_lue']),
            models.Index(fields=['type_notification']),
            models.Index(fields=['canal']),
        ]
    
    def __str__(self):
        return f"{self.titre} → {self.destinataire.username}"
    
    def marquer_comme_lue(self):
        """
        Marque la notification comme lue.
        
        Enregistre la date de lecture.
        """
        from django.utils import timezone
        
        if not self.est_lue:
            self.est_lue = True
            self.date_lecture = timezone.now()
            self.save()
    
    def marquer_comme_envoyee(self):
        """
        Marque la notification comme envoyée.
        
        Enregistre la date d'envoi.
        """
        from django.utils import timezone
        
        if not self.envoyee:
            self.envoyee = True
            self.date_envoi = timezone.now()
            self.save()

# MODÈLE : MESSAGE
class Message(BaseModel):
    """
    Représente un message dans la messagerie interne.
    
    Les messages permettent aux utilisateurs de communiquer
    entre eux de manière privée (messagerie interne).
    
    Fonctionnalités :
    - Envoi de messages entre utilisateurs
    - Réponses et fils de discussion
    - Marquage lu/non lu
    - Archivage
    - Pièces jointes
    
    Relations :
    - Expéditeur (User)
    - Destinataire (User)
    - Message parent (pour les réponses)
    """
    
    # Expéditeur et destinataire
    expediteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages_envoyes',
        help_text="Utilisateur qui a envoyé le message"
    )
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_recus',
        help_text="Utilisateur qui reçoit le message"
    )
    
    # Contenu
    sujet = models.CharField(
        max_length=200,
        help_text="Sujet du message"
    )
    corps = models.TextField(
        help_text="Corps du message"
    )
    
    # Pièce jointe (optionnel)
    piece_jointe = models.FileField(
        upload_to='messages/%Y/%m/',
        null=True,
        blank=True,
        help_text="Document joint au message"
    )
    
    # Fil de discussion (pour les réponses)
    message_parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reponses',
        help_text="Message parent (si c'est une réponse)"
    )
    
    # Statut de lecture
    est_lu = models.BooleanField(
        default=False,
        help_text="True si le message a été lu par le destinataire"
    )
    date_lecture = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de lecture"
    )
    
    # Archivage
    est_archive = models.BooleanField(
        default=False,
        help_text="True si le message est archivé"
    )
    
    class Meta:
        db_table = 'messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expediteur', 'destinataire']),
            models.Index(fields=['destinataire', 'est_lu']),
            models.Index(fields=['message_parent']),
        ]
    
    def __str__(self):
        return f"{self.sujet} ({self.expediteur} → {self.destinataire})"
    
    def marquer_comme_lu(self):
        """
        Marque le message comme lu.
        
        Enregistre la date de lecture.
        """
        from django.utils import timezone
        
        if not self.est_lu:
            self.est_lu = True
            self.date_lecture = timezone.now()
            self.save()
    
    def archiver(self):
        """
        Archive le message.
        """
        self.est_archive = True
        self.save()
    
    def desarchivier(self):
        """
        Désarchive le message.
        """
        self.est_archive = False
        self.save()
    
    def est_reponse(self):
        """
        Vérifie si ce message est une réponse à un autre message.
        
        Returns:
            bool: True si c'est une réponse, False sinon
        """
        return self.message_parent is not None

# MODÈLE : PRÉFÉRENCE NOTIFICATION
class PreferenceNotification(BaseModel):
    """
    Stocke les préférences de notification d'un utilisateur.
    
    Permet aux utilisateurs de personnaliser les types de notifications
    qu'ils souhaitent recevoir et par quels canaux.
    
    Exemples de préférences :
    - Recevoir les notifications de notes par email
    - Recevoir les alertes de paiement par SMS
    - Désactiver les notifications d'absences
    
    Relations :
    - Liée à un utilisateur (OneToOne)
    """
    
    # Utilisateur
    utilisateur = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preference_notification',
        help_text="Utilisateur concerné"
    )
    
    # Préférences par type d'événement
    notif_notes = models.BooleanField(
        default=True,
        help_text="Activer les notifications de nouvelles notes"
    )
    notif_absences = models.BooleanField(
        default=True,
        help_text="Activer les notifications d'absences"
    )
    notif_paiements = models.BooleanField(
        default=True,
        help_text="Activer les notifications de paiements"
    )
    notif_bibliotheque = models.BooleanField(
        default=True,
        help_text="Activer les notifications de bibliothèque (retours)"
    )
    notif_emploi_temps = models.BooleanField(
        default=True,
        help_text="Activer les notifications d'emploi du temps"
    )
    notif_annonces = models.BooleanField(
        default=True,
        help_text="Activer les notifications d'annonces"
    )
    notif_messages = models.BooleanField(
        default=True,
        help_text="Activer les notifications de nouveaux messages"
    )
    
    # Préférences par canal
    activer_email = models.BooleanField(
        default=True,
        help_text="Activer les notifications par email"
    )
    activer_sms = models.BooleanField(
        default=False,
        help_text="Activer les notifications par SMS"
    )
    activer_push = models.BooleanField(
        default=True,
        help_text="Activer les notifications push (application)"
    )
    
    # Paramètres avancés
    frequence_digest = models.CharField(
        max_length=20,
        choices=[
            ('IMMEDIAT', 'Immédiat'),
            ('QUOTIDIEN', 'Digest quotidien'),
            ('HEBDOMADAIRE', 'Digest hebdomadaire'),
        ],
        default='IMMEDIAT',
        help_text="Fréquence d'envoi des notifications par email"
    )
    
    class Meta:
        db_table = 'preferences_notification'
        verbose_name = 'Préférence de notification'
        verbose_name_plural = 'Préférences de notification'
    
    def __str__(self):
        return f"Préférences de {self.utilisateur.username}"
    
    def doit_notifier(self, type_evenement, canal):
        """
        Vérifie si l'utilisateur doit recevoir une notification.
        
        Args:
            type_evenement (str): Type d'événement (notes, absences, etc.)
            canal (str): Canal de notification (email, sms, push)
        
        Returns:
            bool: True si la notification doit être envoyée
        """
        # Vérifier si le type d'événement est activé
        type_actif = getattr(self, f'notif_{type_evenement}', True)
        
        # Vérifier si le canal est activé
        canal_actif = getattr(self, f'activer_{canal}', True)
        
        return type_actif and canal_actif
    