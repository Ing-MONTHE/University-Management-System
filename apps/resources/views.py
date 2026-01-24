from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone

from .models import Equipement, Reservation, ReservationEquipement, Maintenance
from .serializers import (
    EquipementListSerializer,
    EquipementDetailSerializer,
    EquipementCreateSerializer,
    ReservationListSerializer,
    ReservationDetailSerializer,
    ReservationCreateSerializer,
    ReservationValidationSerializer,
    MaintenanceListSerializer,
    MaintenanceDetailSerializer,
    MaintenanceCreateSerializer,
    MaintenanceTerminaisonSerializer,
    RetourEquipementSerializer,
    DisponibiliteEquipementSerializer,
)

# VIEWSET : ÉQUIPEMENTS
class EquipementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les équipements.
    
    Endpoints générés automatiquement :
    - GET /equipements/ : Liste tous les équipements
    - POST /equipements/ : Crée un nouvel équipement
    - GET /equipements/{id}/ : Détails d'un équipement
    - PUT /equipements/{id}/ : Mise à jour complète
    - PATCH /equipements/{id}/ : Mise à jour partielle
    - DELETE /equipements/{id}/ : Suppression
    
    Actions personnalisées :
    - GET /equipements/disponibles/ : Équipements disponibles
    - GET /equipements/par-categorie/ : Filtrer par catégorie
    - GET /equipements/en-maintenance/ : Équipements en maintenance
    - GET /equipements/hors-service/ : Équipements hors service
    - POST /equipements/{id}/changer-etat/ : Changer l'état
    - GET /equipements/{id}/historique-maintenances/ : Historique des maintenances
    - POST /equipements/verifier-disponibilite/ : Vérifier disponibilité
    - GET /equipements/statistiques/ : Stats globales
    
    Filtres :
    - ?categorie=INFORMATIQUE : Par catégorie
    - ?etat=DISPONIBLE : Par état
    - ?salle={id} : Par salle
    - ?reservable=true : Seulement réservables
    
    Permissions : Authentification requise
    """
    queryset = Equipement.objects.select_related('salle__batiment').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer approprié selon l'action.
        
        Returns:
            Serializer: Classe de serializer à utiliser
        """
        if self.action in ['create', 'update', 'partial_update']:
            return EquipementCreateSerializer
        elif self.action == 'retrieve':
            return EquipementDetailSerializer
        return EquipementListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Équipements filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par catégorie
        categorie = self.request.query_params.get('categorie')
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        
        # Filtre par état
        etat = self.request.query_params.get('etat')
        if etat:
            queryset = queryset.filter(etat=etat)
        
        # Filtre par salle
        salle_id = self.request.query_params.get('salle')
        if salle_id:
            queryset = queryset.filter(salle_id=salle_id)
        
        # Filtre par réservabilité
        reservable = self.request.query_params.get('reservable')
        if reservable is not None:
            queryset = queryset.filter(reservable=(reservable.lower() == 'true'))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        Action personnalisée : Liste les équipements disponibles.
        
        URL: GET /equipements/disponibles/
        
        Returns:
            Response: Équipements disponibles pour réservation
        """
        equipements = self.get_queryset().filter(
            etat='DISPONIBLE',
            quantite_disponible__gt=0,
            reservable=True
        )
        
        serializer = self.get_serializer(equipements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Action personnalisée : Filtrer par catégorie.
        
        URL: GET /equipements/par-categorie/?categorie={categorie}
        
        Returns:
            Response: Équipements de la catégorie
        """
        categorie = request.query_params.get('categorie')
        
        if not categorie:
            return Response(
                {'error': 'Le paramètre categorie est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        equipements = self.get_queryset().filter(categorie=categorie)
        serializer = self.get_serializer(equipements, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_maintenance(self, request):
        """
        Action personnalisée : Équipements en maintenance.
        
        URL: GET /equipements/en-maintenance/
        
        Returns:
            Response: Liste des équipements en maintenance
        """
        equipements = self.get_queryset().filter(etat='EN_MAINTENANCE')
        serializer = self.get_serializer(equipements, many=True)
        
        return Response({
            'count': equipements.count(),
            'equipements': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def hors_service(self, request):
        """
        Action personnalisée : Équipements hors service.
        
        URL: GET /equipements/hors-service/
        
        Returns:
            Response: Liste des équipements hors service
        """
        equipements = self.get_queryset().filter(etat='HORS_SERVICE')
        serializer = self.get_serializer(equipements, many=True)
        
        return Response({
            'count': equipements.count(),
            'equipements': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def changer_etat(self, request, pk=None):
        """
        Action personnalisée : Change l'état d'un équipement.
        
        URL: POST /equipements/{id}/changer-etat/
        Body: {"nouvel_etat": "DISPONIBLE|RESERVE|EN_MAINTENANCE|HORS_SERVICE"}
        
        Returns:
            Response: Équipement avec nouvel état
        """
        equipement = self.get_object()
        nouvel_etat = request.data.get('nouvel_etat')
        
        if not nouvel_etat:
            return Response(
                {'error': 'Le paramètre nouvel_etat est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que l'état est valide
        etats_valides = ['DISPONIBLE', 'RESERVE', 'EN_MAINTENANCE', 'HORS_SERVICE']
        if nouvel_etat not in etats_valides:
            return Response(
                {'error': f'État invalide. Valeurs possibles : {", ".join(etats_valides)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Changer l'état (méthode du modèle)
        equipement.changer_etat(nouvel_etat)
        
        serializer = EquipementDetailSerializer(equipement)
        
        return Response({
            'message': f'État changé à {nouvel_etat}.',
            'equipement': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def historique_maintenances(self, request, pk=None):
        """
        Action personnalisée : Historique des maintenances d'un équipement.
        
        URL: GET /equipements/{id}/historique-maintenances/
        
        Returns:
            Response: Liste des maintenances
        """
        equipement = self.get_object()
        maintenances = equipement.maintenances.all()
        
        serializer = MaintenanceListSerializer(maintenances, many=True)
        
        return Response({
            'equipement': equipement.nom,
            'nombre_maintenances': maintenances.count(),
            'maintenances': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def verifier_disponibilite(self, request):
        """
        Action personnalisée : Vérifie la disponibilité d'un équipement.
        
        URL: POST /equipements/verifier-disponibilite/
        Body: {
            "equipement_id": 1,
            "date_debut": "2026-02-01T10:00:00Z",
            "date_fin": "2026-02-01T14:00:00Z",
            "quantite": 2
        }
        
        Returns:
            Response: Disponibilité de l'équipement
        """
        serializer = DisponibiliteEquipementSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        equipement_id = data['equipement_id']
        date_debut = data['date_debut']
        date_fin = data['date_fin']
        quantite = data['quantite']
        
        try:
            equipement = Equipement.objects.get(id=equipement_id)
        except Equipement.DoesNotExist:
            return Response(
                {'error': 'Équipement non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier les réservations existantes sur la période
        reservations_existantes = ReservationEquipement.objects.filter(
            equipement=equipement,
            reservation__date_debut__lt=date_fin,
            reservation__date_fin__gt=date_debut,
            reservation__statut__in=['EN_ATTENTE', 'VALIDEE']
        ).aggregate(total_reserve=Sum('quantite'))
        
        quantite_reservee = reservations_existantes['total_reserve'] or 0
        quantite_disponible = equipement.quantite_totale - quantite_reservee
        
        disponible = quantite_disponible >= quantite
        
        return Response({
            'equipement': equipement.nom,
            'quantite_totale': equipement.quantite_totale,
            'quantite_reservee_periode': quantite_reservee,
            'quantite_disponible_periode': quantite_disponible,
            'quantite_demandee': quantite,
            'disponible': disponible,
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des équipements.
        
        URL: GET /equipements/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = Equipement.objects.count()
        disponibles = Equipement.objects.filter(etat='DISPONIBLE').count()
        reserves = Equipement.objects.filter(etat='RESERVE').count()
        en_maintenance = Equipement.objects.filter(etat='EN_MAINTENANCE').count()
        hors_service = Equipement.objects.filter(etat='HORS_SERVICE').count()
        
        # Valeur totale du parc
        valeur_totale = Equipement.objects.aggregate(
            total=Sum('valeur_acquisition')
        )['total'] or 0
        
        # Répartition par catégorie
        par_categorie = Equipement.objects.values('categorie').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_equipements': total,
            'disponibles': disponibles,
            'reserves': reserves,
            'en_maintenance': en_maintenance,
            'hors_service': hors_service,
            'valeur_totale_parc': float(valeur_totale),
            'repartition_par_categorie': list(par_categorie),
        })

# VIEWSET : RÉSERVATIONS
class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les réservations.
    
    Endpoints :
    - GET /reservations/ : Liste toutes les réservations
    - POST /reservations/ : Crée une nouvelle réservation
    - GET /reservations/{id}/ : Détails d'une réservation
    - PUT/PATCH /reservations/{id}/ : Modifier une réservation
    - DELETE /reservations/{id}/ : Supprimer une réservation
    
    Actions personnalisées :
    - POST /reservations/{id}/valider/ : Valider une réservation
    - POST /reservations/{id}/rejeter/ : Rejeter une réservation
    - POST /reservations/{id}/annuler/ : Annuler une réservation
    - GET /reservations/en-attente/ : Réservations en attente
    - GET /reservations/mes-reservations/ : Réservations de l'utilisateur
    - GET /reservations/par-salle/ : Réservations d'une salle
    - POST /reservations/{id}/retourner-equipement/ : Marquer retour équipement
    - GET /reservations/statistiques/ : Stats globales
    
    Filtres :
    - ?demandeur={id} : Par demandeur
    - ?salle={id} : Par salle
    - ?statut=VALIDEE : Par statut
    - ?type_reservation=SALLE : Par type
    - ?date_debut=YYYY-MM-DD&date_fin=YYYY-MM-DD : Plage de dates
    """
    queryset = Reservation.objects.select_related(
        'demandeur',
        'salle__batiment',
        'valide_par'
    ).prefetch_related('equipements_reserves__equipement').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action == 'create':
            return ReservationCreateSerializer
        elif self.action == 'retrieve':
            return ReservationDetailSerializer
        return ReservationListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Réservations filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par demandeur
        demandeur_id = self.request.query_params.get('demandeur')
        if demandeur_id:
            queryset = queryset.filter(demandeur_id=demandeur_id)
        
        # Filtre par salle
        salle_id = self.request.query_params.get('salle')
        if salle_id:
            queryset = queryset.filter(salle_id=salle_id)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par type
        type_reservation = self.request.query_params.get('type_reservation')
        if type_reservation:
            queryset = queryset.filter(type_reservation=type_reservation)
        
        # Filtre par plage de dates
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                date_debut__gte=date_debut,
                date_fin__lte=date_fin
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """
        Action personnalisée : Valide une réservation.
        
        URL: POST /reservations/{id}/valider/
        Body (optionnel): {"commentaire": "..."}
        
        Returns:
            Response: Réservation validée
        """
        reservation = self.get_object()
        
        # Vérifier que la réservation est en attente
        if reservation.statut != 'EN_ATTENTE':
            return Response(
                {'error': 'Seules les réservations en attente peuvent être validées.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        commentaire = request.data.get('commentaire', '')
        
        # Valider (méthode du modèle)
        reservation.valider(request.user, commentaire)
        
        # Réserver les équipements
        for equip_reserve in reservation.equipements_reserves.all():
            equip_reserve.equipement.reserver(equip_reserve.quantite)
        
        serializer = ReservationDetailSerializer(reservation)
        
        return Response({
            'message': 'Réservation validée avec succès.',
            'reservation': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        """
        Action personnalisée : Rejette une réservation.
        
        URL: POST /reservations/{id}/rejeter/
        Body: {"commentaire": "Raison du rejet"}
        
        Returns:
            Response: Réservation rejetée
        """
        reservation = self.get_object()
        
        # Vérifier que la réservation est en attente
        if reservation.statut != 'EN_ATTENTE':
            return Response(
                {'error': 'Seules les réservations en attente peuvent être rejetées.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReservationValidationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        commentaire = serializer.validated_data.get('commentaire', '')
        
        # Rejeter (méthode du modèle)
        reservation.rejeter(request.user, commentaire)
        
        serializer_result = ReservationDetailSerializer(reservation)
        
        return Response({
            'message': 'Réservation rejetée.',
            'reservation': serializer_result.data
        })
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """
        Action personnalisée : Annule une réservation.
        
        URL: POST /reservations/{id}/annuler/
        
        Returns:
            Response: Réservation annulée
        """
        reservation = self.get_object()
        
        # Vérifier que c'est le demandeur qui annule
        if reservation.demandeur != request.user:
            return Response(
                {'error': 'Seul le demandeur peut annuler sa réservation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que la réservation n'est pas déjà terminée
        if reservation.statut == 'TERMINEE':
            return Response(
                {'error': 'Impossible d\'annuler une réservation terminée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Libérer les équipements si réservation validée
        if reservation.statut == 'VALIDEE':
            for equip_reserve in reservation.equipements_reserves.all():
                equip_reserve.equipement.liberer(equip_reserve.quantite)
        
        # Annuler (méthode du modèle)
        reservation.annuler()
        
        serializer = ReservationDetailSerializer(reservation)
        
        return Response({
            'message': 'Réservation annulée avec succès.',
            'reservation': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """
        Action personnalisée : Réservations en attente de validation.
        
        URL: GET /reservations/en-attente/
        
        Returns:
            Response: Liste des réservations EN_ATTENTE
        """
        reservations = self.get_queryset().filter(statut='EN_ATTENTE')
        serializer = self.get_serializer(reservations, many=True)
        
        return Response({
            'count': reservations.count(),
            'reservations': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def mes_reservations(self, request):
        """
        Action personnalisée : Réservations de l'utilisateur connecté.
        
        URL: GET /reservations/mes-reservations/
        
        Returns:
            Response: Réservations de l'utilisateur
        """
        reservations = self.get_queryset().filter(demandeur=request.user)
        serializer = self.get_serializer(reservations, many=True)
        
        return Response({
            'total': reservations.count(),
            'reservations': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_salle(self, request):
        """
        Action personnalisée : Réservations d'une salle.
        
        URL: GET /reservations/par-salle/?salle_id={id}
        
        Returns:
            Response: Réservations de la salle
        """
        salle_id = request.query_params.get('salle_id')
        
        if not salle_id:
            return Response(
                {'error': 'Le paramètre salle_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reservations = self.get_queryset().filter(salle_id=salle_id)
        serializer = self.get_serializer(reservations, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retourner_equipement(self, request, pk=None):
        """
        Action personnalisée : Marque le retour d'un équipement réservé.
        
        URL: POST /reservations/{id}/retourner-equipement/
        Body: {
            "equipement_id": 1,
            "etat_retour": "Bon état"
        }
        
        Returns:
            Response: Confirmation du retour
        """
        reservation = self.get_object()
        equipement_id = request.data.get('equipement_id')
        
        if not equipement_id:
            return Response(
                {'error': 'Le paramètre equipement_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            equip_reserve = reservation.equipements_reserves.get(equipement_id=equipement_id)
        except ReservationEquipement.DoesNotExist:
            return Response(
                {'error': 'Cet équipement n\'est pas dans cette réservation.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = RetourEquipementSerializer(data=request.data)
        
        if serializer.is_valid():
            etat_retour = serializer.validated_data.get('etat_retour', '')
            
            # Marquer comme retourné (méthode du modèle)
            equip_reserve.marquer_retour(etat_retour)
            
            return Response({
                'message': 'Retour enregistré avec succès.',
                'equipement': equip_reserve.equipement.nom,
                'quantite': equip_reserve.quantite,
                'date_retour': equip_reserve.date_retour,
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques des réservations.
        
        URL: GET /reservations/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = Reservation.objects.count()
        en_attente = Reservation.objects.filter(statut='EN_ATTENTE').count()
        validees = Reservation.objects.filter(statut='VALIDEE').count()
        rejetees = Reservation.objects.filter(statut='REJETEE').count()
        annulees = Reservation.objects.filter(statut='ANNULEE').count()
        
        # Répartition par type
        par_type = Reservation.objects.values('type_reservation').annotate(
            count=Count('id')
        )
        
        # Durée moyenne
        duree_moyenne = Reservation.objects.filter(
            statut__in=['VALIDEE', 'TERMINEE']
        ).aggregate(Avg('date_fin'))
        
        return Response({
            'total_reservations': total,
            'en_attente': en_attente,
            'validees': validees,
            'rejetees': rejetees,
            'annulees': annulees,
            'repartition_par_type': list(par_type),
        })

# VIEWSET : MAINTENANCES
class MaintenanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les maintenances.
    
    Endpoints :
    - GET /maintenances/ : Liste toutes les maintenances
    - POST /maintenances/ : Crée une nouvelle maintenance
    - GET /maintenances/{id}/ : Détails d'une maintenance
    - PUT/PATCH /maintenances/{id}/ : Modifier une maintenance
    - DELETE /maintenances/{id}/ : Supprimer une maintenance
    
    Actions personnalisées :
    - POST /maintenances/{id}/demarrer/ : Démarrer une maintenance
    - POST /maintenances/{id}/terminer/ : Terminer une maintenance
    - POST /maintenances/{id}/annuler/ : Annuler une maintenance
    - GET /maintenances/planifiees/ : Maintenances planifiées
    - GET /maintenances/en-cours/ : Maintenances en cours
    - GET /maintenances/par-equipement/ : Maintenances d'un équipement
    - GET /maintenances/preventives/ : Maintenances préventives
    - GET /maintenances/correctives/ : Maintenances correctives
    - GET /maintenances/statistiques/ : Stats globales
    
    Filtres :
    - ?equipement={id} : Par équipement
    - ?type_maintenance=PREVENTIVE : Par type
    - ?statut=EN_COURS : Par statut
    - ?technicien={id} : Par technicien
    """
    queryset = Maintenance.objects.select_related(
        'equipement',
        'technicien'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action in ['create', 'update', 'partial_update']:
            return MaintenanceCreateSerializer
        elif self.action == 'retrieve':
            return MaintenanceDetailSerializer
        return MaintenanceListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Maintenances filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par équipement
        equipement_id = self.request.query_params.get('equipement')
        if equipement_id:
            queryset = queryset.filter(equipement_id=equipement_id)
        
        # Filtre par type
        type_maintenance = self.request.query_params.get('type_maintenance')
        if type_maintenance:
            queryset = queryset.filter(type_maintenance=type_maintenance)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par technicien
        technicien_id = self.request.query_params.get('technicien')
        if technicien_id:
            queryset = queryset.filter(technicien_id=technicien_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        """
        Action personnalisée : Démarre une maintenance.
        
        URL: POST /maintenances/{id}/demarrer/
        
        Returns:
            Response: Maintenance démarrée
        """
        maintenance = self.get_object()
        
        # Vérifier que la maintenance est planifiée
        if maintenance.statut != 'PLANIFIEE':
            return Response(
                {'error': 'Seules les maintenances planifiées peuvent être démarrées.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Démarrer (méthode du modèle)
        maintenance.demarrer()
        
        serializer = MaintenanceDetailSerializer(maintenance)
        
        return Response({
            'message': 'Maintenance démarrée avec succès.',
            'maintenance': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        """
        Action personnalisée : Termine une maintenance.
        
        URL: POST /maintenances/{id}/terminer/
        Body: {
            "travaux_effectues": "Remplacement disque dur",
            "pieces_remplacees": "Disque dur 1TB",
            "observations": "Équipement opérationnel"
        }
        
        Returns:
            Response: Maintenance terminée
        """
        maintenance = self.get_object()
        
        # Vérifier que la maintenance est en cours
        if maintenance.statut != 'EN_COURS':
            return Response(
                {'error': 'Seules les maintenances en cours peuvent être terminées.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MaintenanceTerminaisonSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Terminer (méthode du modèle)
        maintenance.terminer(
            travaux=data['travaux_effectues'],
            pieces=data.get('pieces_remplacees', ''),
            observations=data.get('observations', '')
        )
        
        serializer_result = MaintenanceDetailSerializer(maintenance)
        
        return Response({
            'message': 'Maintenance terminée avec succès.',
            'maintenance': serializer_result.data
        })
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """
        Action personnalisée : Annule une maintenance.
        
        URL: POST /maintenances/{id}/annuler/
        
        Returns:
            Response: Maintenance annulée
        """
        maintenance = self.get_object()
        
        # Vérifier que la maintenance n'est pas déjà terminée
        if maintenance.statut == 'TERMINEE':
            return Response(
                {'error': 'Impossible d\'annuler une maintenance terminée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Annuler (méthode du modèle)
        maintenance.annuler()
        
        serializer = MaintenanceDetailSerializer(maintenance)
        
        return Response({
            'message': 'Maintenance annulée avec succès.',
            'maintenance': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def planifiees(self, request):
        """
        Action personnalisée : Maintenances planifiées.
        
        URL: GET /maintenances/planifiees/
        
        Returns:
            Response: Liste des maintenances PLANIFIEE
        """
        maintenances = self.get_queryset().filter(statut='PLANIFIEE')
        serializer = self.get_serializer(maintenances, many=True)
        
        return Response({
            'count': maintenances.count(),
            'maintenances': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        """
        Action personnalisée : Maintenances en cours.
        
        URL: GET /maintenances/en-cours/
        
        Returns:
            Response: Liste des maintenances EN_COURS
        """
        maintenances = self.get_queryset().filter(statut='EN_COURS')
        serializer = self.get_serializer(maintenances, many=True)
        
        return Response({
            'count': maintenances.count(),
            'maintenances': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_equipement(self, request):
        """
        Action personnalisée : Maintenances d'un équipement.
        
        URL: GET /maintenances/par-equipement/?equipement_id={id}
        
        Returns:
            Response: Maintenances de l'équipement
        """
        equipement_id = request.query_params.get('equipement_id')
        
        if not equipement_id:
            return Response(
                {'error': 'Le paramètre equipement_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        maintenances = self.get_queryset().filter(equipement_id=equipement_id)
        serializer = self.get_serializer(maintenances, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def preventives(self, request):
        """
        Action personnalisée : Maintenances préventives.
        
        URL: GET /maintenances/preventives/
        
        Returns:
            Response: Maintenances PREVENTIVE
        """
        maintenances = self.get_queryset().filter(type_maintenance='PREVENTIVE')
        serializer = self.get_serializer(maintenances, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def correctives(self, request):
        """
        Action personnalisée : Maintenances correctives.
        
        URL: GET /maintenances/correctives/
        
        Returns:
            Response: Maintenances CORRECTIVE
        """
        maintenances = self.get_queryset().filter(type_maintenance='CORRECTIVE')
        serializer = self.get_serializer(maintenances, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques des maintenances.
        
        URL: GET /maintenances/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = Maintenance.objects.count()
        planifiees = Maintenance.objects.filter(statut='PLANIFIEE').count()
        en_cours = Maintenance.objects.filter(statut='EN_COURS').count()
        terminees = Maintenance.objects.filter(statut='TERMINEE').count()
        
        # Coût total
        cout_total = Maintenance.objects.filter(
            statut='TERMINEE'
        ).aggregate(
            total_main_oeuvre=Sum('cout_main_oeuvre'),
            total_pieces=Sum('cout_pieces')
        )
        
        main_oeuvre = cout_total['total_main_oeuvre'] or 0
        pieces = cout_total['total_pieces'] or 0
        
        # Répartition par type
        par_type = Maintenance.objects.values('type_maintenance').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_maintenances': total,
            'planifiees': planifiees,
            'en_cours': en_cours,
            'terminees': terminees,
            'cout_total_main_oeuvre': float(main_oeuvre),
            'cout_total_pieces': float(pieces),
            'cout_total': float(main_oeuvre + pieces),
            'repartition_par_type': list(par_type),
        })
