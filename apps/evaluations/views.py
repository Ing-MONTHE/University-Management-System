# Endpoints de l'API pour évaluations et notes

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q, Sum

from .models import SessionDeliberation, TypeEvaluation, Evaluation, Note, Resultat, MembreJury, DecisionJury
from .serializers import (
    SessionDeliberationSerializer,
    TypeEvaluationSerializer,
    EvaluationSerializer,
    NoteSerializer,
    ResultatSerializer,
    SaisieMultipleNotesSerializer,
    MembreJurySerializer,
    DecisionJurySerializer
)
from apps.students.models import Etudiant

# TYPE EVALUATION VIEWSET
class TypeEvaluationViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les types d'évaluations.
    
    Endpoints:
    - GET    /api/types-evaluations/         → Liste
    - POST   /api/types-evaluations/         → Créer
    - GET    /api/types-evaluations/{id}/    → Détails
    - PUT    /api/types-evaluations/{id}/    → Modifier
    - DELETE /api/types-evaluations/{id}/    → Supprimer
    """
    
    queryset = TypeEvaluation.objects.all()
    serializer_class = TypeEvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['code']
    search_fields = ['nom', 'description']
    ordering_fields = ['code', 'nom', 'created_at']
    ordering = ['code']

# EVALUATION VIEWSET
class EvaluationViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les évaluations.
    
    Endpoints:
    - GET    /api/evaluations/                    → Liste
    - POST   /api/evaluations/                    → Créer
    - GET    /api/evaluations/{id}/               → Détails
    - PUT    /api/evaluations/{id}/               → Modifier
    - DELETE /api/evaluations/{id}/               → Supprimer
    - GET    /api/evaluations/{id}/notes/         → Notes de l'évaluation
    - GET    /api/evaluations/{id}/statistiques/  → Statistiques
    """
    
    queryset = Evaluation.objects.select_related(
        'matiere', 'type_evaluation', 'annee_academique'
    ).all()
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['matiere', 'type_evaluation', 'annee_academique', 'date']
    search_fields = ['titre', 'matiere__nom', 'matiere__code']
    ordering_fields = ['date', 'titre', 'created_at']
    ordering = ['-date']
    
    @action(detail=True, methods=['get'], url_path='notes')
    def notes(self, request, pk=None):
        """
        Liste des notes pour cette évaluation.
        GET /api/evaluations/{id}/notes/
        """
        evaluation = self.get_object()
        notes = evaluation.notes.select_related('etudiant__user').all()
        
        serializer = NoteSerializer(notes, many=True, context={'request': request})
        
        return Response({
            'evaluation': {
                'id': evaluation.id,
                'titre': evaluation.titre,
                'matiere': evaluation.matiere.nom,
                'date': evaluation.date
            },
            'notes': serializer.data,
            'statistiques': {
                'total': notes.count(),
                'presents': evaluation.get_nombre_presents(),
                'absents': evaluation.get_nombre_absents(),
                'moyenne_classe': round(evaluation.get_moyenne_classe(), 2)
            }
        })
    
    @action(detail=True, methods=['get'], url_path='statistiques')
    def statistiques(self, request, pk=None):
        """
        Statistiques détaillées d'une évaluation.
        GET /api/evaluations/{id}/statistiques/
        """
        evaluation = self.get_object()
        notes = evaluation.notes.filter(absence=False)
        
        if not notes.exists():
            return Response({
                'message': 'Aucune note saisie pour cette évaluation'
            })
        
        # Calculs statistiques
        notes_values = notes.values_list('note_obtenue', flat=True)
        
        moyenne = evaluation.get_moyenne_classe()
        note_min = min(notes_values) if notes_values else 0
        note_max = max(notes_values) if notes_values else 0
        
        # Répartition par tranches
        excellent = notes.filter(note_obtenue__gte=18).count()
        tres_bien = notes.filter(note_obtenue__gte=16, note_obtenue__lt=18).count()
        bien = notes.filter(note_obtenue__gte=14, note_obtenue__lt=16).count()
        assez_bien = notes.filter(note_obtenue__gte=12, note_obtenue__lt=14).count()
        passable = notes.filter(note_obtenue__gte=10, note_obtenue__lt=12).count()
        insuffisant = notes.filter(note_obtenue__lt=10).count()
        
        stats = {
            'evaluation': {
                'titre': evaluation.titre,
                'matiere': evaluation.matiere.nom,
                'date': evaluation.date,
                'coefficient': float(evaluation.coefficient),
                'note_totale': float(evaluation.note_totale)
            },
            'effectifs': {
                'total_inscrits': notes.count() + evaluation.get_nombre_absents(),
                'presents': notes.count(),
                'absents': evaluation.get_nombre_absents()
            },
            'notes': {
                'moyenne': round(moyenne, 2),
                'minimum': float(note_min),
                'maximum': float(note_max)
            },
            'repartition': {
                'excellent': excellent,
                'tres_bien': tres_bien,
                'bien': bien,
                'assez_bien': assez_bien,
                'passable': passable,
                'insuffisant': insuffisant
            }
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'], url_path='dupliquer')
    def dupliquer(self, request, pk=None):
        """
        Dupliquer une évaluation.
        POST /api/evaluations/{id}/dupliquer/
        
        Body: {"titre": "Nouveau titre", "date": "2025-02-15"}
        """
        evaluation = self.get_object()
        
        nouveau_titre = request.data.get('titre')
        nouvelle_date = request.data.get('date')
        
        if not nouveau_titre or not nouvelle_date:
            return Response(
                {'error': 'titre et date requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer la copie
        nouvelle_eval = Evaluation.objects.create(
            matiere=evaluation.matiere,
            type_evaluation=evaluation.type_evaluation,
            annee_academique=evaluation.annee_academique,
            titre=nouveau_titre,
            date=nouvelle_date,
            coefficient=evaluation.coefficient,
            note_totale=evaluation.note_totale,
            duree=evaluation.duree,
            description=evaluation.description
        )
        
        serializer = self.get_serializer(nouvelle_eval)
        
        return Response({
            'message': 'Évaluation dupliquée avec succès',
            'evaluation': serializer.data
        }, status=status.HTTP_201_CREATED)

# NOTE VIEWSET
class NoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les notes.
    
    Endpoints:
    - GET    /api/notes/                      → Liste
    - POST   /api/notes/                      → Créer
    - GET    /api/notes/{id}/                 → Détails
    - PUT    /api/notes/{id}/                 → Modifier
    - DELETE /api/notes/{id}/                 → Supprimer
    - POST   /api/notes/saisie-multiple/      → Saisir plusieurs notes
    """
    
    queryset = Note.objects.select_related(
        'evaluation__matiere', 'etudiant__user'
    ).all()
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['evaluation', 'etudiant', 'absence']
    search_fields = ['etudiant__matricule', 'etudiant__user__first_name', 'etudiant__user__last_name']
    ordering_fields = ['date_saisie', 'note_obtenue']
    ordering = ['-date_saisie']
    
    @action(detail=False, methods=['post'], url_path='saisie-multiple')
    def saisie_multiple(self, request):
        """
        Saisir plusieurs notes en une fois.
        POST /api/notes/saisie-multiple/
        
        Body:
        {
            "evaluation_id": 1,
            "notes": [
                {
                    "etudiant_id": 1,
                    "note_obtenue": 15.5,
                    "absence": false,
                    "appreciations": "Bon travail"
                },
                {
                    "etudiant_id": 2,
                    "absence": true
                }
            ]
        }
        """
        serializer = SaisieMultipleNotesSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        evaluation_id = serializer.validated_data['evaluation_id']
        notes_data = serializer.validated_data['notes']
        
        # Vérifier que l'évaluation existe
        try:
            evaluation = Evaluation.objects.get(id=evaluation_id)
        except Evaluation.DoesNotExist:
            return Response(
                {'error': 'Évaluation introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        notes_creees = []
        notes_modifiees = []
        erreurs = []
        
        for note_data in notes_data:
            etudiant_id = note_data['etudiant_id']
            
            try:
                etudiant = Etudiant.objects.get(id=etudiant_id)
            except Etudiant.DoesNotExist:
                erreurs.append(f"Étudiant {etudiant_id} introuvable")
                continue
            
            # Vérifier si la note existe déjà
            note, created = Note.objects.get_or_create(
                evaluation=evaluation,
                etudiant=etudiant,
                defaults={
                    'note_obtenue': note_data.get('note_obtenue'),
                    'note_sur': evaluation.note_totale,
                    'absence': note_data.get('absence', False),
                    'appreciations': note_data.get('appreciations', '')
                }
            )
            
            if not created:
                # Mettre à jour la note existante
                note.note_obtenue = note_data.get('note_obtenue')
                note.absence = note_data.get('absence', False)
                note.appreciations = note_data.get('appreciations', '')
                note.save()
                notes_modifiees.append(note.id)
            else:
                notes_creees.append(note.id)
        
        return Response({
            'message': 'Saisie multiple terminée',
            'notes_creees': len(notes_creees),
            'notes_modifiees': len(notes_modifiees),
            'erreurs': erreurs
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='par-etudiant/(?P<etudiant_id>[^/.]+)')
    def par_etudiant(self, request, etudiant_id=None):
        """
        Notes d'un étudiant.
        GET /api/notes/par-etudiant/{etudiant_id}/
        """
        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
        except Etudiant.DoesNotExist:
            return Response(
                {'error': 'Étudiant introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        notes = Note.objects.filter(etudiant=etudiant).select_related(
            'evaluation__matiere', 'evaluation__type_evaluation'
        )
        
        serializer = self.get_serializer(notes, many=True)
        
        return Response({
            'etudiant': {
                'id': etudiant.id,
                'matricule': etudiant.matricule,
                'nom_complet': etudiant.user.get_full_name()
            },
            'notes': serializer.data,
            'total': notes.count()
        })

# RESULTAT VIEWSET
class ResultatViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les résultats.
    
    Endpoints:
    - GET    /api/resultats/                     → Liste
    - POST   /api/resultats/                     → Créer
    - GET    /api/resultats/{id}/                → Détails
    - PUT    /api/resultats/{id}/                → Modifier
    - DELETE /api/resultats/{id}/                → Supprimer
    - POST   /api/resultats/calculer-moyenne/    → Calculer moyenne
    - GET    /api/resultats/bulletin/{etudiant}/ → Bulletin d'un étudiant
    """
    
    queryset = Resultat.objects.select_related(
        'etudiant__user', 'matiere', 'annee_academique'
    ).all()
    serializer_class = ResultatSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['etudiant', 'matiere', 'annee_academique', 'statut', 'mention']
    search_fields = ['etudiant__matricule', 'etudiant__user__first_name', 'matiere__nom']
    ordering_fields = ['moyenne_generale', 'rang', 'created_at']
    ordering = ['-moyenne_generale']
    
    @action(detail=False, methods=['post'], url_path='calculer-moyenne')
    def calculer_moyenne(self, request):
        """
        Calculer la moyenne d'un étudiant pour une matière.
        POST /api/resultats/calculer-moyenne/
        
        Body:
        {
            "etudiant_id": 1,
            "matiere_id": 1,
            "annee_academique_id": 1
        }
        """
        etudiant_id = request.data.get('etudiant_id')
        matiere_id = request.data.get('matiere_id')
        annee_academique_id = request.data.get('annee_academique_id')
        
        if not all([etudiant_id, matiere_id, annee_academique_id]):
            return Response(
                {'error': 'etudiant_id, matiere_id et annee_academique_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            matiere = __import__('apps.academic.models', fromlist=['Matiere']).Matiere.objects.get(id=matiere_id)
            annee_academique = __import__('apps.academic.models', fromlist=['AnneeAcademique']).AnneeAcademique.objects.get(id=annee_academique_id)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculer la moyenne
        moyenne = Resultat.calculer_moyenne(etudiant, matiere, annee_academique)
        
        # Créer ou mettre à jour le résultat
        resultat, created = Resultat.objects.update_or_create(
            etudiant=etudiant,
            matiere=matiere,
            annee_academique=annee_academique,
            defaults={'moyenne_generale': moyenne}
        )
        
        serializer = self.get_serializer(resultat)
        
        return Response({
            'message': 'Moyenne calculée et enregistrée',
            'action': 'créé' if created else 'mis à jour',
            'resultat': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='bulletin/(?P<etudiant_id>[^/.]+)')
    def bulletin(self, request, etudiant_id=None):
        """
        Bulletin complet d'un étudiant.
        GET /api/resultats/bulletin/{etudiant_id}/
        
        Query params: ?annee_academique_id=1
        """
        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
        except Etudiant.DoesNotExist:
            return Response(
                {'error': 'Étudiant introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        annee_academique_id = request.query_params.get('annee_academique_id')
        
        resultats = Resultat.objects.filter(etudiant=etudiant)
        
        if annee_academique_id:
            resultats = resultats.filter(annee_academique_id=annee_academique_id)
        
        serializer = self.get_serializer(resultats, many=True)
        
        # Calculs globaux
        total_credits = resultats.aggregate(total=Sum('credits_obtenus'))['total'] or 0
        moyenne_generale = resultats.aggregate(moyenne=Avg('moyenne_generale'))['moyenne'] or 0
        
        return Response({
            'etudiant': {
                'id': etudiant.id,
                'matricule': etudiant.matricule,
                'nom_complet': etudiant.user.get_full_name()
            },
            'resultats': serializer.data,
            'statistiques': {
                'nombre_matieres': resultats.count(),
                'total_credits': total_credits,
                'moyenne_generale': round(moyenne_generale, 2)
            }
        })
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request):
        """
        Statistiques générales des résultats.
        GET /api/resultats/statistiques/
        """
        total = Resultat.objects.count()
        
        # Par statut
        admis = Resultat.objects.filter(statut='ADMIS').count()
        ajournes = Resultat.objects.filter(statut='AJOURNE').count()
        rattrapage = Resultat.objects.filter(statut='RATTRAPAGE').count()
        
        # Par mention
        excellent = Resultat.objects.filter(mention='EXCELLENT').count()
        tres_bien = Resultat.objects.filter(mention='TB').count()
        bien = Resultat.objects.filter(mention='B').count()
        assez_bien = Resultat.objects.filter(mention='AB').count()
        passable = Resultat.objects.filter(mention='PASSABLE').count()
        
        # Moyenne générale
        moyenne = Resultat.objects.aggregate(moyenne=Avg('moyenne_generale'))['moyenne'] or 0
        
        stats = {
            'total': total,
            'par_statut': {
                'admis': admis,
                'ajournes': ajournes,
                'rattrapage': rattrapage
            },
            'par_mention': {
                'excellent': excellent,
                'tres_bien': tres_bien,
                'bien': bien,
                'assez_bien': assez_bien,
                'passable': passable
            },
            'moyenne_generale': round(moyenne, 2)
        }
        
        return Response(stats)

# SESSION DELIBERATION VIEWSET
class SessionDeliberationViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les sessions de délibération.
    
    Endpoints:
    - GET    /api/sessions-deliberation/                    → Liste
    - POST   /api/sessions-deliberation/                    → Créer
    - GET    /api/sessions-deliberation/{id}/               → Détails
    - PUT    /api/sessions-deliberation/{id}/               → Modifier
    - DELETE /api/sessions-deliberation/{id}/               → Supprimer
    - GET    /api/sessions-deliberation/{id}/decisions/     → Décisions
    - POST   /api/sessions-deliberation/{id}/generer-decisions/ → Générer décisions
    - POST   /api/sessions-deliberation/{id}/cloturer/      → Clôturer
    """
    
    queryset = SessionDeliberation.objects.select_related(
        'annee_academique', 'filiere'
    ).all()
    serializer_class = SessionDeliberationSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['annee_academique', 'filiere', 'niveau', 'semestre', 'statut']
    search_fields = ['filiere__nom', 'president_jury', 'lieu']
    ordering_fields = ['date_deliberation', 'created_at']
    ordering = ['-date_deliberation']
    
    @action(detail=True, methods=['get'], url_path='decisions')
    def decisions(self, request, pk=None):
        """
        Liste des décisions d'une session.
        GET /api/sessions-deliberation/{id}/decisions/
        """
        session = self.get_object()
        decisions = session.decisions.select_related('etudiant__user').all()
        
        from .serializers import DecisionJurySerializer
        serializer = DecisionJurySerializer(decisions, many=True, context={'request': request})
        
        return Response({
            'session': {
                'id': session.id,
                'filiere': session.filiere.nom,
                'niveau': session.niveau,
                'semestre': session.semestre
            },
            'decisions': serializer.data,
            'statistiques': {
                'total': decisions.count(),
                'admis': decisions.filter(decision='ADMIS').count(),
                'ajournes': decisions.filter(decision='AJOURNE').count(),
                'redoublement': decisions.filter(decision='REDOUBLEMENT').count(),
                'taux_reussite': session.get_taux_reussite()
            }
        })
    
    @action(detail=True, methods=['post'], url_path='generer-decisions')
    def generer_decisions(self, request, pk=None):
        """
        Générer automatiquement les décisions.
        POST /api/sessions-deliberation/{id}/generer-decisions/
        
        Body:
        {
            "seuil_admission": 10.0,
            "seuil_rattrapage": 7.0
        }
        """
        session = self.get_object()
        
        from .serializers import GenerationDecisionsSerializer
        serializer = GenerationDecisionsSerializer(data={
            'session_id': session.id,
            **request.data
        })
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        seuil_admission = serializer.validated_data['seuil_admission']
        seuil_rattrapage = serializer.validated_data['seuil_rattrapage']
        
        # Récupérer tous les étudiants de la filière/niveau
        inscriptions = __import__('apps.students.models', fromlist=['Inscription']).Inscription.objects.filter(
            filiere=session.filiere,
            niveau=session.niveau,
            annee_academique=session.annee_academique,
            statut='INSCRIT'
        ).select_related('etudiant')
        
        decisions_creees = 0
        decisions_modifiees = 0
        
        for inscription in inscriptions:
            etudiant = inscription.etudiant
            
            # Calculer la moyenne générale (simplifiée)
            resultats = Resultat.objects.filter(
                etudiant=etudiant,
                annee_academique=session.annee_academique
            )
            
            if not resultats.exists():
                continue
            
            moyenne = resultats.aggregate(moyenne=Avg('moyenne_generale'))['moyenne'] or 0
            credits_obtenus = resultats.aggregate(total=Sum('credits_obtenus'))['total'] or 0
            
            # Déterminer la décision
            if moyenne >= seuil_admission:
                decision = 'ADMIS'
            elif moyenne >= seuil_rattrapage:
                decision = 'AJOURNE'
            else:
                decision = 'REDOUBLEMENT'
            
            # Créer ou mettre à jour la décision
            decision_obj, created = DecisionJury.objects.update_or_create(
                session=session,
                etudiant=etudiant,
                defaults={
                    'moyenne_generale': moyenne,
                    'total_credits_obtenus': credits_obtenus,
                    'total_credits_requis': 60,  # À adapter selon le système
                    'decision': decision
                }
            )
            
            if created:
                decisions_creees += 1
            else:
                decisions_modifiees += 1
        
        # Calculer les rangs
        decisions = DecisionJury.objects.filter(session=session).order_by('-moyenne_generale')
        for rang, decision in enumerate(decisions, start=1):
            decision.rang_classe = rang
            decision.save()
        
        return Response({
            'message': 'Décisions générées avec succès',
            'decisions_creees': decisions_creees,
            'decisions_modifiees': decisions_modifiees,
            'total': decisions_creees + decisions_modifiees
        })
    
    @action(detail=True, methods=['post'], url_path='cloturer')
    def cloturer(self, request, pk=None):
        """
        Clôturer une session.
        POST /api/sessions-deliberation/{id}/cloturer/
        """
        session = self.get_object()
        
        if session.statut == 'VALIDEE':
            return Response(
                {'error': 'Cette session est déjà validée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.statut = 'TERMINEE'
        session.save()
        
        serializer = self.get_serializer(session)
        
        return Response({
            'message': 'Session clôturée avec succès',
            'session': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='valider')
    def valider(self, request, pk=None):
        """
        Valider une session.
        POST /api/sessions-deliberation/{id}/valider/
        """
        session = self.get_object()
        
        if session.statut != 'TERMINEE':
            return Response(
                {'error': 'La session doit être terminée avant d\'être validée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.statut = 'VALIDEE'
        session.save()
        
        serializer = self.get_serializer(session)
        
        return Response({
            'message': 'Session validée avec succès',
            'session': serializer.data
        })

# MEMBRE JURY VIEWSET
class MembreJuryViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les membres du jury.
    
    Endpoints:
    - GET    /api/membres-jury/               → Liste
    - POST   /api/membres-jury/               → Créer
    - GET    /api/membres-jury/{id}/          → Détails
    - PUT    /api/membres-jury/{id}/          → Modifier
    - DELETE /api/membres-jury/{id}/          → Supprimer
    """
    
    queryset = MembreJury.objects.select_related(
        'session', 'enseignant__user'
    ).all()
    serializer_class = MembreJurySerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'enseignant', 'role', 'present']
    search_fields = ['enseignant__matricule', 'enseignant__user__first_name', 'enseignant__user__last_name']
    ordering_fields = ['role', 'created_at']
    ordering = ['role']

# DECISION JURY VIEWSET
class DecisionJuryViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les décisions du jury.
    
    Endpoints:
    - GET    /api/decisions-jury/              → Liste
    - POST   /api/decisions-jury/              → Créer
    - GET    /api/decisions-jury/{id}/         → Détails
    - PUT    /api/decisions-jury/{id}/         → Modifier
    - DELETE /api/decisions-jury/{id}/         → Supprimer
    """
    
    queryset = DecisionJury.objects.select_related(
        'session', 'etudiant__user'
    ).all()
    serializer_class = DecisionJurySerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'etudiant', 'decision', 'mention']
    search_fields = ['etudiant__matricule', 'etudiant__user__first_name', 'etudiant__user__last_name']
    ordering_fields = ['moyenne_generale', 'rang_classe', 'created_at']
    ordering = ['rang_classe']