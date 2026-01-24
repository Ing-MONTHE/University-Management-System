from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

from .models import Rapport, Dashboard, KPI
from .serializers import (
    RapportListSerializer,
    RapportDetailSerializer,
    RapportCreateSerializer,
    DashboardListSerializer,
    DashboardDetailSerializer,
    DashboardCreateSerializer,
    KPIListSerializer,
    KPIDetailSerializer,
    KPICreateSerializer,
)

# VIEWSET : RAPPORTS
class RapportViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les rapports.
    
    Endpoints :
    - GET /rapports/ : Liste tous les rapports
    - POST /rapports/ : Crée un nouveau rapport
    - GET /rapports/{id}/ : Détails d'un rapport
    - PUT/PATCH /rapports/{id}/ : Modifier un rapport
    - DELETE /rapports/{id}/ : Supprimer un rapport
    
    Actions personnalisées :
    - POST /rapports/{id}/generer/ : Générer le rapport
    - GET /rapports/generes/ : Rapports générés
    - GET /rapports/planifies/ : Rapports planifiés
    - GET /rapports/par-type/ : Filtrer par type
    - GET /rapports/statistiques/ : Stats globales
    """
    queryset = Rapport.objects.select_related(
        'annee_academique',
        'filiere',
        'genere_par'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RapportCreateSerializer
        elif self.action == 'retrieve':
            return RapportDetailSerializer
        return RapportListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        type_rapport = self.request.query_params.get('type_rapport')
        if type_rapport:
            queryset = queryset.filter(type_rapport=type_rapport)
        
        genere = self.request.query_params.get('genere')
        if genere is not None:
            queryset = queryset.filter(genere=(genere.lower() == 'true'))
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def generer(self, request, pk=None):
        """
        Action personnalisée : Génère le rapport.
        
        URL: POST /rapports/{id}/generer/
        """
        rapport = self.get_object()
        
        if rapport.genere:
            return Response(
                {'error': 'Ce rapport a déjà été généré.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Générer le fichier selon le type et format
        # Pour cette démo, on marque juste comme généré
        
        rapport.generer_rapport(request.user)
        
        serializer = RapportDetailSerializer(rapport, context={'request': request})
        
        return Response({
            'message': 'Rapport généré avec succès.',
            'rapport': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def generes(self, request):
        """
        Action personnalisée : Rapports générés.
        
        URL: GET /rapports/generes/
        """
        rapports = self.get_queryset().filter(genere=True)
        serializer = self.get_serializer(rapports, many=True)
        
        return Response({
            'count': rapports.count(),
            'rapports': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def planifies(self, request):
        """
        Action personnalisée : Rapports planifiés.
        
        URL: GET /rapports/planifies/
        """
        rapports = self.get_queryset().filter(planifie=True)
        serializer = self.get_serializer(rapports, many=True)
        
        return Response({
            'count': rapports.count(),
            'rapports': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """
        Action personnalisée : Filtrer par type.
        
        URL: GET /rapports/par-type/?type={type}
        """
        type_rapport = request.query_params.get('type')
        
        if not type_rapport:
            return Response(
                {'error': 'Le paramètre type est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rapports = self.get_queryset().filter(type_rapport=type_rapport)
        serializer = self.get_serializer(rapports, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales.
        
        URL: GET /rapports/statistiques/
        """
        total = Rapport.objects.count()
        generes = Rapport.objects.filter(genere=True).count()
        planifies = Rapport.objects.filter(planifie=True).count()
        
        par_type = Rapport.objects.values('type_rapport').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_rapports': total,
            'generes': generes,
            'planifies': planifies,
            'repartition_par_type': list(par_type),
        })

# VIEWSET : DASHBOARDS
class DashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les dashboards.
    
    Endpoints :
    - GET /dashboards/ : Liste tous les dashboards
    - POST /dashboards/ : Crée un nouveau dashboard
    - GET /dashboards/{id}/ : Détails d'un dashboard
    - PUT/PATCH /dashboards/{id}/ : Modifier un dashboard
    - DELETE /dashboards/{id}/ : Supprimer un dashboard
    
    Actions personnalisées :
    - GET /dashboards/mes-dashboards/ : Dashboards de l'utilisateur
    - GET /dashboards/partages/ : Dashboards partagés avec l'utilisateur
    - POST /dashboards/{id}/partager/ : Partager avec des utilisateurs
    - POST /dashboards/{id}/definir-par-defaut/ : Définir comme défaut
    """
    queryset = Dashboard.objects.select_related('proprietaire').prefetch_related('utilisateurs_partages').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DashboardCreateSerializer
        elif self.action == 'retrieve':
            return DashboardDetailSerializer
        return DashboardListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrer pour ne montrer que les dashboards de l'utilisateur ou partagés avec lui
        user = self.request.user
        queryset = queryset.filter(
            Q(proprietaire=user) | Q(utilisateurs_partages=user)
        ).distinct()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def mes_dashboards(self, request):
        """
        Action personnalisée : Dashboards de l'utilisateur.
        
        URL: GET /dashboards/mes-dashboards/
        """
        dashboards = Dashboard.objects.filter(proprietaire=request.user)
        serializer = self.get_serializer(dashboards, many=True)
        
        return Response({
            'total': dashboards.count(),
            'dashboards': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def partages(self, request):
        """
        Action personnalisée : Dashboards partagés avec l'utilisateur.
        
        URL: GET /dashboards/partages/
        """
        dashboards = Dashboard.objects.filter(utilisateurs_partages=request.user)
        serializer = self.get_serializer(dashboards, many=True)
        
        return Response({
            'total': dashboards.count(),
            'dashboards': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def partager(self, request, pk=None):
        """
        Action personnalisée : Partager avec des utilisateurs.
        
        URL: POST /dashboards/{id}/partager/
        Body: {"utilisateurs": [1, 2, 3]}
        """
        dashboard = self.get_object()
        
        # Vérifier que c'est le propriétaire
        if dashboard.proprietaire != request.user:
            return Response(
                {'error': 'Seul le propriétaire peut partager ce dashboard.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        utilisateurs_ids = request.data.get('utilisateurs', [])
        
        from apps.core.models import User
        utilisateurs = User.objects.filter(id__in=utilisateurs_ids)
        
        dashboard.utilisateurs_partages.add(*utilisateurs)
        dashboard.partage = True
        dashboard.save()
        
        serializer = DashboardDetailSerializer(dashboard, context={'request': request})
        
        return Response({
            'message': 'Dashboard partagé avec succès.',
            'dashboard': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def definir_par_defaut(self, request, pk=None):
        """
        Action personnalisée : Définir comme dashboard par défaut.
        
        URL: POST /dashboards/{id}/definir-par-defaut/
        """
        dashboard = self.get_object()
        
        # Retirer le statut par défaut des autres dashboards de l'utilisateur
        Dashboard.objects.filter(
            proprietaire=request.user,
            par_defaut=True
        ).update(par_defaut=False)
        
        # Définir celui-ci comme par défaut
        dashboard.par_defaut = True
        dashboard.save()
        
        serializer = DashboardDetailSerializer(dashboard, context={'request': request})
        
        return Response({
            'message': 'Dashboard défini comme par défaut.',
            'dashboard': serializer.data
        })

# VIEWSET : KPIs
class KPIViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les KPIs.
    
    Endpoints :
    - GET /kpis/ : Liste tous les KPIs
    - POST /kpis/ : Crée un nouveau KPI
    - GET /kpis/{id}/ : Détails d'un KPI
    - PUT/PATCH /kpis/{id}/ : Modifier un KPI
    - DELETE /kpis/{id}/ : Supprimer un KPI
    
    Actions personnalisées :
    - GET /kpis/actifs/ : KPIs actifs
    - GET /kpis/par-categorie/ : Filtrer par catégorie
    - GET /kpis/objectifs-atteints/ : KPIs avec objectifs atteints
    - GET /kpis/tableau-bord/ : Synthèse pour tableau de bord
    """
    queryset = KPI.objects.select_related('annee_academique', 'filiere').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return KPICreateSerializer
        elif self.action == 'retrieve':
            return KPIDetailSerializer
        return KPIListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        categorie = self.request.query_params.get('categorie')
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        
        actif = self.request.query_params.get('actif')
        if actif is not None:
            queryset = queryset.filter(actif=(actif.lower() == 'true'))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """
        Action personnalisée : KPIs actifs.
        
        URL: GET /kpis/actifs/
        """
        kpis = self.get_queryset().filter(actif=True)
        serializer = self.get_serializer(kpis, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Action personnalisée : Filtrer par catégorie.
        
        URL: GET /kpis/par-categorie/?categorie={categorie}
        """
        categorie = request.query_params.get('categorie')
        
        if not categorie:
            return Response(
                {'error': 'Le paramètre categorie est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        kpis = self.get_queryset().filter(categorie=categorie, actif=True)
        serializer = self.get_serializer(kpis, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def objectifs_atteints(self, request):
        """
        Action personnalisée : KPIs avec objectifs atteints.
        
        URL: GET /kpis/objectifs-atteints/
        """
        kpis = [kpi for kpi in self.get_queryset().filter(actif=True) if kpi.est_objectif_atteint()]
        serializer = self.get_serializer(kpis, many=True)
        
        return Response({
            'count': len(kpis),
            'kpis': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def tableau_bord(self, request):
        """
        Action personnalisée : Synthèse pour tableau de bord.
        
        URL: GET /kpis/tableau-bord/
        """
        kpis_actifs = self.get_queryset().filter(actif=True)
        
        total = kpis_actifs.count()
        avec_objectif = kpis_actifs.exclude(objectif__isnull=True).count()
        objectifs_atteints = len([kpi for kpi in kpis_actifs if kpi.est_objectif_atteint()])
        
        par_categorie = kpis_actifs.values('categorie').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_kpis': total,
            'avec_objectif': avec_objectif,
            'objectifs_atteints': objectifs_atteints,
            'taux_reussite': (objectifs_atteints / avec_objectif * 100) if avec_objectif > 0 else 0,
            'repartition_par_categorie': list(par_categorie),
        })
