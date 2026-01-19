# Endpoints de l'API pour emploi du temps

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg
from django.http import HttpResponse

from .models import Batiment, Salle, Creneau, Cours, ConflitSalle
from .serializers import (
    BatimentSerializer,
    SalleSerializer,
    CreneauSerializer,
    CoursSerializer,
    ConflitSalleSerializer,
    DetectionConflitsSerializer,
    ResolutionConflitSerializer,
    EmploiDuTempsSerializer,
    StatistiquesEmploiDuTempsSerializer
)
from apps.academic.models import AnneeAcademique
from .utils import (
    EmploiDuTempsPDF,
    EmploiDuTempsExcel,
    ConflitsPDF,
    PlanningEnseignantPDF
)

# BATIMENT VIEWSET
class BatimentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les bâtiments.
    
    Endpoints:
    - GET    /api/batiments/                → Liste
    - POST   /api/batiments/                → Créer
    - GET    /api/batiments/{id}/           → Détails
    - PUT    /api/batiments/{id}/           → Modifier
    - DELETE /api/batiments/{id}/           → Supprimer
    - GET    /api/batiments/{id}/salles/    → Salles du bâtiment
    - GET    /api/batiments/statistiques/   → Statistiques
    """
    
    queryset = Batiment.objects.all()
    serializer_class = BatimentSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['code', 'nom', 'adresse']
    ordering_fields = ['code', 'nom', 'nombre_etages', 'created_at']
    ordering = ['code']
    
    @action(detail=True, methods=['get'], url_path='salles')
    def salles(self, request, pk=None):
        """
        Liste des salles d'un bâtiment.
        GET /api/batiments/{id}/salles/
        """
        batiment = self.get_object()
        salles = batiment.salles.all()
        
        serializer = SalleSerializer(salles, many=True, context={'request': request})
        
        return Response({
            'batiment': {
                'id': batiment.id,
                'code': batiment.code,
                'nom': batiment.nom
            },
            'salles': serializer.data,
            'total': salles.count()
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques globales des bâtiments.
        GET /api/batiments/statistiques/
        """
        total = Batiment.objects.count()
        actifs = Batiment.objects.filter(is_active=True).count()
        
        # Nombre total de salles
        total_salles = Salle.objects.count()
        
        # Répartition par bâtiment
        par_batiment = Batiment.objects.annotate(
            nb_salles=Count('salles')
        ).values('code', 'nom', 'nb_salles')
        
        stats = {
            'total_batiments': total,
            'batiments_actifs': actifs,
            'total_salles': total_salles,
            'repartition': list(par_batiment)
        }
        
        return Response(stats)

# SALLE VIEWSET
class SalleViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les salles.
    
    Endpoints:
    - GET    /api/salles/                    → Liste
    - POST   /api/salles/                    → Créer
    - GET    /api/salles/{id}/               → Détails
    - PUT    /api/salles/{id}/               → Modifier
    - DELETE /api/salles/{id}/               → Supprimer
    - GET    /api/salles/{id}/cours/         → Cours dans cette salle
    - GET    /api/salles/{id}/disponibilite/ → Disponibilité
    - GET    /api/salles/disponibles/        → Salles disponibles
    - GET    /api/salles/statistiques/       → Statistiques
    """
    
    queryset = Salle.objects.select_related('batiment').all()
    serializer_class = SalleSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['batiment', 'type_salle', 'is_disponible', 'etage']
    search_fields = ['code', 'nom', 'equipements']
    ordering_fields = ['code', 'capacite', 'etage', 'created_at']
    ordering = ['batiment', 'etage', 'code']
    
    @action(detail=True, methods=['get'], url_path='cours')
    def cours(self, request, pk=None):
        """
        Liste des cours dans cette salle.
        GET /api/salles/{id}/cours/
        
        Query params: ?annee_academique_id=1
        """
        salle = self.get_object()
        
        annee_academique_id = request.query_params.get('annee_academique_id')
        
        cours = Cours.objects.filter(salle=salle, is_actif=True)
        
        if annee_academique_id:
            cours = cours.filter(annee_academique_id=annee_academique_id)
        
        cours = cours.select_related(
            'matiere', 'enseignant__user', 'filiere', 'creneau'
        ).order_by('creneau__jour', 'creneau__heure_debut')
        
        serializer = CoursSerializer(cours, many=True, context={'request': request})
        
        return Response({
            'salle': {
                'id': salle.id,
                'code': salle.code,
                'nom': salle.nom,
                'capacite': salle.capacite
            },
            'cours': serializer.data,
            'total': cours.count()
        })
    
    @action(detail=True, methods=['get'], url_path='disponibilite')
    def disponibilite(self, request, pk=None):
        """
        Vérifier la disponibilité d'une salle.
        GET /api/salles/{id}/disponibilite/
        
        Query params: ?creneau_id=1&annee_academique_id=1
        """
        salle = self.get_object()
        
        creneau_id = request.query_params.get('creneau_id')
        annee_academique_id = request.query_params.get('annee_academique_id')
        
        if not creneau_id:
            return Response(
                {'error': 'creneau_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Chercher cours existant
        cours_existant = Cours.objects.filter(
            salle=salle,
            creneau_id=creneau_id,
            is_actif=True
        )
        
        if annee_academique_id:
            cours_existant = cours_existant.filter(annee_academique_id=annee_academique_id)
        
        if cours_existant.exists():
            cours = cours_existant.first()
            return Response({
                'disponible': False,
                'cours_existant': {
                    'id': cours.id,
                    'matiere': cours.matiere.nom,
                    'filiere': cours.filiere.code,
                    'enseignant': cours.enseignant.user.get_full_name() if cours.enseignant else None
                }
            })
        
        return Response({
            'disponible': True
        })
    
    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        """
        Liste des salles disponibles pour un créneau.
        GET /api/salles/disponibles/
        
        Query params: ?creneau_id=1&annee_academique_id=1&capacite_min=30
        """
        creneau_id = request.query_params.get('creneau_id')
        annee_academique_id = request.query_params.get('annee_academique_id')
        capacite_min = request.query_params.get('capacite_min')
        
        if not creneau_id:
            return Response(
                {'error': 'creneau_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Salles occupées à ce créneau
        salles_occupees = Cours.objects.filter(
            creneau_id=creneau_id,
            is_actif=True
        )
        
        if annee_academique_id:
            salles_occupees = salles_occupees.filter(annee_academique_id=annee_academique_id)
        
        salles_occupees_ids = salles_occupees.values_list('salle_id', flat=True)
        
        # Salles disponibles
        salles_disponibles = Salle.objects.filter(
            is_disponible=True
        ).exclude(id__in=salles_occupees_ids)
        
        if capacite_min:
            salles_disponibles = salles_disponibles.filter(capacite__gte=int(capacite_min))
        
        serializer = self.get_serializer(salles_disponibles, many=True)
        
        return Response({
            'salles_disponibles': serializer.data,
            'total': salles_disponibles.count()
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques globales des salles.
        GET /api/salles/statistiques/
        """
        total = Salle.objects.count()
        disponibles = Salle.objects.filter(is_disponible=True).count()
        
        # Par type
        par_type = Salle.objects.values('type_salle').annotate(
            count=Count('id')
        )
        
        # Capacité totale
        capacite_totale = sum(Salle.objects.values_list('capacite', flat=True))
        capacite_moyenne = Salle.objects.aggregate(moyenne=Avg('capacite'))['moyenne'] or 0
        
        stats = {
            'total_salles': total,
            'disponibles': disponibles,
            'par_type': list(par_type),
            'capacite_totale': capacite_totale,
            'capacite_moyenne': round(capacite_moyenne, 2)
        }
        
        return Response(stats)

# CRENEAU VIEWSET
class CreneauViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les créneaux horaires.
    
    Endpoints:
    - GET    /api/creneaux/              → Liste
    - POST   /api/creneaux/              → Créer
    - GET    /api/creneaux/{id}/         → Détails
    - PUT    /api/creneaux/{id}/         → Modifier
    - DELETE /api/creneaux/{id}/         → Supprimer
    - GET    /api/creneaux/par-jour/     → Créneaux groupés par jour
    """
    
    queryset = Creneau.objects.all()
    serializer_class = CreneauSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['jour']
    search_fields = ['code']
    ordering_fields = ['jour', 'heure_debut', 'created_at']
    ordering = ['jour', 'heure_debut']
    
    @action(detail=False, methods=['get'], url_path='par-jour')
    def par_jour(self, request):
        """
        Créneaux groupés par jour.
        GET /api/creneaux/par-jour/
        """
        jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI', 'DIMANCHE']
        
        result = {}
        
        for jour in jours:
            creneaux = Creneau.objects.filter(jour=jour).order_by('heure_debut')
            serializer = self.get_serializer(creneaux, many=True)
            result[jour] = serializer.data
        
        return Response(result)

# COURS VIEWSET
class CoursViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les cours.
    
    Endpoints:
    - GET    /api/cours/                      → Liste
    - POST   /api/cours/                      → Créer
    - GET    /api/cours/{id}/                 → Détails
    - PUT    /api/cours/{id}/                 → Modifier
    - DELETE /api/cours/{id}/                 → Supprimer
    - GET    /api/cours/emploi-du-temps/      → Emploi du temps par filière
    - GET    /api/cours/par-enseignant/{id}/  → Cours d'un enseignant
    - GET    /api/cours/statistiques/         → Statistiques
    """
    
    queryset = Cours.objects.select_related(
        'annee_academique', 'matiere', 'enseignant__user',
        'filiere', 'salle', 'creneau'
    ).all()
    serializer_class = CoursSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'annee_academique', 'matiere', 'enseignant', 'filiere',
        'salle', 'creneau', 'type_cours', 'semestre', 'is_actif'
    ]
    search_fields = ['matiere__nom', 'matiere__code', 'filiere__nom']
    ordering_fields = ['created_at']
    ordering = ['creneau__jour', 'creneau__heure_debut']
    
    @action(detail=False, methods=['post'], url_path='emploi-du-temps')
    def emploi_du_temps(self, request):
        """
        Générer l'emploi du temps d'une filière.
        POST /api/cours/emploi-du-temps/
        
        Body:
        {
            "filiere_id": 1,
            "semestre": 1,
            "annee_academique_id": 1  (optionnel, par défaut année active)
        }
        """
        serializer = EmploiDuTempsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filiere_id = serializer.validated_data['filiere_id']
        semestre = serializer.validated_data['semestre']
        annee_academique_id = serializer.validated_data.get('annee_academique_id')
        
        # Si pas d'année spécifiée, prendre l'année active
        if not annee_academique_id:
            try:
                annee_active = AnneeAcademique.objects.get(is_active=True)
                annee_academique_id = annee_active.id
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Aucune année académique active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Récupérer les cours
        cours = Cours.objects.filter(
            filiere_id=filiere_id,
            semestre=semestre,
            annee_academique_id=annee_academique_id,
            is_actif=True
        ).select_related(
            'matiere', 'enseignant__user', 'salle', 'creneau'
        ).order_by('creneau__jour', 'creneau__heure_debut')
        
        # Grouper par jour
        jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
        emploi_du_temps = {}
        
        for jour in jours:
            cours_jour = cours.filter(creneau__jour=jour)
            serializer_cours = CoursSerializer(cours_jour, many=True, context={'request': request})
            emploi_du_temps[jour] = serializer_cours.data
        
        return Response({
            'filiere_id': filiere_id,
            'semestre': semestre,
            'annee_academique_id': annee_academique_id,
            'emploi_du_temps': emploi_du_temps,
            'total_cours': cours.count()
        })
    
    @action(detail=False, methods=['get'], url_path='par-enseignant/(?P<enseignant_id>[^/.]+)')
    def par_enseignant(self, request, enseignant_id=None):
        """
        Cours d'un enseignant.
        GET /api/cours/par-enseignant/{enseignant_id}/
        
        Query params: ?annee_academique_id=1
        """
        annee_academique_id = request.query_params.get('annee_academique_id')
        
        cours = Cours.objects.filter(
            enseignant_id=enseignant_id,
            is_actif=True
        )
        
        if annee_academique_id:
            cours = cours.filter(annee_academique_id=annee_academique_id)
        
        cours = cours.select_related(
            'matiere', 'filiere', 'salle', 'creneau'
        ).order_by('creneau__jour', 'creneau__heure_debut')
        
        serializer = self.get_serializer(cours, many=True)
        
        return Response({
            'enseignant_id': enseignant_id,
            'cours': serializer.data,
            'total': cours.count()
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques globales des cours.
        GET /api/cours/statistiques/
        
        Query params: ?annee_academique_id=1
        """
        annee_academique_id = request.query_params.get('annee_academique_id')
        
        cours = Cours.objects.filter(is_actif=True)
        
        if annee_academique_id:
            cours = cours.filter(annee_academique_id=annee_academique_id)
        
        total = cours.count()
        
        # Par type
        par_type = cours.values('type_cours').annotate(count=Count('id'))
        
        # Par semestre
        par_semestre = cours.values('semestre').annotate(count=Count('id'))
        
        stats = {
            'total_cours': total,
            'par_type': list(par_type),
            'par_semestre': list(par_semestre)
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'], url_path='emploi-du-temps-pdf')
    def emploi_du_temps_pdf(self, request):
        """
        Télécharger l'emploi du temps en PDF.
        POST /api/cours/emploi-du-temps-pdf/
        
        Body:
        {
            "filiere_id": 1,
            "semestre": 1,
            "annee_academique_id": 1
        }
        """
        serializer = EmploiDuTempsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filiere_id = serializer.validated_data['filiere_id']
        semestre = serializer.validated_data['semestre']
        annee_academique_id = serializer.validated_data.get('annee_academique_id')
        
        # Année académique
        if not annee_academique_id:
            try:
                annee_active = AnneeAcademique.objects.get(is_active=True)
                annee_academique_id = annee_active.id
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Aucune année académique active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            from apps.students.models import Filiere
            filiere = Filiere.objects.get(id=filiere_id)
            annee_academique = AnneeAcademique.objects.get(id=annee_academique_id)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les cours
        cours = Cours.objects.filter(
            filiere_id=filiere_id,
            semestre=semestre,
            annee_academique_id=annee_academique_id,
            is_actif=True
        ).select_related(
            'matiere', 'enseignant__user', 'salle', 'creneau'
        ).order_by('creneau__jour', 'creneau__heure_debut')
        
        # Grouper par jour
        jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
        cours_par_jour = {}
        
        for jour in jours:
            cours_jour = cours.filter(creneau__jour=jour)
            if cours_jour.exists():
                cours_par_jour[jour] = list(cours_jour)
        
        # Générer le PDF
        pdf_generator = EmploiDuTempsPDF(filiere, semestre, annee_academique, cours_par_jour)
        pdf_buffer = pdf_generator.generate()
        
        # Nom du fichier
        filename = f"Emploi_du_temps_{filiere.code}_S{semestre}_{annee_academique.code}.pdf"
        
        # Réponse HTTP
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @action(detail=False, methods=['post'], url_path='emploi-du-temps-excel')
    def emploi_du_temps_excel(self, request):
        """
        Télécharger l'emploi du temps en Excel.
        POST /api/cours/emploi-du-temps-excel/
        
        Body:
        {
            "filiere_id": 1,
            "semestre": 1,
            "annee_academique_id": 1
        }
        """
        serializer = EmploiDuTempsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filiere_id = serializer.validated_data['filiere_id']
        semestre = serializer.validated_data['semestre']
        annee_academique_id = serializer.validated_data.get('annee_academique_id')
        
        # Année académique
        if not annee_academique_id:
            try:
                annee_active = AnneeAcademique.objects.get(is_active=True)
                annee_academique_id = annee_active.id
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Aucune année académique active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            from apps.students.models import Filiere
            filiere = Filiere.objects.get(id=filiere_id)
            annee_academique = AnneeAcademique.objects.get(id=annee_academique_id)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les cours
        cours = Cours.objects.filter(
            filiere_id=filiere_id,
            semestre=semestre,
            annee_academique_id=annee_academique_id,
            is_actif=True
        ).select_related(
            'matiere', 'enseignant__user', 'salle', 'creneau'
        ).order_by('creneau__jour', 'creneau__heure_debut')
        
        # Grouper par jour
        jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
        cours_par_jour = {}
        
        for jour in jours:
            cours_jour = cours.filter(creneau__jour=jour)
            if cours_jour.exists():
                cours_par_jour[jour] = list(cours_jour)
        
        # Générer le Excel
        excel_generator = EmploiDuTempsExcel(filiere, semestre, annee_academique, cours_par_jour)
        excel_buffer = excel_generator.generate()
        
        # Nom du fichier
        filename = f"Emploi_du_temps_{filiere.code}_S{semestre}_{annee_academique.code}.xlsx"
        
        # Réponse HTTP
        response = HttpResponse(
            excel_buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @action(detail=False, methods=['get'], url_path='planning-enseignant-pdf/(?P<enseignant_id>[^/.]+)')
    def planning_enseignant_pdf(self, request, enseignant_id=None):
        """
        Télécharger le planning d'un enseignant en PDF.
        GET /api/cours/planning-enseignant-pdf/{enseignant_id}/
        
        Query params: ?annee_academique_id=1
        """
        annee_academique_id = request.query_params.get('annee_academique_id')
        
        # Année académique
        if not annee_academique_id:
            try:
                annee_academique = AnneeAcademique.objects.get(is_active=True)
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Aucune année académique active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            try:
                annee_academique = AnneeAcademique.objects.get(id=annee_academique_id)
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Année académique introuvable'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Enseignant
        try:
            from apps.students.models import Enseignant
            enseignant = Enseignant.objects.select_related('user').get(id=enseignant_id)
        except Enseignant.DoesNotExist:
            return Response(
                {'error': 'Enseignant introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les cours
        cours = Cours.objects.filter(
            enseignant_id=enseignant_id,
            annee_academique=annee_academique,
            is_actif=True
        ).select_related(
            'matiere', 'filiere', 'salle', 'creneau'
        ).order_by('creneau__jour', 'creneau__heure_debut')
        
        # Grouper par jour
        jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
        cours_par_jour = {}
        
        for jour in jours:
            cours_jour = cours.filter(creneau__jour=jour)
            if cours_jour.exists():
                cours_par_jour[jour] = list(cours_jour)
        
        # Générer le PDF
        pdf_generator = PlanningEnseignantPDF(enseignant, cours_par_jour, annee_academique)
        pdf_buffer = pdf_generator.generate()
        
        # Nom du fichier
        filename = f"Planning_{enseignant.user.last_name}_{annee_academique.code}.pdf"
        
        # Réponse HTTP
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

# CONFLIT SALLE VIEWSET
class ConflitSalleViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les conflits de salles.
    
    Endpoints:
    - GET    /api/conflits/                  → Liste
    - POST   /api/conflits/                  → Créer
    - GET    /api/conflits/{id}/             → Détails
    - PUT    /api/conflits/{id}/             → Modifier
    - DELETE /api/conflits/{id}/             → Supprimer
    - POST   /api/conflits/detecter/         → Détecter conflits
    - POST   /api/conflits/{id}/resoudre/    → Marquer résolu
    - GET    /api/conflits/statistiques/     → Statistiques
    """
    
    queryset = ConflitSalle.objects.select_related(
        'cours1__matiere', 'cours1__filiere', 'cours1__salle',
        'cours2__matiere', 'cours2__filiere', 'cours2__salle'
    ).all()
    serializer_class = ConflitSalleSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_conflit', 'statut']
    search_fields = ['description']
    ordering_fields = ['date_detection', 'date_resolution']
    ordering = ['-date_detection']
    
    @action(detail=False, methods=['post'], url_path='detecter')
    def detecter(self, request):
        """
        Détecter tous les conflits pour une année académique.
        POST /api/conflits/detecter/
        
        Body:
        {
            "annee_academique_id": 1
        }
        """
        serializer = DetectionConflitsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        annee_academique_id = serializer.validated_data['annee_academique_id']
        
        try:
            annee_academique = AnneeAcademique.objects.get(id=annee_academique_id)
        except AnneeAcademique.DoesNotExist:
            return Response(
                {'error': 'Année académique introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Lancer la détection
        conflits = ConflitSalle.detecter_conflits(annee_academique)
        
        serializer_result = self.get_serializer(conflits, many=True)
        
        return Response({
            'message': 'Détection terminée',
            'conflits_detectes': len(conflits),
            'conflits': serializer_result.data
        })
    
    @action(detail=True, methods=['post'], url_path='resoudre')
    def resoudre(self, request, pk=None):
        """
        Marquer un conflit comme résolu.
        POST /api/conflits/{id}/resoudre/
        
        Body:
        {
            "solution": "Cours déplacé en salle B203"
        }
        """
        conflit = self.get_object()
        
        serializer = ResolutionConflitSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        solution = serializer.validated_data['solution']
        
        conflit.marquer_resolu(solution)
        
        serializer_result = self.get_serializer(conflit)
        
        return Response({
            'message': 'Conflit marqué comme résolu',
            'conflit': serializer_result.data
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques des conflits.
        GET /api/conflits/statistiques/
        """
        total = ConflitSalle.objects.count()
        
        # Par statut
        par_statut = ConflitSalle.objects.values('statut').annotate(count=Count('id'))
        
        # Par type
        par_type = ConflitSalle.objects.values('type_conflit').annotate(count=Count('id'))
        
        # Conflits non résolus
        non_resolus = ConflitSalle.objects.filter(
            statut__in=['DETECTE', 'EN_COURS']
        ).count()
        
        stats = {
            'total': total,
            'non_resolus': non_resolus,
            'par_statut': list(par_statut),
            'par_type': list(par_type)
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request):
        """
        Exporter la liste des conflits en PDF.
        GET /api/conflits/export-pdf/
        
        Query params: ?annee_academique_id=1&statut=DETECTE
        """
        annee_academique_id = request.query_params.get('annee_academique_id')
        statut = request.query_params.get('statut')
        
        # Année académique
        if not annee_academique_id:
            try:
                annee_academique = AnneeAcademique.objects.get(is_active=True)
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Aucune année académique active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            try:
                annee_academique = AnneeAcademique.objects.get(id=annee_academique_id)
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Année académique introuvable'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Filtrer les conflits
        conflits = ConflitSalle.objects.filter(
            cours1__annee_academique=annee_academique
        ).select_related(
            'cours1__matiere', 'cours1__filiere', 'cours1__salle',
            'cours2__matiere', 'cours2__filiere', 'cours2__salle'
        )
        
        # Filtrer par statut si demandé
        if statut:
            conflits = conflits.filter(statut=statut)
        
        conflits = conflits.order_by('-date_detection')
        
        # Générer le PDF
        pdf_generator = ConflitsPDF(list(conflits), annee_academique)
        pdf_buffer = pdf_generator.generate()
        
        # Nom du fichier
        filename = f"Rapport_Conflits_{annee_academique.code}.pdf"
        
        # Réponse HTTP
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
