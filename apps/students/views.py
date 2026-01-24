# Endpoints de l'API pour étudiants et enseignants

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count

from .models import Etudiant, Enseignant, Inscription, Attribution
from .serializers import (
    EtudiantSerializer,
    EnseignantSerializer,
    InscriptionSerializer,
    AttributionSerializer
)

# ETUDIANT VIEWSET
class EtudiantViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les étudiants.
    
    Endpoints:
    - GET    /api/etudiants/                   → Liste
    - POST   /api/etudiants/                   → Créer
    - GET    /api/etudiants/{id}/              → Détails
    - PUT    /api/etudiants/{id}/              → Modifier
    - DELETE /api/etudiants/{id}/              → Supprimer
    - GET    /api/etudiants/{id}/inscriptions/ → Inscriptions
    - GET    /api/etudiants/statistiques/      → Statistiques
    """
    
    queryset = Etudiant.objects.select_related('user').all()
    serializer_class = EtudiantSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'sexe', 'ville', 'nationalite']
    search_fields = ['matricule', 'user__first_name', 'user__last_name', 'telephone', 'email_personnel']
    ordering_fields = ['matricule', 'created_at', 'user__last_name']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'], url_path='inscriptions')
    def inscriptions(self, request, pk=None):
        """
        Liste des inscriptions d'un étudiant.
        GET /api/etudiants/{id}/inscriptions/
        """
        etudiant = self.get_object()
        inscriptions = etudiant.inscriptions.all()
        
        serializer = InscriptionSerializer(inscriptions, many=True, context={'request': request})
        
        return Response({
            'etudiant': {
                'id': etudiant.id,
                'matricule': etudiant.matricule,
                'nom_complet': etudiant.user.get_full_name()
            },
            'inscriptions': serializer.data,
            'count': inscriptions.count()
        })
    
    @action(detail=True, methods=['get'], url_path='inscription-active')
    def inscription_active(self, request, pk=None):
        """
        Inscription active de l'étudiant.
        GET /api/etudiants/{id}/inscription-active/
        """
        etudiant = self.get_object()
        inscriptions = etudiant.get_inscriptions_actives()
        
        if inscriptions.exists():
            serializer = InscriptionSerializer(inscriptions, many=True, context={'request': request})
            return Response(serializer.data)
        
        return Response(
            {'message': 'Aucune inscription active'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques globales des étudiants.
        GET /api/etudiants/statistiques/
        """
        total = Etudiant.objects.count()
        actifs = Etudiant.objects.filter(statut='ACTIF').count()
        suspendus = Etudiant.objects.filter(statut='SUSPENDU').count()
        diplomes = Etudiant.objects.filter(statut='DIPLOME').count()
        abandonnes = Etudiant.objects.filter(statut='ABANDONNE').count()
        
        # Par sexe
        masculin = Etudiant.objects.filter(sexe='M').count()
        feminin = Etudiant.objects.filter(sexe='F').count()
        
        # Par nationalité (top 5)
        nationalites = Etudiant.objects.values('nationalite').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        stats = {
            'total': total,
            'par_statut': {
                'actifs': actifs,
                'suspendus': suspendus,
                'diplomes': diplomes,
                'abandonnes': abandonnes
            },
            'par_sexe': {
                'masculin': masculin,
                'feminin': feminin
            },
            'top_nationalites': list(nationalites)
        }
        
        return Response(stats)

# ENSEIGNANT VIEWSET
class EnseignantViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les enseignants.
    
    Endpoints:
    - GET    /api/enseignants/                    → Liste
    - POST   /api/enseignants/                    → Créer
    - GET    /api/enseignants/{id}/               → Détails
    - PUT    /api/enseignants/{id}/               → Modifier
    - DELETE /api/enseignants/{id}/               → Supprimer
    - GET    /api/enseignants/{id}/attributions/  → Attributions
    - GET    /api/enseignants/statistiques/       → Statistiques
    """
    
    queryset = Enseignant.objects.select_related('user', 'departement').all()
    serializer_class = EnseignantSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['departement', 'grade', 'statut', 'sexe']
    search_fields = ['matricule', 'user__first_name', 'user__last_name', 'specialite', 'telephone']
    ordering_fields = ['matricule', 'grade', 'date_embauche', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'], url_path='attributions')
    def attributions(self, request, pk=None):
        """
        Liste des attributions d'un enseignant.
        GET /api/enseignants/{id}/attributions/
        """
        enseignant = self.get_object()
        attributions = enseignant.attributions.all()
        
        serializer = AttributionSerializer(attributions, many=True, context={'request': request})
        
        return Response({
            'enseignant': {
                'id': enseignant.id,
                'matricule': enseignant.matricule,
                'nom_complet': enseignant.user.get_full_name(),
                'grade': enseignant.get_grade_display()
            },
            'attributions': serializer.data,
            'count': attributions.count()
        })
    
    @action(detail=True, methods=['get'], url_path='charge-horaire')
    def charge_horaire(self, request, pk=None):
        """
        Charge horaire totale d'un enseignant.
        GET /api/enseignants/{id}/charge-horaire/
        """
        enseignant = self.get_object()
        
        # Année académique active
        from apps.academic.models import AnneeAcademique
        try:
            annee_active = AnneeAcademique.objects.get(is_active=True)
        except AnneeAcademique.DoesNotExist:
            return Response(
                {'error': 'Aucune année académique active'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Attributions de l'année active
        attributions = enseignant.attributions.filter(annee_academique=annee_active)
        
        # Calcul par type
        total_cm = attributions.filter(type_enseignement='CM').aggregate(
            total=Sum('volume_horaire_assigne')
        )['total'] or 0
        
        total_td = attributions.filter(type_enseignement='TD').aggregate(
            total=Sum('volume_horaire_assigne')
        )['total'] or 0
        
        total_tp = attributions.filter(type_enseignement='TP').aggregate(
            total=Sum('volume_horaire_assigne')
        )['total'] or 0
        
        total = total_cm + total_td + total_tp
        
        return Response({
            'enseignant': enseignant.user.get_full_name(),
            'annee_academique': annee_active.code,
            'charge_horaire': {
                'cm': total_cm,
                'td': total_td,
                'tp': total_tp,
                'total': total
            },
            'nombre_matieres': attributions.values('matiere').distinct().count()
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques globales des enseignants.
        GET /api/enseignants/statistiques/
        """
        total = Enseignant.objects.count()
        actifs = Enseignant.objects.filter(statut='ACTIF').count()
        en_conge = Enseignant.objects.filter(statut='EN_CONGE').count()
        retires = Enseignant.objects.filter(statut='RETIRE').count()
        
        # Par sexe
        masculin = Enseignant.objects.filter(sexe='M').count()
        feminin = Enseignant.objects.filter(sexe='F').count()
        
        # Par grade
        par_grade = Enseignant.objects.values('grade').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Par département
        par_departement = Enseignant.objects.filter(
            departement__isnull=False
        ).values('departement__nom', 'departement__code').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        stats = {
            'total': total,
            'par_statut': {
                'actifs': actifs,
                'en_conge': en_conge,
                'retires': retires
            },
            'par_sexe': {
                'masculin': masculin,
                'feminin': feminin
            },
            'par_grade': list(par_grade),
            'top_departements': list(par_departement)
        }
        
        return Response(stats)

# INSCRIPTION VIEWSET
class InscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les inscriptions.
    
    Endpoints:
    - GET    /api/inscriptions/              → Liste
    - POST   /api/inscriptions/              → Créer
    - GET    /api/inscriptions/{id}/         → Détails
    - PUT    /api/inscriptions/{id}/         → Modifier
    - DELETE /api/inscriptions/{id}/         → Supprimer
    - POST   /api/inscriptions/{id}/payer/   → Enregistrer paiement
    """
    
    queryset = Inscription.objects.select_related(
        'etudiant__user', 'filiere', 'annee_academique'
    ).all()
    serializer_class = InscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['etudiant', 'filiere', 'annee_academique', 'niveau', 'statut', 'statut_paiement']
    search_fields = ['etudiant__matricule', 'etudiant__user__first_name', 'etudiant__user__last_name']
    ordering_fields = ['date_inscription', 'niveau', 'montant_inscription']
    ordering = ['-date_inscription']
    
    @action(detail=True, methods=['post'], url_path='payer')
    def payer(self, request, pk=None):
        """
        Enregistrer un paiement.
        POST /api/inscriptions/{id}/payer/
        
        Body:
        {
            "montant": 50000
        }
        """
        inscription = self.get_object()
        montant = request.data.get('montant')
        
        if not montant:
            return Response(
                {'error': 'Le montant est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            montant = float(montant)
            if montant <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {'error': 'Montant invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ajouter le paiement
        inscription.montant_paye += montant
        inscription.save()  # Le statut_paiement se met à jour automatiquement
        
        serializer = self.get_serializer(inscription)
        
        return Response({
            'message': 'Paiement enregistré avec succès',
            'inscription': serializer.data,
            'nouveau_montant_paye': inscription.montant_paye,
            'reste_a_payer': inscription.get_reste_a_payer()
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques des inscriptions.
        GET /api/inscriptions/statistiques/
        """
        total = Inscription.objects.count()
        inscrites = Inscription.objects.filter(statut='INSCRIT').count()
        
        # Paiements
        complet = Inscription.objects.filter(statut_paiement='COMPLET').count()
        partiel = Inscription.objects.filter(statut_paiement='PARTIEL').count()
        impaye = Inscription.objects.filter(statut_paiement='IMPAYE').count()
        
        # Montants
        montants = Inscription.objects.aggregate(
            total_a_payer=Sum('montant_inscription'),
            total_paye=Sum('montant_paye')
        )
        
        stats = {
            'total': total,
            'par_statut': {
                'inscrites': inscrites,
                'abandonnees': Inscription.objects.filter(statut='ABANDONNE').count(),
                'transferees': Inscription.objects.filter(statut='TRANSFERE').count()
            },
            'par_paiement': {
                'complet': complet,
                'partiel': partiel,
                'impaye': impaye
            },
            'montants': {
                'total_a_payer': montants['total_a_payer'] or 0,
                'total_paye': montants['total_paye'] or 0,
                'reste_a_payer': (montants['total_a_payer'] or 0) - (montants['total_paye'] or 0)
            }
        }
        
        return Response(stats)

# ATTRIBUTION VIEWSET
class AttributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les attributions.
    
    Endpoints:
    - GET    /api/attributions/              → Liste
    - POST   /api/attributions/              → Créer
    - GET    /api/attributions/{id}/         → Détails
    - PUT    /api/attributions/{id}/         → Modifier
    - DELETE /api/attributions/{id}/         → Supprimer
    """
    
    queryset = Attribution.objects.select_related(
        'enseignant__user', 'matiere', 'annee_academique'
    ).all()
    serializer_class = AttributionSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['enseignant', 'matiere', 'annee_academique', 'type_enseignement']
    search_fields = ['enseignant__matricule', 'enseignant__user__first_name', 'matiere__code', 'matiere__nom']
    ordering_fields = ['created_at', 'volume_horaire_assigne']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'], url_path='par-matiere/(?P<matiere_id>[^/.]+)')
    def par_matiere(self, request, matiere_id=None):
        """
        Attributions pour une matière.
        GET /api/attributions/par-matiere/{matiere_id}/
        """
        attributions = Attribution.objects.filter(matiere_id=matiere_id)
        serializer = self.get_serializer(attributions, many=True)
        
        return Response({
            'matiere_id': matiere_id,
            'attributions': serializer.data,
            'count': attributions.count()
        })
