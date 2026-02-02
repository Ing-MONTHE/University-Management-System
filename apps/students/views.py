# Endpoints de l'API pour étudiants et enseignants

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count

from .models import Etudiant, Enseignant, Inscription, Attribution
from .serializers import (
    EtudiantSerializer,
    EnseignantSerializer,
    InscriptionSerializer,
    AttributionSerializer
)
from .serializers import (
    EtudiantListSerializer,
    EtudiantCreateSerializer,
    EtudiantUpdateSerializer,
    EtudiantDetailSerializer
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
    serializer_class = EtudiantListSerializer
    permission_classes = [AllowAny]  # Pour le debug, à changer en [IsAuthenticated] en production
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'sexe', 'ville', 'nationalite']
    search_fields = ['matricule', 'user__first_name', 'user__last_name', 'telephone', 'email_personnel']
    ordering_fields = ['matricule', 'created_at', 'user__last_name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action"""
        if self.action == 'create':
            return EtudiantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EtudiantUpdateSerializer
        elif self.action == 'retrieve':
            return EtudiantDetailSerializer
        return EtudiantListSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer un étudiant"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        etudiant = serializer.save()
        
        # Retourner avec le serializer de liste
        output_serializer = EtudiantListSerializer(etudiant, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Mettre à jour un étudiant"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        etudiant = serializer.save()
        
        # Retourner avec le serializer détaillé
        output_serializer = EtudiantDetailSerializer(etudiant, context={'request': request})
        return Response(output_serializer.data)
    
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
    
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """
        Statistiques pour le dashboard admin.
        GET /api/etudiants/dashboard-stats/
        """
        from django.db.models import Q
        from datetime import datetime, timedelta
        
        # Total étudiants
        total = Etudiant.objects.count()
        
        # Étudiants actifs
        actifs = Etudiant.objects.filter(statut='ACTIF').count()
        
        # Nouveaux inscrits (30 derniers jours)
        date_limite = datetime.now() - timedelta(days=30)
        nouveaux = Etudiant.objects.filter(created_at__gte=date_limite).count()
        
        # Par statut
        par_statut = {
            'actifs': Etudiant.objects.filter(statut='ACTIF').count(),
            'suspendus': Etudiant.objects.filter(statut='SUSPENDU').count(),
            'diplomes': Etudiant.objects.filter(statut='DIPLOME').count(),
            'exclus': Etudiant.objects.filter(statut='EXCLU').count(),
            'abandonnes': Etudiant.objects.filter(statut='ABANDONNE').count(),
        }
        
        # Par sexe
        par_sexe = {
            'masculin': Etudiant.objects.filter(sexe='M').count(),
            'feminin': Etudiant.objects.filter(sexe='F').count(),
        }
        
        # Taux de réussite (diplômés / total * 100)
        diplomes = par_statut['diplomes']
        taux_reussite = round((diplomes / total * 100), 2) if total > 0 else 0
        
        # Statistiques de paiement
        inscriptions = Inscription.objects.all()
        total_a_payer = inscriptions.aggregate(Sum('montant_inscription'))['montant_inscription__sum'] or 0
        total_paye = inscriptions.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0
        montant_impaye = total_a_payer - total_paye
        
        # Étudiants avec retard de paiement
        etudiants_impaye = Inscription.objects.filter(
            statut_paiement__in=['IMPAYE', 'PARTIEL']
        ).values('etudiant').distinct().count()
        
        return Response({
            'students': {
                'total': total,
                'actifs': actifs,
                'nouveaux': nouveaux,
                'taux_reussite': taux_reussite,
                'par_statut': par_statut,
                'par_sexe': par_sexe,
            },
            'finance': {
                'total_a_payer': float(total_a_payer),
                'total_paye': float(total_paye),
                'montant_impaye': float(montant_impaye),
                'etudiants_impaye': etudiants_impaye,
            }
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques globales des étudiants.
        GET /api/etudiants/statistiques/
        """
        from django.db.models import Q
        from datetime import datetime
        
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
        
        # Nouveaux inscrits cette année
        annee_courante = datetime.now().year
        nouveaux = Etudiant.objects.filter(
            created_at__year=annee_courante
        ).count()
        
        # Par filière
        par_filiere = Inscription.objects.filter(
            statut='INSCRIT'
        ).values('filiere__nom').annotate(
            count=Count('etudiant', distinct=True)
        ).order_by('-count')[:10]
        
        # Calculer taux de réussite (estimation basée sur diplômés vs total)
        taux_reussite = round((diplomes / total * 100), 2) if total > 0 else 0
        
        stats = {
            'total': total,
            'actifs': actifs,
            'nouveaux': nouveaux,
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
            'par_filiere': list(par_filiere),
            'top_nationalites': list(nationalites),
            'taux_reussite': taux_reussite
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """Import massif d'étudiants via CSV"""
        import csv
        from io import StringIO
        from django.contrib.auth import get_user_model
        from datetime import datetime
        
        User = get_user_model()
        fichier = request.FILES.get('fichier')
        
        if not fichier:
            return Response(
                {'error': 'Aucun fichier fourni'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Lire le CSV
            decoded_file = fichier.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(decoded_file))
            
            crees = 0
            erreurs = []
            doublons = 0
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Vérifier doublons (par email ou matricule si fourni)
                    email = row.get('email', '').strip()
                    if not email:
                        erreurs.append({
                            'ligne': row_num,
                            'erreur': 'Email requis'
                        })
                        continue
                    
                    if Etudiant.objects.filter(email_personnel=email).exists():
                        doublons += 1
                        continue
                    
                    # Créer l'utilisateur
                    nom = row.get('nom', '').strip()
                    prenom = row.get('prenom', '').strip()
                    
                    if not nom or not prenom:
                        erreurs.append({
                            'ligne': row_num,
                            'erreur': 'Nom et prénom requis'
                        })
                        continue
                    
                    # Générer username unique
                    username = f"{prenom.lower()}.{nom.lower()}"
                    counter = 1
                    original_username = username
                    while User.objects.filter(username=username).exists():
                        username = f"{original_username}{counter}"
                        counter += 1
                    
                    # Créer l'utilisateur
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=prenom,
                        last_name=nom,
                        password='changeme123'  # Mot de passe par défaut
                    )
                    
                    # Générer matricule
                    annee = datetime.now().year
                    matricule = Etudiant.generer_matricule(annee)
                    
                    # Créer l'étudiant
                    etudiant_data = {
                        'user': user,
                        'matricule': matricule,
                        'email_personnel': email,
                        'sexe': row.get('sexe', 'M').upper(),
                        'date_naissance': row.get('date_naissance'),
                        'lieu_naissance': row.get('lieu_naissance', ''),
                        'nationalite': row.get('nationalite', 'Camerounaise'),
                        'telephone': row.get('telephone', ''),
                        'adresse': row.get('adresse', ''),
                        'ville': row.get('ville', ''),
                        'pays': row.get('pays', 'Cameroun'),
                        'tuteur_nom': row.get('tuteur_nom', ''),
                        'tuteur_telephone': row.get('tuteur_telephone', ''),
                        'tuteur_email': row.get('tuteur_email', ''),
                        'statut': row.get('statut', 'ACTIF').upper()
                    }
                    
                    Etudiant.objects.create(**etudiant_data)
                    crees += 1
                    
                except Exception as e:
                    erreurs.append({
                        'ligne': row_num,
                        'erreur': str(e)
                    })
            
            return Response({
                'crees': crees,
                'doublons': doublons,
                'erreurs': erreurs,
                'total_lignes': csv_reader.line_num - 1
            })
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du traitement : {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def bulletin(self, request, pk=None):
        """Bulletin de notes de l'étudiant (JSON)"""
        etudiant = self.get_object()
        
        # Importer le modèle Note
        try:
            from apps.evaluations.models import Note
            notes = Note.objects.filter(
                etudiant=etudiant
            ).select_related('evaluation', 'evaluation__matiere')
        except ImportError:
            notes = []
        
        # Obtenir la filière actuelle
        filiere = etudiant.get_filiere_actuelle()
        
        bulletin_data = {
            'etudiant': {
                'matricule': etudiant.matricule,
                'nom_complet': f"{etudiant.user.last_name} {etudiant.user.first_name}",
                'filiere': filiere.nom if filiere else None,
                'photo': etudiant.photo.url if etudiant.photo else None,
            },
            'notes': [
                {
                    'matiere': note.evaluation.matiere.nom,
                    'evaluation': note.evaluation.titre,
                    'note': float(note.note),
                    'coefficient': note.evaluation.coefficient if hasattr(note.evaluation, 'coefficient') else 1,
                }
                for note in notes
            ]
        }
        
        return Response(bulletin_data)
    
    @action(detail=True, methods=['post'])
    def upload_photo(self, request, pk=None):
        """Upload de photo de profil"""
        etudiant = self.get_object()
        photo = request.FILES.get('photo')
        
        if not photo:
            return Response(
                {'error': 'Aucune photo fournie'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        etudiant.photo = photo
        etudiant.save()
        
        return Response({
            'message': 'Photo uploadée avec succès',
            'photo_url': etudiant.photo.url if etudiant.photo else None
        })

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