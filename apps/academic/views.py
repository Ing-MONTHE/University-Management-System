# Endpoints de l'API académique

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import AnneeAcademique, Faculte, Departement, Filiere, Matiere
from .serializers import (
    AnneeAcademiqueSerializer,
    FaculteSerializer,
    DepartementSerializer,
    FiliereSerializer,
    MatiereSerializer,
    MatiereSimpleSerializer
)

# ANNEE ACADEMIQUE VIEWSET
class AnneeAcademiqueViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les années académiques.
    
    Endpoints:
    - GET    /api/annees-academiques/          → Liste
    - POST   /api/annees-academiques/          → Créer
    - GET    /api/annees-academiques/{id}/     → Détails
    - PUT    /api/annees-academiques/{id}/     → Modifier
    - PATCH  /api/annees-academiques/{id}/     → Modifier partiellement
    - DELETE /api/annees-academiques/{id}/     → Supprimer
    - POST   /api/annees-academiques/{id}/activate/  → Activer
    """
    
    queryset = AnneeAcademique.objects.all()
    serializer_class = AnneeAcademiqueSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['code']
    ordering_fields = ['date_debut', 'date_fin', 'created_at']
    ordering = ['-date_debut']
    
    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """
        Activer une année académique.
        POST /api/annees-academiques/{id}/activate/
        
        Désactive automatiquement toutes les autres années.
        """
        annee = self.get_object()
        annee.activate()
        
        serializer = self.get_serializer(annee)
        return Response({
            'message': f'Année académique {annee.code} activée avec succès',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='active')
    def get_active(self, request):
        """
        Obtenir l'année académique active.
        GET /api/annees-academiques/active/
        """
        try:
            annee = AnneeAcademique.objects.get(is_active=True)
            serializer = self.get_serializer(annee)
            return Response(serializer.data)
        except AnneeAcademique.DoesNotExist:
            return Response(
                {'error': 'Aucune année académique active'},
                status=status.HTTP_404_NOT_FOUND
            )

# FACULTE VIEWSET
class FaculteViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les facultés.
    
    Endpoints:
    - GET    /api/facultes/                    → Liste
    - POST   /api/facultes/                    → Créer
    - GET    /api/facultes/{id}/               → Détails
    - PUT    /api/facultes/{id}/               → Modifier
    - DELETE /api/facultes/{id}/               → Supprimer
    - GET    /api/facultes/{id}/departements/  → Départements de la faculté
    - GET    /api/facultes/{id}/statistiques/  → Statistiques
    """
    
    queryset = Faculte.objects.all()
    serializer_class = FaculteSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'nom', 'doyen']
    ordering_fields = ['nom', 'code', 'created_at']
    ordering = ['nom']
    
    @action(detail=True, methods=['get'], url_path='departements')
    def departements(self, request, pk=None):
        """
        Liste des départements d'une faculté.
        GET /api/facultes/{id}/departements/
        """
        faculte = self.get_object()
        departements = faculte.departements.all()
        
        from .serializers import DepartementSerializer
        serializer = DepartementSerializer(departements, many=True)
        
        return Response({
            'faculte': FaculteSerializer(faculte).data,
            'departements': serializer.data,
            'count': departements.count()
        })
    
    @action(detail=True, methods=['get'], url_path='statistiques')
    def statistiques(self, request, pk=None):
        """
        Statistiques d'une faculté.
        GET /api/facultes/{id}/statistiques/
        """
        faculte = self.get_object()
        
        stats = {
            'faculte': faculte.nom,
            'code': faculte.code,
            'departements': faculte.departements.count(),
            'filieres': sum(d.filieres.count() for d in faculte.departements.all()),
            'etudiants': faculte.get_etudiants_count(),
        }
        
        return Response(stats)

# DEPARTEMENT VIEWSET
class DepartementViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les départements.
    
    Endpoints:
    - GET    /api/departements/              → Liste
    - POST   /api/departements/              → Créer
    - GET    /api/departements/{id}/         → Détails
    - PUT    /api/departements/{id}/         → Modifier
    - DELETE /api/departements/{id}/         → Supprimer
    - GET    /api/departements/{id}/filieres/ → Filières du département
    """
    
    queryset = Departement.objects.select_related('faculte').all()
    serializer_class = DepartementSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculte']
    search_fields = ['code', 'nom', 'chef_departement']
    ordering_fields = ['nom', 'code', 'created_at']
    ordering = ['nom']
    
    @action(detail=True, methods=['get'], url_path='filieres')
    def filieres(self, request, pk=None):
        """
        Liste des filières d'un département.
        GET /api/departements/{id}/filieres/
        """
        departement = self.get_object()
        filieres = departement.filieres.all()
        
        from .serializers import FiliereSerializer
        serializer = FiliereSerializer(filieres, many=True)
        
        return Response({
            'departement': DepartementSerializer(departement).data,
            'filieres': serializer.data,
            'count': filieres.count()
        })

# FILIERE VIEWSET
class FiliereViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les filières.
    
    Endpoints:
    - GET    /api/filieres/                  → Liste
    - POST   /api/filieres/                  → Créer
    - GET    /api/filieres/{id}/             → Détails
    - PUT    /api/filieres/{id}/             → Modifier
    - DELETE /api/filieres/{id}/             → Supprimer
    - GET    /api/filieres/{id}/matieres/    → Matières de la filière
    """
    
    queryset = Filiere.objects.select_related('departement__faculte').all()
    serializer_class = FiliereSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['departement', 'cycle', 'is_active']
    search_fields = ['code', 'nom']
    ordering_fields = ['nom', 'code', 'cycle', 'created_at']
    ordering = ['nom']
    
    @action(detail=True, methods=['get'], url_path='matieres')
    def matieres(self, request, pk=None):
        """
        Liste des matières d'une filière.
        GET /api/filieres/{id}/matieres/
        """
        filiere = self.get_object()
        matieres = filiere.matieres.all()
        
        serializer = MatiereSimpleSerializer(matieres, many=True)
        
        return Response({
            'filiere': FiliereSerializer(filiere).data,
            'matieres': serializer.data,
            'count': matieres.count()
        })
    
    @action(detail=True, methods=['post'], url_path='add-matiere')
    def add_matiere(self, request, pk=None):
        """
        Ajouter une matière à une filière.
        POST /api/filieres/{id}/add-matiere/
        
        Body: {"matiere_id": 5}
        """
        filiere = self.get_object()
        matiere_id = request.data.get('matiere_id')
        
        if not matiere_id:
            return Response(
                {'error': 'matiere_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            matiere = Matiere.objects.get(id=matiere_id)
            matiere.filieres.add(filiere)
            
            return Response({
                'message': f'Matière {matiere.nom} ajoutée à {filiere.nom}',
                'matiere': MatiereSimpleSerializer(matiere).data
            })
        except Matiere.DoesNotExist:
            return Response(
                {'error': 'Matière introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

# MATIERE VIEWSET
class MatiereViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les matières.
    
    Endpoints:
    - GET    /api/matieres/          → Liste
    - POST   /api/matieres/          → Créer
    - GET    /api/matieres/{id}/     → Détails
    - PUT    /api/matieres/{id}/     → Modifier
    - DELETE /api/matieres/{id}/     → Supprimer
    """
    
    queryset = Matiere.objects.prefetch_related('filieres').all()
    serializer_class = MatiereSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['semestre', 'is_optionnelle']
    search_fields = ['code', 'nom']
    ordering_fields = ['nom', 'code', 'coefficient', 'credits', 'created_at']
    ordering = ['semestre', 'nom']
    
    @action(detail=False, methods=['get'], url_path='par-semestre/(?P<semestre>[^/.]+)')
    def par_semestre(self, request, semestre=None):
        """
        Liste des matières par semestre.
        GET /api/matieres/par-semestre/1/
        GET /api/matieres/par-semestre/2/
        """
        try:
            semestre_int = int(semestre)
            if semestre_int not in [1, 2]:
                raise ValueError
        except ValueError:
            return Response(
                {'error': 'Semestre doit être 1 ou 2'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        matieres = Matiere.objects.filter(semestre=semestre_int)
        serializer = MatiereSimpleSerializer(matieres, many=True)
        
        return Response({
            'semestre': semestre_int,
            'matieres': serializer.data,
            'count': matieres.count()
        })