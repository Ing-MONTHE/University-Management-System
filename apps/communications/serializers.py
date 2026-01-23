from rest_framework import serializers
from django.utils import timezone
from .models import Annonce, Notification, Message, PreferenceNotification
from apps.core.models import User

# SERIALIZER : ANNONCE (LISTE)
class AnnonceListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des annonces (vue simplifiée).
    
    Affiche les informations essentielles pour les listes.
    Inclut le nom de l'auteur et vérifie l'expiration.
    """
    auteur_nom = serializers.SerializerMethodField()
    est_expiree = serializers.SerializerMethodField()
    
    class Meta:
        model = Annonce
        fields = [
            'id',
            'auteur',
            'auteur_nom',
            'titre',
            'type_annonce',
            'est_prioritaire',
            'statut',
            'date_publication',
            'date_expiration',
            'est_expiree',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_auteur_nom(self, obj):
        """
        Retourne le nom complet de l'auteur.
        
        Returns:
            str: Nom complet ou "Système"
        """
        if obj.auteur:
            return f"{obj.auteur.first_name} {obj.auteur.last_name}"
        return "Système"
    
    def get_est_expiree(self, obj):
        """
        Vérifie si l'annonce a expiré.
        
        Returns:
            bool: True si expirée
        """
        return obj.est_expiree()

# SERIALIZER : ANNONCE (DÉTAIL)
class AnnonceDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'une annonce.
    
    Inclut toutes les informations + URL de la pièce jointe.
    """
    auteur_nom = serializers.SerializerMethodField()
    est_expiree = serializers.SerializerMethodField()
    piece_jointe_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Annonce
        fields = [
            'id',
            'auteur',
            'auteur_nom',
            'titre',
            'contenu',
            'type_annonce',
            'est_prioritaire',
            'statut',
            'date_publication',
            'date_expiration',
            'est_expiree',
            'piece_jointe',
            'piece_jointe_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_auteur_nom(self, obj):
        if obj.auteur:
            return f"{obj.auteur.first_name} {obj.auteur.last_name}"
        return "Système"
    
    def get_est_expiree(self, obj):
        return obj.est_expiree()
    
    def get_piece_jointe_url(self, obj):
        """
        Retourne l'URL complète de la pièce jointe.
        
        Returns:
            str: URL du fichier ou None
        """
        if obj.piece_jointe:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.piece_jointe.url)
            return obj.piece_jointe.url
        return None

# SERIALIZER : CRÉATION ANNONCE
class AnnonceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une nouvelle annonce.
    
    Valide que :
    1. Le titre n'est pas vide
    2. Si date d'expiration, elle est dans le futur
    """
    
    class Meta:
        model = Annonce
        fields = [
            'titre',
            'contenu',
            'type_annonce',
            'est_prioritaire',
            'date_expiration',
            'piece_jointe',
        ]
    
    def validate_date_expiration(self, value):
        """
        Valide que la date d'expiration est dans le futur.
        
        Args:
            value (datetime): Date d'expiration
        
        Raises:
            ValidationError: Si la date est dans le passé
        
        Returns:
            datetime: Date validée
        """
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "La date d'expiration doit être dans le futur."
            )
        return value
    
    def create(self, validated_data):
        """
        Crée l'annonce avec l'auteur automatiquement défini.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            Annonce: Instance créée
        """
        # Récupérer l'utilisateur depuis le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['auteur'] = request.user
        
        return Annonce.objects.create(**validated_data)

# SERIALIZER : NOTIFICATION (LISTE)
class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des notifications (vue simplifiée).
    
    Affiche les informations essentielles.
    """
    destinataire_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'destinataire',
            'destinataire_nom',
            'titre',
            'type_notification',
            'canal',
            'est_lue',
            'date_lecture',
            'envoyee',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_destinataire_nom(self, obj):
        """Retourne le nom du destinataire."""
        return f"{obj.destinataire.first_name} {obj.destinataire.last_name}"

# SERIALIZER : NOTIFICATION (DÉTAIL)
class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'une notification.
    
    Inclut toutes les informations.
    """
    destinataire_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'destinataire',
            'destinataire_nom',
            'titre',
            'message',
            'type_notification',
            'canal',
            'est_lue',
            'date_lecture',
            'lien',
            'envoyee',
            'date_envoi',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_destinataire_nom(self, obj):
        return f"{obj.destinataire.first_name} {obj.destinataire.last_name}"

# SERIALIZER : CRÉATION NOTIFICATION
class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une nouvelle notification.
    
    Permet de créer manuellement une notification.
    """
    
    class Meta:
        model = Notification
        fields = [
            'destinataire',
            'titre',
            'message',
            'type_notification',
            'canal',
            'lien',
        ]
    
    def create(self, validated_data):
        """
        Crée la notification.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            Notification: Instance créée
        """
        return Notification.objects.create(**validated_data)

# SERIALIZER : NOTIFICATION EN MASSE
class NotificationMasseSerializer(serializers.Serializer):
    """
    Serializer pour envoyer des notifications en masse.
    
    Permet d'envoyer la même notification à plusieurs utilisateurs.
    
    Format :
    {
        "destinataires": [1, 2, 3],  # IDs des utilisateurs
        "titre": "Nouvelle note disponible",
        "message": "Votre note de mathématiques est disponible",
        "type_notification": "INFO",
        "canal": "APP",
        "lien": "/notes"
    }
    """
    destinataires = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Liste des IDs des utilisateurs destinataires"
    )
    titre = serializers.CharField(max_length=200)
    message = serializers.TextField()
    type_notification = serializers.ChoiceField(
        choices=Notification.TypeNotification.choices,
        default='INFO'
    )
    canal = serializers.ChoiceField(
        choices=Notification.CanalNotification.choices,
        default='APP'
    )
    lien = serializers.CharField(required=False, allow_blank=True)
    
    def validate_destinataires(self, value):
        """
        Valide que tous les destinataires existent.
        
        Args:
            value (list): Liste des IDs
        
        Raises:
            ValidationError: Si un ID n'existe pas
        
        Returns:
            list: IDs validés
        """
        if not value:
            raise serializers.ValidationError("La liste des destinataires ne peut pas être vide.")
        
        # Vérifier que tous les IDs existent
        users_count = User.objects.filter(id__in=value).count()
        if users_count != len(value):
            raise serializers.ValidationError("Certains destinataires n'existent pas.")
        
        return value

# SERIALIZER : MESSAGE (LISTE)
class MessageListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des messages (vue simplifiée).
    
    Affiche les informations essentielles pour la boîte de réception.
    """
    expediteur_nom = serializers.SerializerMethodField()
    destinataire_nom = serializers.SerializerMethodField()
    est_reponse = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'expediteur',
            'expediteur_nom',
            'destinataire',
            'destinataire_nom',
            'sujet',
            'message_parent',
            'est_reponse',
            'est_lu',
            'date_lecture',
            'est_archive',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_expediteur_nom(self, obj):
        """Retourne le nom de l'expéditeur."""
        if obj.expediteur:
            return f"{obj.expediteur.first_name} {obj.expediteur.last_name}"
        return "Utilisateur supprimé"
    
    def get_destinataire_nom(self, obj):
        """Retourne le nom du destinataire."""
        return f"{obj.destinataire.first_name} {obj.destinataire.last_name}"
    
    def get_est_reponse(self, obj):
        """Vérifie si c'est une réponse."""
        return obj.est_reponse()

# SERIALIZER : MESSAGE (DÉTAIL)
class MessageDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un message.
    
    Inclut le corps complet, les pièces jointes et les réponses.
    """
    expediteur_nom = serializers.SerializerMethodField()
    destinataire_nom = serializers.SerializerMethodField()
    est_reponse = serializers.SerializerMethodField()
    piece_jointe_url = serializers.SerializerMethodField()
    nombre_reponses = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'expediteur',
            'expediteur_nom',
            'destinataire',
            'destinataire_nom',
            'sujet',
            'corps',
            'piece_jointe',
            'piece_jointe_url',
            'message_parent',
            'est_reponse',
            'nombre_reponses',
            'est_lu',
            'date_lecture',
            'est_archive',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_expediteur_nom(self, obj):
        if obj.expediteur:
            return f"{obj.expediteur.first_name} {obj.expediteur.last_name}"
        return "Utilisateur supprimé"
    
    def get_destinataire_nom(self, obj):
        return f"{obj.destinataire.first_name} {obj.destinataire.last_name}"
    
    def get_est_reponse(self, obj):
        return obj.est_reponse()
    
    def get_piece_jointe_url(self, obj):
        """Retourne l'URL de la pièce jointe."""
        if obj.piece_jointe:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.piece_jointe.url)
            return obj.piece_jointe.url
        return None
    
    def get_nombre_reponses(self, obj):
        """Compte le nombre de réponses à ce message."""
        return obj.reponses.count()

# SERIALIZER : CRÉATION MESSAGE
class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un nouveau message.
    
    Valide que l'expéditeur et le destinataire sont différents.
    """
    
    class Meta:
        model = Message
        fields = [
            'destinataire',
            'sujet',
            'corps',
            'piece_jointe',
            'message_parent',
        ]
    
    def validate(self, data):
        """
        Validation globale.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si expéditeur = destinataire
        
        Returns:
            dict: Données validées
        """
        # Récupérer l'expéditeur depuis le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            expediteur = request.user
            destinataire = data.get('destinataire')
            
            # Vérifier que l'expéditeur != destinataire
            if expediteur == destinataire:
                raise serializers.ValidationError(
                    "Vous ne pouvez pas vous envoyer un message à vous-même."
                )
        
        return data
    
    def create(self, validated_data):
        """
        Crée le message avec l'expéditeur automatiquement défini.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            Message: Instance créée
        """
        # Récupérer l'utilisateur depuis le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['expediteur'] = request.user
        
        return Message.objects.create(**validated_data)

# SERIALIZER : PRÉFÉRENCE NOTIFICATION
class PreferenceNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour les préférences de notification.
    
    Permet de consulter et modifier les préférences.
    """
    utilisateur_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = PreferenceNotification
        fields = [
            'id',
            'utilisateur',
            'utilisateur_nom',
            # Préférences par type
            'notif_notes',
            'notif_absences',
            'notif_paiements',
            'notif_bibliotheque',
            'notif_emploi_temps',
            'notif_annonces',
            'notif_messages',
            # Préférences par canal
            'activer_email',
            'activer_sms',
            'activer_push',
            # Paramètres avancés
            'frequence_digest',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'utilisateur', 'created_at', 'updated_at']
    
    def get_utilisateur_nom(self, obj):
        """Retourne le nom de l'utilisateur."""
        return f"{obj.utilisateur.first_name} {obj.utilisateur.last_name}"

# SERIALIZER : MISE À JOUR PRÉFÉRENCES
class PreferenceNotificationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mettre à jour les préférences de notification.
    
    Permet une mise à jour partielle des préférences.
    """
    
    class Meta:
        model = PreferenceNotification
        fields = [
            'notif_notes',
            'notif_absences',
            'notif_paiements',
            'notif_bibliotheque',
            'notif_emploi_temps',
            'notif_annonces',
            'notif_messages',
            'activer_email',
            'activer_sms',
            'activer_push',
            'frequence_digest',
        ]
    
    def update(self, instance, validated_data):
        """
        Met à jour les préférences.
        
        Args:
            instance (PreferenceNotification): Instance existante
            validated_data (dict): Nouvelles valeurs
        
        Returns:
            PreferenceNotification: Instance mise à jour
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

# SERIALIZER : STATISTIQUES UTILISATEUR
class StatistiquesUtilisateurSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques de communication d'un utilisateur.
    
    Retourne :
    - Nombre de notifications non lues
    - Nombre de messages non lus
    - Dernières notifications
    - Derniers messages
    """
    notifications_non_lues = serializers.IntegerField()
    messages_non_lus = serializers.IntegerField()
    total_notifications = serializers.IntegerField()
    total_messages_recus = serializers.IntegerField()
    total_messages_envoyes = serializers.IntegerField()
