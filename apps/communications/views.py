from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone

from .models import Annonce, Notification, Message, PreferenceNotification
from .serializers import (
    AnnonceListSerializer,
    AnnonceDetailSerializer,
    AnnonceCreateSerializer,
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationCreateSerializer,
    NotificationMasseSerializer,
    MessageListSerializer,
    MessageDetailSerializer,
    MessageCreateSerializer,
    PreferenceNotificationSerializer,
    PreferenceNotificationUpdateSerializer,
    StatistiquesUtilisateurSerializer,
)
from apps.core.models import User

# VIEWSET : ANNONCES
class AnnonceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les annonces et actualités.
    
    Endpoints générés automatiquement :
    - GET /annonces/ : Liste toutes les annonces
    - POST /annonces/ : Crée une nouvelle annonce
    - GET /annonces/{id}/ : Détails d'une annonce
    - PUT /annonces/{id}/ : Mise à jour complète
    - PATCH /annonces/{id}/ : Mise à jour partielle
    - DELETE /annonces/{id}/ : Suppression
    
    Actions personnalisées :
    - POST /annonces/{id}/publier/ : Publier une annonce
    - POST /annonces/{id}/archiver/ : Archiver une annonce
    - GET /annonces/publiees/ : Annonces publiées et non expirées
    - GET /annonces/urgentes/ : Annonces urgentes
    - GET /annonces/par-type/ : Filtrer par type
    - GET /annonces/statistiques/ : Stats globales
    
    Filtres :
    - ?type_annonce=GENERALE : Par type
    - ?statut=PUBLIEE : Par statut
    - ?est_prioritaire=true : Seulement prioritaires
    
    Permissions : Authentification requise
    """
    queryset = Annonce.objects.select_related('auteur').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer approprié selon l'action.
        
        Returns:
            Serializer: Classe de serializer à utiliser
        """
        if self.action in ['create', 'update', 'partial_update']:
            return AnnonceCreateSerializer
        elif self.action == 'retrieve':
            return AnnonceDetailSerializer
        return AnnonceListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Paramètres de requête supportés :
        - type_annonce : Type d'annonce
        - statut : Statut de publication
        - est_prioritaire : true/false
        
        Returns:
            QuerySet: Annonces filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par type
        type_annonce = self.request.query_params.get('type_annonce')
        if type_annonce:
            queryset = queryset.filter(type_annonce=type_annonce)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par priorité
        est_prioritaire = self.request.query_params.get('est_prioritaire')
        if est_prioritaire is not None:
            queryset = queryset.filter(est_prioritaire=(est_prioritaire.lower() == 'true'))
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        """
        Action personnalisée : Publie une annonce.
        
        URL: POST /annonces/{id}/publier/
        
        Processus :
        1. Change le statut à PUBLIEE
        2. Enregistre la date de publication
        
        Returns:
            Response: Annonce publiée avec message
        """
        annonce = self.get_object()
        
        # Vérifier que l'annonce n'est pas déjà publiée
        if annonce.statut == 'PUBLIEE':
            return Response(
                {'error': 'Cette annonce est déjà publiée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Publier l'annonce (méthode du modèle)
        annonce.publier()
        
        serializer = AnnonceDetailSerializer(annonce)
        
        return Response({
            'message': 'Annonce publiée avec succès.',
            'annonce': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        """
        Action personnalisée : Archive une annonce.
        
        URL: POST /annonces/{id}/archiver/
        
        Returns:
            Response: Annonce archivée
        """
        annonce = self.get_object()
        
        # Archiver l'annonce (méthode du modèle)
        annonce.archiver()
        
        serializer = AnnonceDetailSerializer(annonce)
        
        return Response({
            'message': 'Annonce archivée avec succès.',
            'annonce': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def publiees(self, request):
        """
        Action personnalisée : Liste les annonces publiées et non expirées.
        
        URL: GET /annonces/publiees/
        
        Returns:
            Response: Liste des annonces publiées et valides
        """
        date_actuelle = timezone.now()
        
        annonces = self.get_queryset().filter(
            statut='PUBLIEE'
        ).filter(
            Q(date_expiration__isnull=True) | Q(date_expiration__gte=date_actuelle)
        )
        
        serializer = self.get_serializer(annonces, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgentes(self, request):
        """
        Action personnalisée : Liste les annonces urgentes.
        
        URL: GET /annonces/urgentes/
        
        Returns:
            Response: Annonces urgentes publiées
        """
        annonces = self.get_queryset().filter(
            type_annonce='URGENTE',
            statut='PUBLIEE'
        )
        
        serializer = self.get_serializer(annonces, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """
        Action personnalisée : Filtrer les annonces par type.
        
        URL: GET /annonces/par-type/?type={type}
        
        Returns:
            Response: Annonces du type spécifié
        """
        type_annonce = request.query_params.get('type')
        
        if not type_annonce:
            return Response(
                {'error': 'Le paramètre type est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        annonces = self.get_queryset().filter(
            type_annonce=type_annonce,
            statut='PUBLIEE'
        )
        
        serializer = self.get_serializer(annonces, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des annonces.
        
        URL: GET /annonces/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = Annonce.objects.count()
        publiees = Annonce.objects.filter(statut='PUBLIEE').count()
        brouillons = Annonce.objects.filter(statut='BROUILLON').count()
        archivees = Annonce.objects.filter(statut='ARCHIVEE').count()
        urgentes = Annonce.objects.filter(type_annonce='URGENTE', statut='PUBLIEE').count()
        
        # Répartition par type
        par_type = Annonce.objects.filter(statut='PUBLIEE').values('type_annonce').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_annonces': total,
            'publiees': publiees,
            'brouillons': brouillons,
            'archivees': archivees,
            'urgentes': urgentes,
            'repartition_par_type': list(par_type),
        })

# VIEWSET : NOTIFICATIONS
class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les notifications.
    
    Endpoints :
    - GET /notifications/ : Liste toutes les notifications
    - POST /notifications/ : Crée une nouvelle notification
    - GET /notifications/{id}/ : Détails d'une notification
    - PUT/PATCH /notifications/{id}/ : Modifier une notification
    - DELETE /notifications/{id}/ : Supprimer une notification
    
    Actions personnalisées :
    - POST /notifications/{id}/marquer-lue/ : Marquer comme lue
    - POST /notifications/marquer-toutes-lues/ : Marquer toutes comme lues
    - POST /notifications/envoyer-masse/ : Envoyer à plusieurs utilisateurs
    - GET /notifications/non-lues/ : Notifications non lues
    - GET /notifications/mes-notifications/ : Notifications de l'utilisateur connecté
    - GET /notifications/statistiques/ : Stats globales
    
    Filtres :
    - ?destinataire={id} : Par destinataire
    - ?type_notification=ALERTE : Par type
    - ?canal=EMAIL : Par canal
    - ?est_lue=false : Seulement non lues
    """
    queryset = Notification.objects.select_related('destinataire').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action == 'create':
            return NotificationCreateSerializer
        elif self.action == 'envoyer_masse':
            return NotificationMasseSerializer
        elif self.action == 'retrieve':
            return NotificationDetailSerializer
        return NotificationListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Notifications filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par destinataire
        destinataire_id = self.request.query_params.get('destinataire')
        if destinataire_id:
            queryset = queryset.filter(destinataire_id=destinataire_id)
        
        # Filtre par type
        type_notif = self.request.query_params.get('type_notification')
        if type_notif:
            queryset = queryset.filter(type_notification=type_notif)
        
        # Filtre par canal
        canal = self.request.query_params.get('canal')
        if canal:
            queryset = queryset.filter(canal=canal)
        
        # Filtre par statut de lecture
        est_lue = self.request.query_params.get('est_lue')
        if est_lue is not None:
            queryset = queryset.filter(est_lue=(est_lue.lower() == 'true'))
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        """
        Action personnalisée : Marque une notification comme lue.
        
        URL: POST /notifications/{id}/marquer-lue/
        
        Returns:
            Response: Notification marquée comme lue
        """
        notification = self.get_object()
        
        # Marquer comme lue (méthode du modèle)
        notification.marquer_comme_lue()
        
        serializer = NotificationDetailSerializer(notification)
        
        return Response({
            'message': 'Notification marquée comme lue.',
            'notification': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def marquer_toutes_lues(self, request):
        """
        Action personnalisée : Marque toutes les notifications de l'utilisateur comme lues.
        
        URL: POST /notifications/marquer-toutes-lues/
        
        Returns:
            Response: Nombre de notifications marquées
        """
        # Récupérer toutes les notifications non lues de l'utilisateur
        notifications = Notification.objects.filter(
            destinataire=request.user,
            est_lue=False
        )
        
        count = 0
        for notif in notifications:
            notif.marquer_comme_lue()
            count += 1
        
        return Response({
            'message': f'{count} notification(s) marquée(s) comme lue(s).',
            'count': count
        })
    
    @action(detail=False, methods=['post'])
    def envoyer_masse(self, request):
        """
        Action personnalisée : Envoie une notification à plusieurs utilisateurs.
        
        URL: POST /notifications/envoyer-masse/
        Body: {
            "destinataires": [1, 2, 3],
            "titre": "Nouvelle note",
            "message": "Votre note est disponible",
            "type_notification": "INFO",
            "canal": "APP"
        }
        
        Returns:
            Response: Nombre de notifications créées
        """
        serializer = NotificationMasseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Créer une notification pour chaque destinataire
        notifications_creees = []
        for user_id in data['destinataires']:
            notification = Notification.objects.create(
                destinataire_id=user_id,
                titre=data['titre'],
                message=data['message'],
                type_notification=data['type_notification'],
                canal=data['canal'],
                lien=data.get('lien', '')
            )
            notifications_creees.append(notification)
        
        return Response({
            'message': f'{len(notifications_creees)} notification(s) créée(s) avec succès.',
            'count': len(notifications_creees)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """
        Action personnalisée : Liste les notifications non lues.
        
        URL: GET /notifications/non-lues/
        
        Returns:
            Response: Notifications non lues
        """
        notifications = self.get_queryset().filter(est_lue=False)
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'count': notifications.count(),
            'notifications': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def mes_notifications(self, request):
        """
        Action personnalisée : Liste les notifications de l'utilisateur connecté.
        
        URL: GET /notifications/mes-notifications/
        
        Returns:
            Response: Notifications de l'utilisateur
        """
        notifications = self.get_queryset().filter(destinataire=request.user)
        serializer = self.get_serializer(notifications, many=True)
        
        # Compter les non lues
        non_lues = notifications.filter(est_lue=False).count()
        
        return Response({
            'total': notifications.count(),
            'non_lues': non_lues,
            'notifications': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des notifications.
        
        URL: GET /notifications/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = Notification.objects.count()
        non_lues = Notification.objects.filter(est_lue=False).count()
        envoyees = Notification.objects.filter(envoyee=True).count()
        
        # Répartition par type
        par_type = Notification.objects.values('type_notification').annotate(
            count=Count('id')
        )
        
        # Répartition par canal
        par_canal = Notification.objects.values('canal').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_notifications': total,
            'non_lues': non_lues,
            'envoyees': envoyees,
            'repartition_par_type': list(par_type),
            'repartition_par_canal': list(par_canal),
        })

# VIEWSET : MESSAGES
class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer la messagerie interne.
    
    Endpoints :
    - GET /messages/ : Liste tous les messages
    - POST /messages/ : Envoie un nouveau message
    - GET /messages/{id}/ : Détails d'un message
    - PUT/PATCH /messages/{id}/ : Modifier un message
    - DELETE /messages/{id}/ : Supprimer un message
    
    Actions personnalisées :
    - POST /messages/{id}/marquer-lu/ : Marquer comme lu
    - POST /messages/{id}/archiver/ : Archiver le message
    - POST /messages/{id}/desarchivier/ : Désarchiver le message
    - POST /messages/{id}/repondre/ : Répondre au message
    - GET /messages/boite-reception/ : Messages reçus
    - GET /messages/messages-envoyes/ : Messages envoyés
    - GET /messages/non-lus/ : Messages non lus
    - GET /messages/archives/ : Messages archivés
    - GET /messages/conversation/ : Fil de discussion
    - GET /messages/statistiques/ : Stats globales
    
    Filtres :
    - ?expediteur={id} : Par expéditeur
    - ?destinataire={id} : Par destinataire
    - ?est_lu=false : Seulement non lus
    - ?est_archive=true : Seulement archivés
    """
    queryset = Message.objects.select_related('expediteur', 'destinataire', 'message_parent').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action == 'create':
            return MessageCreateSerializer
        elif self.action == 'retrieve':
            return MessageDetailSerializer
        return MessageListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Messages filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par expéditeur
        expediteur_id = self.request.query_params.get('expediteur')
        if expediteur_id:
            queryset = queryset.filter(expediteur_id=expediteur_id)
        
        # Filtre par destinataire
        destinataire_id = self.request.query_params.get('destinataire')
        if destinataire_id:
            queryset = queryset.filter(destinataire_id=destinataire_id)
        
        # Filtre par statut de lecture
        est_lu = self.request.query_params.get('est_lu')
        if est_lu is not None:
            queryset = queryset.filter(est_lu=(est_lu.lower() == 'true'))
        
        # Filtre par archivage
        est_archive = self.request.query_params.get('est_archive')
        if est_archive is not None:
            queryset = queryset.filter(est_archive=(est_archive.lower() == 'true'))
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def marquer_lu(self, request, pk=None):
        """
        Action personnalisée : Marque un message comme lu.
        
        URL: POST /messages/{id}/marquer-lu/
        
        Returns:
            Response: Message marqué comme lu
        """
        message = self.get_object()
        
        # Vérifier que c'est le destinataire qui marque comme lu
        if message.destinataire != request.user:
            return Response(
                {'error': 'Vous ne pouvez marquer comme lu que vos propres messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Marquer comme lu (méthode du modèle)
        message.marquer_comme_lu()
        
        serializer = MessageDetailSerializer(message)
        
        return Response({
            'message_text': 'Message marqué comme lu.',
            'message': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        """
        Action personnalisée : Archive un message.
        
        URL: POST /messages/{id}/archiver/
        
        Returns:
            Response: Message archivé
        """
        message = self.get_object()
        
        # Archiver (méthode du modèle)
        message.archiver()
        
        serializer = MessageDetailSerializer(message)
        
        return Response({
            'message_text': 'Message archivé avec succès.',
            'message': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def desarchivier(self, request, pk=None):
        """
        Action personnalisée : Désarchive un message.
        
        URL: POST /messages/{id}/desarchivier/
        
        Returns:
            Response: Message désarchivé
        """
        message = self.get_object()
        
        # Désarchiver (méthode du modèle)
        message.desarchivier()
        
        serializer = MessageDetailSerializer(message)
        
        return Response({
            'message_text': 'Message désarchivé avec succès.',
            'message': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def repondre(self, request, pk=None):
        """
        Action personnalisée : Répond à un message.
        
        URL: POST /messages/{id}/repondre/
        Body: {
            "corps": "Contenu de la réponse",
            "piece_jointe": (optionnel)
        }
        
        Returns:
            Response: Message de réponse créé
        """
        message_parent = self.get_object()
        
        # Créer la réponse
        serializer = MessageCreateSerializer(
            data={
                'destinataire': message_parent.expediteur.id,
                'sujet': f"Re: {message_parent.sujet}",
                'corps': request.data.get('corps'),
                'message_parent': message_parent.id
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            reponse = serializer.save()
            detail_serializer = MessageDetailSerializer(reponse)
            
            return Response({
                'message_text': 'Réponse envoyée avec succès.',
                'message': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def boite_reception(self, request):
        """
        Action personnalisée : Boîte de réception de l'utilisateur.
        
        URL: GET /messages/boite-reception/
        
        Returns:
            Response: Messages reçus par l'utilisateur
        """
        messages = self.get_queryset().filter(
            destinataire=request.user,
            est_archive=False
        )
        
        serializer = self.get_serializer(messages, many=True)
        
        # Compter les non lus
        non_lus = messages.filter(est_lu=False).count()
        
        return Response({
            'total': messages.count(),
            'non_lus': non_lus,
            'messages': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def messages_envoyes(self, request):
        """
        Action personnalisée : Messages envoyés par l'utilisateur.
        
        URL: GET /messages/messages-envoyes/
        
        Returns:
            Response: Messages envoyés
        """
        messages = self.get_queryset().filter(expediteur=request.user)
        serializer = self.get_serializer(messages, many=True)
        
        return Response({
            'total': messages.count(),
            'messages': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def non_lus(self, request):
        """
        Action personnalisée : Messages non lus de l'utilisateur.
        
        URL: GET /messages/non-lus/
        
        Returns:
            Response: Messages non lus
        """
        messages = self.get_queryset().filter(
            destinataire=request.user,
            est_lu=False
        )
        
        serializer = self.get_serializer(messages, many=True)
        
        return Response({
            'count': messages.count(),
            'messages': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def archives(self, request):
        """
        Action personnalisée : Messages archivés de l'utilisateur.
        
        URL: GET /messages/archives/
        
        Returns:
            Response: Messages archivés
        """
        messages = self.get_queryset().filter(
            Q(expediteur=request.user) | Q(destinataire=request.user),
            est_archive=True
        )
        
        serializer = self.get_serializer(messages, many=True)
        
        return Response({
            'count': messages.count(),
            'messages': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def conversation(self, request):
        """
        Action personnalisée : Récupère un fil de conversation.
        
        URL: GET /messages/conversation/?message_id={id}
        
        Returns:
            Response: Fil complet de la conversation
        """
        message_id = request.query_params.get('message_id')
        
        if not message_id:
            return Response(
                {'error': 'Le paramètre message_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remonter au message racine
        racine = message
        while racine.message_parent:
            racine = racine.message_parent
        
        # Récupérer tous les messages du fil
        conversation = [racine]
        
        def get_reponses(msg):
            """Récupère récursivement toutes les réponses."""
            reponses = msg.reponses.all()
            for reponse in reponses:
                conversation.append(reponse)
                get_reponses(reponse)
        
        get_reponses(racine)
        
        serializer = MessageDetailSerializer(conversation, many=True)
        
        return Response({
            'count': len(conversation),
            'conversation': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques des messages de l'utilisateur.
        
        URL: GET /messages/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        # Messages reçus
        messages_recus = Message.objects.filter(destinataire=request.user).count()
        non_lus = Message.objects.filter(destinataire=request.user, est_lu=False).count()
        
        # Messages envoyés
        messages_envoyes = Message.objects.filter(expediteur=request.user).count()
        
        # Messages archivés
        archives = Message.objects.filter(
            Q(expediteur=request.user) | Q(destinataire=request.user),
            est_archive=True
        ).count()
        
        return Response({
            'messages_recus': messages_recus,
            'messages_non_lus': non_lus,
            'messages_envoyes': messages_envoyes,
            'messages_archives': archives,
        })

# VIEWSET : PRÉFÉRENCES NOTIFICATION
class PreferenceNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les préférences de notification.
    
    Endpoints :
    - GET /preferences/ : Liste toutes les préférences
    - POST /preferences/ : Crée de nouvelles préférences
    - GET /preferences/{id}/ : Détails des préférences
    - PUT/PATCH /preferences/{id}/ : Modifier les préférences
    - DELETE /preferences/{id}/ : Supprimer les préférences
    
    Actions personnalisées :
    - GET /preferences/mes-preferences/ : Préférences de l'utilisateur connecté
    - PATCH /preferences/mes-preferences/mettre-a-jour/ : Met à jour les préférences
    
    Permissions : Authentification requise
    """
    queryset = PreferenceNotification.objects.select_related('utilisateur').all()
    permission_classes = [IsAuthenticated]
    serializer_class = PreferenceNotificationSerializer
    
    @action(detail=False, methods=['get'])
    def mes_preferences(self, request):
        """
        Action personnalisée : Récupère les préférences de l'utilisateur connecté.
        
        URL: GET /preferences/mes-preferences/
        
        Crée automatiquement les préférences si elles n'existent pas.
        
        Returns:
            Response: Préférences de l'utilisateur
        """
        # Récupérer ou créer les préférences
        preference, created = PreferenceNotification.objects.get_or_create(
            utilisateur=request.user
        )
        
        serializer = PreferenceNotificationSerializer(preference)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def mettre_a_jour(self, request):
        """
        Action personnalisée : Met à jour les préférences de l'utilisateur.
        
        URL: PATCH /preferences/mettre-a-jour/
        
        Returns:
            Response: Préférences mises à jour
        """
        # Récupérer ou créer les préférences
        preference, created = PreferenceNotification.objects.get_or_create(
            utilisateur=request.user
        )
        
        serializer = PreferenceNotificationUpdateSerializer(
            preference,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Retourner les préférences complètes
            result_serializer = PreferenceNotificationSerializer(preference)
            
            return Response({
                'message': 'Préférences mises à jour avec succès.',
                'preferences': result_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# VIEWSET : STATISTIQUES GLOBALES
class StatistiquesViewSet(viewsets.ViewSet):
    """
    ViewSet pour les statistiques globales de communication.
    
    Actions :
    - GET /statistiques/utilisateur/ : Stats de l'utilisateur connecté
    - GET /statistiques/globales/ : Stats système globales
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def utilisateur(self, request):
        """
        Action personnalisée : Statistiques de l'utilisateur connecté.
        
        URL: GET /statistiques/utilisateur/
        
        Returns:
            Response: Stats complètes de l'utilisateur
        """
        user = request.user
        
        # Notifications
        notif_non_lues = Notification.objects.filter(
            destinataire=user,
            est_lue=False
        ).count()
        
        notif_totales = Notification.objects.filter(destinataire=user).count()
        
        # Messages
        msg_non_lus = Message.objects.filter(
            destinataire=user,
            est_lu=False
        ).count()
        
        msg_recus = Message.objects.filter(destinataire=user).count()
        msg_envoyes = Message.objects.filter(expediteur=user).count()
        
        data = {
            'notifications_non_lues': notif_non_lues,
            'total_notifications': notif_totales,
            'messages_non_lus': msg_non_lus,
            'total_messages_recus': msg_recus,
            'total_messages_envoyes': msg_envoyes,
        }
        
        serializer = StatistiquesUtilisateurSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def globales(self, request):
        """
        Action personnalisée : Statistiques globales du système.
        
        URL: GET /statistiques/globales/
        
        Returns:
            Response: Stats système complètes
        """
        # Annonces
        total_annonces = Annonce.objects.count()
        annonces_publiees = Annonce.objects.filter(statut='PUBLIEE').count()
        
        # Notifications
        total_notifications = Notification.objects.count()
        notif_non_lues = Notification.objects.filter(est_lue=False).count()
        
        # Messages
        total_messages = Message.objects.count()
        msg_non_lus = Message.objects.filter(est_lu=False).count()
        
        # Utilisateurs avec préférences
        users_avec_prefs = PreferenceNotification.objects.count()
        
        return Response({
            'annonces': {
                'total': total_annonces,
                'publiees': annonces_publiees,
            },
            'notifications': {
                'total': total_notifications,
                'non_lues': notif_non_lues,
            },
            'messages': {
                'total': total_messages,
                'non_lus': msg_non_lus,
            },
            'utilisateurs_avec_preferences': users_avec_prefs,
        })
