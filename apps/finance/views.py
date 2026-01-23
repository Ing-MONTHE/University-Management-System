from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from decimal import Decimal

from .models import FraisScolarite, Paiement, Bourse, Facture
from .serializers import (
    FraisScolariteListSerializer,
    FraisScolariteDetailSerializer,
    FraisScolariteCreateSerializer,
    PaiementListSerializer,
    PaiementDetailSerializer,
    PaiementCreateSerializer,
    PaiementValidationSerializer,
    BourseListSerializer,
    BourseDetailSerializer,
    BourseCreateSerializer,
    FactureListSerializer,
    FactureDetailSerializer,
    FactureGenerationSerializer,
)
from apps.students.models import Inscription

# VIEWSET : FRAIS DE SCOLARITÉ
class FraisScolariteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les frais de scolarité.
    
    Endpoints générés automatiquement :
    - GET /frais-scolarite/ : Liste tous les frais
    - POST /frais-scolarite/ : Crée de nouveaux frais
    - GET /frais-scolarite/{id}/ : Détails d'un tarif
    - PUT /frais-scolarite/{id}/ : Mise à jour complète
    - PATCH /frais-scolarite/{id}/ : Mise à jour partielle
    - DELETE /frais-scolarite/{id}/ : Suppression
    
    Actions personnalisées :
    - GET /frais-scolarite/actifs/ : Frais actifs uniquement
    - GET /frais-scolarite/par-filiere/ : Frais d'une filière
    - GET /frais-scolarite/par-annee/ : Frais d'une année académique
    - GET /frais-scolarite/statistiques/ : Stats globales
    
    Filtres :
    - ?filiere={id} : Par filière
    - ?annee_academique={id} : Par année
    - ?niveau=L1 : Par niveau
    - ?actif=true : Seulement les actifs
    
    Permissions : Authentification requise
    """
    queryset = FraisScolarite.objects.select_related(
        'filiere__departement__faculte',
        'annee_academique'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer approprié selon l'action.
        
        Returns:
            Serializer: Classe de serializer à utiliser
        """
        if self.action in ['create', 'update', 'partial_update']:
            return FraisScolariteCreateSerializer
        elif self.action == 'retrieve':
            return FraisScolariteDetailSerializer
        return FraisScolariteListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Paramètres de requête supportés :
        - filiere : ID de la filière
        - annee_academique : ID de l'année académique
        - niveau : Niveau d'études (ex: L1, L2, M1)
        - actif : true/false
        
        Returns:
            QuerySet: Frais filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par filière
        filiere_id = self.request.query_params.get('filiere')
        if filiere_id:
            queryset = queryset.filter(filiere_id=filiere_id)
        
        # Filtre par année académique
        annee_id = self.request.query_params.get('annee_academique')
        if annee_id:
            queryset = queryset.filter(annee_academique_id=annee_id)
        
        # Filtre par niveau
        niveau = self.request.query_params.get('niveau')
        if niveau:
            queryset = queryset.filter(niveau=niveau)
        
        # Filtre par statut actif
        actif = self.request.query_params.get('actif')
        if actif is not None:
            queryset = queryset.filter(actif=(actif.lower() == 'true'))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """
        Action personnalisée : Liste uniquement les frais actifs.
        
        URL: GET /frais-scolarite/actifs/
        
        Returns:
            Response: Liste des frais actifs
        """
        frais = self.get_queryset().filter(actif=True)
        serializer = self.get_serializer(frais, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_filiere(self, request):
        """
        Action personnalisée : Frais d'une filière spécifique.
        
        URL: GET /frais-scolarite/par-filiere/?filiere_id={id}
        
        Paramètres :
        - filiere_id : ID de la filière (requis)
        
        Returns:
            Response: Liste des frais de la filière
        """
        filiere_id = request.query_params.get('filiere_id')
        
        if not filiere_id:
            return Response(
                {'error': 'Le paramètre filiere_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        frais = self.get_queryset().filter(filiere_id=filiere_id)
        serializer = self.get_serializer(frais, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_annee(self, request):
        """
        Action personnalisée : Frais d'une année académique.
        
        URL: GET /frais-scolarite/par-annee/?annee_id={id}
        
        Returns:
            Response: Liste des frais de l'année
        """
        annee_id = request.query_params.get('annee_id')
        
        if not annee_id:
            return Response(
                {'error': 'Le paramètre annee_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        frais = self.get_queryset().filter(annee_academique_id=annee_id)
        serializer = self.get_serializer(frais, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des frais de scolarité.
        
        URL: GET /frais-scolarite/statistiques/
        
        Returns:
            Response: {
                total_configurations: int,
                configurations_actives: int,
                montant_moyen: float,
                montant_min: float,
                montant_max: float,
                repartition_par_filiere: [{filiere, count}]
            }
        """
        total = FraisScolarite.objects.count()
        actifs = FraisScolarite.objects.filter(actif=True).count()
        
        # Calculer les montants
        stats_montants = FraisScolarite.objects.aggregate(
            montant_moyen=Avg('montant_total'),
            montant_min=Sum('montant_total'),
            montant_max=Sum('montant_total')
        )
        
        # Répartition par filière
        repartition = FraisScolarite.objects.values(
            'filiere__nom'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_configurations': total,
            'configurations_actives': actifs,
            'montant_moyen': float(stats_montants['montant_moyen'] or 0),
            'repartition_par_filiere': list(repartition),
        })

# VIEWSET : PAIEMENTS
class PaiementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les paiements.
    
    Endpoints :
    - GET /paiements/ : Liste tous les paiements
    - POST /paiements/ : Enregistre un nouveau paiement
    - GET /paiements/{id}/ : Détails d'un paiement
    - PUT/PATCH /paiements/{id}/ : Modifier un paiement
    - DELETE /paiements/{id}/ : Supprimer un paiement
    
    Actions personnalisées :
    - POST /paiements/{id}/valider/ : Valider un paiement
    - GET /paiements/en-attente/ : Paiements à valider
    - GET /paiements/par-etudiant/ : Paiements d'un étudiant
    - GET /paiements/par-mode/ : Répartition par mode de paiement
    - GET /paiements/statistiques/ : Stats financières globales
    
    Filtres :
    - ?inscription={id} : Par inscription
    - ?statut=VALIDE : Par statut
    - ?mode_paiement=ESPECES : Par mode
    - ?date_debut=YYYY-MM-DD&date_fin=YYYY-MM-DD : Plage de dates
    """
    queryset = Paiement.objects.select_related(
        'inscription__etudiant__user',
        'inscription__filiere',
        'inscription__annee_academique',
        'valide_par'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action == 'create':
            return PaiementCreateSerializer
        elif self.action == 'retrieve':
            return PaiementDetailSerializer
        return PaiementListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Paiements filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par inscription
        inscription_id = self.request.query_params.get('inscription')
        if inscription_id:
            queryset = queryset.filter(inscription_id=inscription_id)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par mode de paiement
        mode = self.request.query_params.get('mode_paiement')
        if mode:
            queryset = queryset.filter(mode_paiement=mode)
        
        # Filtre par plage de dates
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                date_paiement__gte=date_debut,
                date_paiement__lte=date_fin
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """
        Action personnalisée : Valide un paiement.
        
        URL: POST /paiements/{id}/valider/
        Body (optionnel): { "observations": "Paiement vérifié" }
        
        Processus :
        1. Change le statut à VALIDE
        2. Enregistre qui a validé et quand
        3. Met à jour la facture
        
        Returns:
            Response: Paiement validé avec message
        """
        paiement = self.get_object()
        
        # Vérifier que le paiement n'est pas déjà validé
        if paiement.statut == 'VALIDE':
            return Response(
                {'error': 'Ce paiement a déjà été validé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les observations optionnelles
        observations = request.data.get('observations', '')
        if observations:
            paiement.observations = observations
        
        # Valider le paiement (méthode du modèle)
        paiement.valider(request.user)
        
        serializer = PaiementDetailSerializer(paiement)
        
        return Response({
            'message': 'Paiement validé avec succès.',
            'paiement': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """
        Action personnalisée : Liste les paiements en attente de validation.
        
        URL: GET /paiements/en-attente/
        
        Returns:
            Response: Liste des paiements EN_ATTENTE
        """
        paiements = self.get_queryset().filter(statut='EN_ATTENTE').order_by('date_paiement')
        serializer = self.get_serializer(paiements, many=True)
        
        return Response({
            'count': paiements.count(),
            'paiements': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_etudiant(self, request):
        """
        Action personnalisée : Paiements d'un étudiant.
        
        URL: GET /paiements/par-etudiant/?etudiant_id={id}
        
        Returns:
            Response: Liste avec statistiques
        """
        etudiant_id = request.query_params.get('etudiant_id')
        
        if not etudiant_id:
            return Response(
                {'error': 'Le paramètre etudiant_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        paiements = self.get_queryset().filter(
            inscription__etudiant_id=etudiant_id
        )
        
        serializer = self.get_serializer(paiements, many=True)
        
        # Calculer les statistiques
        total_paye = paiements.filter(statut='VALIDE').aggregate(
            total=Sum('montant')
        )['total'] or Decimal('0.00')
        
        return Response({
            'paiements': serializer.data,
            'statistiques': {
                'nombre_paiements': paiements.count(),
                'total_paye': float(total_paye),
            }
        })
    
    @action(detail=False, methods=['get'])
    def par_mode(self, request):
        """
        Action personnalisée : Répartition des paiements par mode.
        
        URL: GET /paiements/par-mode/
        
        Returns:
            Response: Statistiques par mode de paiement
        """
        repartition = Paiement.objects.filter(
            statut='VALIDE'
        ).values('mode_paiement').annotate(
            nombre=Count('id'),
            montant_total=Sum('montant')
        )
        
        return Response(list(repartition))
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques financières globales.
        
        URL: GET /paiements/statistiques/
        
        Returns:
            Response: Stats complètes des paiements
        """
        # Total des paiements validés
        stats = Paiement.objects.filter(statut='VALIDE').aggregate(
            total_paiements=Count('id'),
            montant_total=Sum('montant'),
            montant_moyen=Avg('montant')
        )
        
        # Paiements en attente
        en_attente = Paiement.objects.filter(statut='EN_ATTENTE').aggregate(
            nombre=Count('id'),
            montant=Sum('montant')
        )
        
        # Paiements du mois en cours
        date_actuelle = timezone.now()
        premier_jour = date_actuelle.replace(day=1)
        
        mois_actuel = Paiement.objects.filter(
            statut='VALIDE',
            date_paiement__gte=premier_jour
        ).aggregate(
            nombre=Count('id'),
            montant=Sum('montant')
        )
        
        return Response({
            'total_paiements_valides': stats['total_paiements'] or 0,
            'montant_total_encaisse': float(stats['montant_total'] or 0),
            'montant_moyen_paiement': float(stats['montant_moyen'] or 0),
            'paiements_en_attente': {
                'nombre': en_attente['nombre'] or 0,
                'montant': float(en_attente['montant'] or 0),
            },
            'mois_actuel': {
                'nombre': mois_actuel['nombre'] or 0,
                'montant': float(mois_actuel['montant'] or 0),
            }
        })

# VIEWSET : BOURSES
class BourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les bourses et exonérations.
    
    Endpoints :
    - GET /bourses/ : Liste toutes les bourses
    - POST /bourses/ : Crée une nouvelle bourse
    - GET /bourses/{id}/ : Détails d'une bourse
    - PUT/PATCH /bourses/{id}/ : Modifier une bourse
    - DELETE /bourses/{id}/ : Supprimer une bourse
    
    Actions personnalisées :
    - GET /bourses/actives/ : Bourses actuellement actives
    - GET /bourses/par-etudiant/ : Bourses d'un étudiant
    - GET /bourses/par-source/ : Répartition par source
    - POST /bourses/{id}/suspendre/ : Suspendre une bourse
    - POST /bourses/{id}/reactiver/ : Réactiver une bourse
    - GET /bourses/statistiques/ : Stats globales
    
    Filtres :
    - ?etudiant={id} : Par étudiant
    - ?annee_academique={id} : Par année
    - ?type_bourse=TOTALE : Par type
    - ?statut=EN_COURS : Par statut
    - ?source=GOUVERNEMENT : Par source
    """
    queryset = Bourse.objects.select_related(
        'etudiant__user',
        'annee_academique'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action in ['create', 'update', 'partial_update']:
            return BourseCreateSerializer
        elif self.action == 'retrieve':
            return BourseDetailSerializer
        return BourseListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Bourses filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par étudiant
        etudiant_id = self.request.query_params.get('etudiant')
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        
        # Filtre par année académique
        annee_id = self.request.query_params.get('annee_academique')
        if annee_id:
            queryset = queryset.filter(annee_academique_id=annee_id)
        
        # Filtre par type
        type_bourse = self.request.query_params.get('type_bourse')
        if type_bourse:
            queryset = queryset.filter(type_bourse=type_bourse)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source_financement=source)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def actives(self, request):
        """
        Action personnalisée : Liste les bourses actuellement actives.
        
        URL: GET /bourses/actives/
        
        Returns:
            Response: Liste des bourses EN_COURS et dans la période de validité
        """
        date_actuelle = timezone.now().date()
        
        bourses = self.get_queryset().filter(
            statut='EN_COURS',
            date_debut__lte=date_actuelle,
            date_fin__gte=date_actuelle
        )
        
        serializer = self.get_serializer(bourses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_etudiant(self, request):
        """
        Action personnalisée : Bourses d'un étudiant.
        
        URL: GET /bourses/par-etudiant/?etudiant_id={id}
        
        Returns:
            Response: Liste des bourses avec montants calculés
        """
        etudiant_id = request.query_params.get('etudiant_id')
        
        if not etudiant_id:
            return Response(
                {'error': 'Le paramètre etudiant_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bourses = self.get_queryset().filter(etudiant_id=etudiant_id)
        serializer = self.get_serializer(bourses, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_source(self, request):
        """
        Action personnalisée : Répartition des bourses par source.
        
        URL: GET /bourses/par-source/
        
        Returns:
            Response: Statistiques par source de financement
        """
        repartition = Bourse.objects.values('source_financement').annotate(
            nombre=Count('id')
        ).order_by('-nombre')
        
        return Response(list(repartition))
    
    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        """
        Action personnalisée : Suspendre une bourse.
        
        URL: POST /bourses/{id}/suspendre/
        
        Returns:
            Response: Bourse suspendue
        """
        bourse = self.get_object()
        
        if bourse.statut == 'SUSPENDUE':
            return Response(
                {'error': 'Cette bourse est déjà suspendue.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bourse.statut = 'SUSPENDUE'
        bourse.save()
        
        serializer = BourseDetailSerializer(bourse)
        
        return Response({
            'message': 'Bourse suspendue avec succès.',
            'bourse': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reactiver(self, request, pk=None):
        """
        Action personnalisée : Réactiver une bourse suspendue.
        
        URL: POST /bourses/{id}/reactiver/
        
        Returns:
            Response: Bourse réactivée
        """
        bourse = self.get_object()
        
        if bourse.statut != 'SUSPENDUE':
            return Response(
                {'error': 'Seules les bourses suspendues peuvent être réactivées.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bourse.statut = 'EN_COURS'
        bourse.save()
        
        serializer = BourseDetailSerializer(bourse)
        
        return Response({
            'message': 'Bourse réactivée avec succès.',
            'bourse': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des bourses.
        
        URL: GET /bourses/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = Bourse.objects.count()
        actives = Bourse.objects.filter(statut='EN_COURS').count()
        suspendues = Bourse.objects.filter(statut='SUSPENDUE').count()
        
        # Répartition par type
        par_type = Bourse.objects.values('type_bourse').annotate(
            count=Count('id')
        )
        
        # Répartition par source
        par_source = Bourse.objects.values('source_financement').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_bourses': total,
            'bourses_actives': actives,
            'bourses_suspendues': suspendues,
            'repartition_par_type': list(par_type),
            'repartition_par_source': list(par_source),
        })

# VIEWSET : FACTURES
class FactureViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les factures de scolarité.
    
    Endpoints :
    - GET /factures/ : Liste toutes les factures
    - POST /factures/ : Génère une nouvelle facture
    - GET /factures/{id}/ : Détails d'une facture
    - PUT/PATCH /factures/{id}/ : Modifier une facture
    - DELETE /factures/{id}/ : Supprimer une facture
    
    Actions personnalisées :
    - POST /factures/generer/ : Générer une facture pour une inscription
    - GET /factures/impayees/ : Factures impayées
    - GET /factures/en-retard/ : Factures en retard de paiement
    - GET /factures/soldees/ : Factures totalement payées
    - GET /factures/par-etudiant/ : Factures d'un étudiant
    - GET /factures/statistiques/ : Stats de recouvrement
    
    Filtres :
    - ?inscription={id} : Par inscription
    - ?statut=IMPAYEE : Par statut
    - ?en_retard=true : Seulement les retards
    """
    queryset = Facture.objects.select_related(
        'inscription__etudiant__user',
        'inscription__filiere',
        'inscription__annee_academique'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action == 'retrieve':
            return FactureDetailSerializer
        return FactureListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Factures filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par inscription
        inscription_id = self.request.query_params.get('inscription')
        if inscription_id:
            queryset = queryset.filter(inscription_id=inscription_id)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre factures en retard
        en_retard = self.request.query_params.get('en_retard')
        if en_retard and en_retard.lower() == 'true':
            date_actuelle = timezone.now().date()
            queryset = queryset.filter(
                date_echeance__lt=date_actuelle
            ).exclude(statut='SOLDEE')
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generer(self, request):
        """
        Action personnalisée : Génère une facture pour une inscription.
        
        URL: POST /factures/generer/
        Body: {
            "inscription_id": 123,
            "date_echeance": "2026-06-30"  # optionnel
        }
        
        Processus :
        1. Récupère les frais de scolarité
        2. Calcule les bourses/réductions
        3. Génère la facture
        
        Returns:
            Response: Facture générée
        """
        serializer = FactureGenerationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        inscription_id = serializer.validated_data['inscription_id']
        date_echeance = serializer.validated_data.get('date_echeance')
        
        try:
            inscription = Inscription.objects.get(id=inscription_id)
        except Inscription.DoesNotExist:
            return Response(
                {'error': 'Inscription non trouvée.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les frais de scolarité
        try:
            frais = FraisScolarite.objects.get(
                filiere=inscription.filiere,
                annee_academique=inscription.annee_academique,
                niveau=inscription.niveau,
                actif=True
            )
        except FraisScolarite.DoesNotExist:
            return Response(
                {'error': 'Aucun frais de scolarité configuré pour cette inscription.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculer les réductions (bourses)
        bourses = Bourse.objects.filter(
            etudiant=inscription.etudiant,
            annee_academique=inscription.annee_academique,
            statut='EN_COURS'
        )
        
        montant_reduction = Decimal('0.00')
        for bourse in bourses:
            if bourse.est_active():
                montant_reduction += bourse.calculer_montant_reduction(frais.montant_total)
        
        # Calculer le montant net
        montant_net = frais.montant_total - montant_reduction
        
        # Date d'échéance
        if not date_echeance:
            date_echeance = frais.date_limite_paiement
        
        # Créer la facture
        facture = Facture.objects.create(
            inscription=inscription,
            montant_brut=frais.montant_total,
            montant_reduction=montant_reduction,
            montant_net=montant_net,
            date_echeance=date_echeance
        )
        
        serializer_facture = FactureDetailSerializer(facture)
        
        return Response({
            'message': 'Facture générée avec succès.',
            'facture': serializer_facture.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def impayees(self, request):
        """
        Action personnalisée : Liste les factures impayées.
        
        URL: GET /factures/impayees/
        
        Returns:
            Response: Liste des factures IMPAYEE
        """
        factures = self.get_queryset().filter(statut='IMPAYEE')
        serializer = self.get_serializer(factures, many=True)
        
        # Calculer le total impayé
        total_impaye = factures.aggregate(total=Sum('solde'))['total'] or Decimal('0.00')
        
        return Response({
            'count': factures.count(),
            'total_impaye': float(total_impaye),
            'factures': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def en_retard(self, request):
        """
        Action personnalisée : Factures en retard de paiement.
        
        URL: GET /factures/en-retard/
        
        Returns:
            Response: Factures non soldées avec échéance dépassée
        """
        date_actuelle = timezone.now().date()
        
        factures = self.get_queryset().filter(
            date_echeance__lt=date_actuelle
        ).exclude(statut='SOLDEE')
        
        serializer = self.get_serializer(factures, many=True)
        
        # Calculer le total en retard
        total_retard = factures.aggregate(total=Sum('solde'))['total'] or Decimal('0.00')
        
        return Response({
            'count': factures.count(),
            'total_en_retard': float(total_retard),
            'factures': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def soldees(self, request):
        """
        Action personnalisée : Factures totalement payées.
        
        URL: GET /factures/soldees/
        
        Returns:
            Response: Liste des factures SOLDEE
        """
        factures = self.get_queryset().filter(statut='SOLDEE')
        serializer = self.get_serializer(factures, many=True)
        
        return Response({
            'count': factures.count(),
            'factures': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_etudiant(self, request):
        """
        Action personnalisée : Factures d'un étudiant.
        
        URL: GET /factures/par-etudiant/?etudiant_id={id}
        
        Returns:
            Response: Liste des factures avec totaux
        """
        etudiant_id = request.query_params.get('etudiant_id')
        
        if not etudiant_id:
            return Response(
                {'error': 'Le paramètre etudiant_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        factures = self.get_queryset().filter(inscription__etudiant_id=etudiant_id)
        serializer = self.get_serializer(factures, many=True)
        
        # Calculer les totaux
        totaux = factures.aggregate(
            total_net=Sum('montant_net'),
            total_paye=Sum('montant_paye'),
            total_solde=Sum('solde')
        )
        
        return Response({
            'factures': serializer.data,
            'totaux': {
                'total_a_payer': float(totaux['total_net'] or 0),
                'total_paye': float(totaux['total_paye'] or 0),
                'total_restant': float(totaux['total_solde'] or 0),
            }
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques de recouvrement.
        
        URL: GET /factures/statistiques/
        
        Returns:
            Response: Stats financières complètes
        """
        total_factures = Facture.objects.count()
        
        # Totaux par statut
        totaux = Facture.objects.aggregate(
            montant_total_brut=Sum('montant_brut'),
            montant_total_net=Sum('montant_net'),
            montant_total_paye=Sum('montant_paye'),
            montant_total_solde=Sum('solde')
        )
        
        # Répartition par statut
        par_statut = Facture.objects.values('statut').annotate(
            count=Count('id'),
            montant=Sum('solde')
        )
        
        # Factures en retard
        date_actuelle = timezone.now().date()
        factures_retard = Facture.objects.filter(
            date_echeance__lt=date_actuelle
        ).exclude(statut='SOLDEE')
        
        total_retard = factures_retard.aggregate(total=Sum('solde'))['total'] or Decimal('0.00')
        
        # Taux de recouvrement
        montant_net = totaux['montant_total_net'] or Decimal('0.00')
        montant_paye = totaux['montant_total_paye'] or Decimal('0.00')
        
        taux_recouvrement = 0
        if montant_net > 0:
            taux_recouvrement = round((float(montant_paye) / float(montant_net)) * 100, 2)
        
        return Response({
            'total_factures': total_factures,
            'montant_total_a_encaisser': float(montant_net),
            'montant_total_encaisse': float(montant_paye),
            'montant_total_restant': float(totaux['montant_total_solde'] or 0),
            'taux_recouvrement': taux_recouvrement,
            'factures_en_retard': {
                'nombre': factures_retard.count(),
                'montant': float(total_retard),
            },
            'repartition_par_statut': list(par_statut),
        })
