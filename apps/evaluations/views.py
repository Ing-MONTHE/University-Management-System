# Endpoints de l'API pour évaluations et notes - VERSION COMPLÉTÉE

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Sum, Max, Min, Count, Q
from decimal import Decimal

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
from apps.academic.models import Matiere

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

# EVALUATION VIEWSET - COMPLÉTÉ
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
    - POST   /api/evaluations/{id}/saisie-lot/    → ✨ NOUVEAU: Saisie en lot
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
        Si aucune note n'existe, retourne la liste des étudiants inscrits dans la matière.
        GET /api/evaluations/{id}/notes/
        """
        evaluation = self.get_object()
        notes_existantes = evaluation.notes.select_related('etudiant__user').all()
        
        # Si des notes existent, les retourner
        if notes_existantes.exists():
            serializer = NoteSerializer(notes_existantes, many=True, context={'request': request})
            
            return Response({
                'evaluation': {
                    'id': evaluation.id,
                    'titre': evaluation.titre,
                    'matiere': evaluation.matiere.nom,
                    'date': evaluation.date
                },
                'notes': serializer.data,
                'statistiques': {
                    'total': notes_existantes.count(),
                    'presents': evaluation.get_nombre_presents(),
                    'absents': evaluation.get_nombre_absents(),
                    'moyenne_classe': round(evaluation.get_moyenne_classe(), 2)
                }
            })
        
        # Sinon, retourner la liste des étudiants inscrits dans les filières de la matière
        from apps.students.models import Inscription
        
        # Récupérer toutes les filières qui ont cette matière
        filieres = evaluation.matiere.filieres.all()
        
        # Récupérer les étudiants inscrits dans ces filières pour l'année académique
        inscriptions = Inscription.objects.filter(
            filiere__in=filieres,
            annee_academique=evaluation.annee_academique,
            statut='INSCRIT'
        ).select_related('etudiant__user')
        
        # Récupérer les IDs uniques des étudiants
        etudiant_ids = inscriptions.values_list('etudiant_id', flat=True).distinct()
        
        # Récupérer les étudiants uniques
        from apps.students.models import Etudiant
        etudiants = Etudiant.objects.filter(id__in=etudiant_ids).select_related('user')
        
        # Créer des notes vides pour chaque étudiant
        notes_vides = []
        for etudiant in etudiants:
            photo_url = None
            if etudiant.photo:
                try:
                    photo_url = request.build_absolute_uri(etudiant.photo.url)
                except:
                    photo_url = None
            
            notes_vides.append({
                'id': None,
                'evaluation': evaluation.id,
                'etudiant': etudiant.id,
                'etudiant_details': {
                    'id': etudiant.id,
                    'matricule': etudiant.matricule,
                    'nom': etudiant.user.last_name or '',
                    'prenom': etudiant.user.first_name or '',
                    'photo_url': photo_url
                },
                'note_obtenue': None,
                'note_sur': float(evaluation.note_totale),
                'absence': False,
                'appreciations': '',
                'date_saisie': None
            })
        
        return Response({
            'evaluation': {
                'id': evaluation.id,
                'titre': evaluation.titre,
                'matiere': evaluation.matiere.nom,
                'date': evaluation.date
            },
            'notes': notes_vides,
            'statistiques': {
                'total': len(notes_vides),
                'presents': 0,
                'absents': 0,
                'moyenne_classe': 0
            }
        })
    
    @action(detail=True, methods=['post'], url_path='saisie-lot')
    def saisie_lot(self, request, pk=None):
        """
        ✨ NOUVEAU: Saisie des notes en lot pour une évaluation
        POST /api/evaluations/{id}/saisie-lot/
        
        Body:
        {
            "notes": [
                {"etudiant_id": 1, "note": 15.5, "absent": false},
                {"etudiant_id": 2, "note": null, "absent": true},
                ...
            ]
        }
        """
        evaluation = self.get_object()
        notes_data = request.data.get('notes', [])
        
        if not notes_data:
            return Response(
                {'error': 'Le champ "notes" est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created = 0
        updated = 0
        errors = []
        
        for note_item in notes_data:
            try:
                etudiant_id = note_item.get('etudiant_id')
                note_value = note_item.get('note')
                absent = note_item.get('absent', False)
                
                if not etudiant_id:
                    errors.append({
                        'error': 'etudiant_id manquant',
                        'data': note_item
                    })
                    continue
                
                # Vérifier que l'étudiant existe
                try:
                    etudiant = Etudiant.objects.get(id=etudiant_id)
                except Etudiant.DoesNotExist:
                    errors.append({
                        'etudiant_id': etudiant_id,
                        'error': f'Étudiant {etudiant_id} introuvable'
                    })
                    continue
                
                # Validation : note <= barème
                if not absent and note_value is not None:
                    note_decimal = Decimal(str(note_value))
                    if note_decimal > evaluation.note_totale:
                        errors.append({
                            'etudiant_id': etudiant_id,
                            'error': f'Note {note_value} supérieure au barème {evaluation.note_totale}'
                        })
                        continue
                    if note_decimal < 0:
                        errors.append({
                            'etudiant_id': etudiant_id,
                            'error': f'Note {note_value} ne peut pas être négative'
                        })
                        continue
                
                # Validation : si absent, pas de note
                if absent and note_value is not None:
                    note_value = None
                
                # Validation : si présent, note obligatoire
                if not absent and note_value is None:
                    errors.append({
                        'etudiant_id': etudiant_id,
                        'error': 'Note obligatoire si l\'étudiant n\'est pas absent'
                    })
                    continue
                
                # Créer ou mettre à jour
                note_obj, created_flag = Note.objects.update_or_create(
                    evaluation=evaluation,
                    etudiant=etudiant,
                    defaults={
                        'note_obtenue': None if absent else Decimal(str(note_value)),
                        'note_sur': evaluation.note_totale,
                        'absence': absent
                    }
                )
                
                if created_flag:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                errors.append({
                    'etudiant_id': note_item.get('etudiant_id'),
                    'error': str(e)
                })
        
        return Response({
            'success': True,
            'created': created,
            'updated': updated,
            'total_processed': created + updated,
            'errors': errors
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
                'message': 'Aucune note saisie pour cette évaluation',
                'nb_notes': 0
            })
        
        # Calculs statistiques
        notes_values = notes.values_list('note_obtenue', flat=True)
        
        stats_agg = notes.aggregate(
            moyenne=Avg('note_obtenue'),
            note_min=Min('note_obtenue'),
            note_max=Max('note_obtenue'),
            nb_notes=Count('id')
        )
        
        nb_absents = evaluation.notes.filter(absence=True).count()
        
        # Répartition par tranches (notes sur 20)
        bareme = float(evaluation.note_totale)
        excellent = notes.filter(note_obtenue__gte=bareme * 0.9).count()  # >= 18/20
        tres_bien = notes.filter(note_obtenue__gte=bareme * 0.8, note_obtenue__lt=bareme * 0.9).count()  # 16-18
        bien = notes.filter(note_obtenue__gte=bareme * 0.7, note_obtenue__lt=bareme * 0.8).count()  # 14-16
        assez_bien = notes.filter(note_obtenue__gte=bareme * 0.6, note_obtenue__lt=bareme * 0.7).count()  # 12-14
        passable = notes.filter(note_obtenue__gte=bareme * 0.5, note_obtenue__lt=bareme * 0.6).count()  # 10-12
        insuffisant = notes.filter(note_obtenue__lt=bareme * 0.5).count()  # < 10
        
        nb_reussis = notes.filter(note_obtenue__gte=bareme * 0.5).count()
        taux_reussite = (nb_reussis / stats_agg['nb_notes'] * 100) if stats_agg['nb_notes'] > 0 else 0
        
        return Response({
            'moyenne_classe': round(float(stats_agg['moyenne'] or 0), 2),
            'note_min': float(stats_agg['note_min'] or 0),
            'note_max': float(stats_agg['note_max'] or 0),
            'nb_notes': stats_agg['nb_notes'],
            'nb_absents': nb_absents,
            'nb_reussis': nb_reussis,
            'taux_reussite': round(taux_reussite, 2),
            'bareme': float(evaluation.note_totale),
            'distribution': {
                'excellent': excellent,
                'tres_bien': tres_bien,
                'bien': bien,
                'assez_bien': assez_bien,
                'passable': passable,
                'insuffisant': insuffisant
            }
        })
    
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
    ordering_fields = ['date_saisie', 'note_obtenue', 'created_at']
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
                {"etudiant_id": 1, "note_obtenue": 15, "absence": false},
                {"etudiant_id": 2, "note_obtenue": null, "absence": true}
            ]
        }
        """
        serializer = SaisieMultipleNotesSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        evaluation_id = serializer.validated_data['evaluation_id']
        notes_data = serializer.validated_data['notes']
        
        try:
            evaluation = Evaluation.objects.get(id=evaluation_id)
        except Evaluation.DoesNotExist:
            return Response(
                {'error': f'Évaluation {evaluation_id} introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_notes = []
        updated_notes = []
        errors = []
        
        for note_data in notes_data:
            try:
                etudiant_id = note_data['etudiant_id']
                note_obtenue = note_data.get('note_obtenue')
                absence = note_data.get('absence', False)
                appreciations = note_data.get('appreciations', '')
                
                # Créer ou mettre à jour la note
                note_obj, created = Note.objects.update_or_create(
                    evaluation=evaluation,
                    etudiant_id=etudiant_id,
                    defaults={
                        'note_obtenue': note_obtenue,
                        'note_sur': evaluation.note_totale,
                        'absence': absence,
                        'appreciations': appreciations
                    }
                )
                
                if created:
                    created_notes.append(NoteSerializer(note_obj).data)
                else:
                    updated_notes.append(NoteSerializer(note_obj).data)
                    
            except Exception as e:
                errors.append({
                    'etudiant_id': note_data.get('etudiant_id'),
                    'error': str(e)
                })
        
        return Response({
            'message': 'Notes saisies avec succès',
            'created': len(created_notes),
            'updated': len(updated_notes),
            'total': len(created_notes) + len(updated_notes),
            'errors': errors,
            'notes_created': created_notes,
            'notes_updated': updated_notes
        }, status=status.HTTP_201_CREATED)

# RESULTAT VIEWSET - COMPLÉTÉ
class ResultatViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les résultats.
    
    Endpoints:
    - GET    /api/resultats/                     → Liste
    - POST   /api/resultats/                     → Créer
    - GET    /api/resultats/{id}/                → Détails
    - PUT    /api/resultats/{id}/                → Modifier
    - DELETE /api/resultats/{id}/                → Supprimer
    - POST   /api/resultats/calculer-moyenne/    → ✨ NOUVEAU: Calculer moyenne
    - GET    /api/resultats/bulletin/            → ✨ NOUVEAU: Bulletin étudiant
    """
    
    queryset = Resultat.objects.select_related(
        'etudiant__user', 'matiere', 'annee_academique'
    ).all()
    serializer_class = ResultatSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['etudiant', 'matiere', 'annee_academique', 'statut', 'mention']
    search_fields = ['etudiant__matricule', 'etudiant__user__first_name', 'etudiant__user__last_name']
    ordering_fields = ['moyenne_generale', 'rang', 'created_at']
    ordering = ['-moyenne_generale']
    
    @action(detail=False, methods=['post'], url_path='calculer-moyenne')
    def calculer_moyenne(self, request):
        """
        ✨ NOUVEAU: Calcul automatique de la moyenne d'un étudiant pour une matière
        POST /api/resultats/calculer-moyenne/
        
        Body:
        {
            "etudiant_id": 1,
            "matiere_id": 5,
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
        
        # Vérifier l'existence des objets
        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            matiere = Matiere.objects.get(id=matiere_id)
        except (Etudiant.DoesNotExist, Matiere.DoesNotExist) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer toutes les notes de l'étudiant pour cette matière
        notes = Note.objects.filter(
            etudiant_id=etudiant_id,
            evaluation__matiere_id=matiere_id,
            evaluation__annee_academique_id=annee_academique_id,
            absence=False
        ).select_related('evaluation')
        
        if not notes.exists():
            return Response({
                'success': False,
                'moyenne': None,
                'message': 'Aucune note trouvée',
                'nb_evaluations': 0
            })
        
        # Calcul : Moyenne = Σ(note_sur_20 × coef) / Σ(coef)
        total_points = Decimal(0)
        total_coefs = Decimal(0)
        evaluations_details = []
        
        for note in notes:
            coef = note.evaluation.coefficient
            # Normaliser la note sur 20
            note_sur_20 = (note.note_obtenue / note.note_sur) * Decimal(20)
            total_points += note_sur_20 * coef
            total_coefs += coef
            
            evaluations_details.append({
                'evaluation': note.evaluation.titre,
                'note': float(note.note_obtenue),
                'bareme': float(note.note_sur),
                'note_sur_20': round(float(note_sur_20), 2),
                'coefficient': float(coef)
            })
        
        moyenne = total_points / total_coefs if total_coefs > 0 else Decimal(0)
        
        # Déterminer le statut
        if moyenne >= 10:
            statut = 'ADMIS'
        elif moyenne >= 8:
            statut = 'RATTRAPAGE'
        else:
            statut = 'AJOURNE'
        
        # Créer ou mettre à jour le Résultat
        resultat, created = Resultat.objects.update_or_create(
            etudiant_id=etudiant_id,
            matiere_id=matiere_id,
            annee_academique_id=annee_academique_id,
            defaults={
                'moyenne_generale': round(moyenne, 2),
                'statut': statut,
                'credits_obtenus': matiere.credits if statut == 'ADMIS' else 0
            }
        )
        
        return Response({
            'success': True,
            'moyenne': float(resultat.moyenne_generale),
            'matiere_id': matiere_id,
            'matiere_nom': matiere.nom,
            'etudiant_id': etudiant_id,
            'nb_evaluations': notes.count(),
            'evaluations': evaluations_details,
            'statut': statut,
            'credits_obtenus': matiere.credits if statut == 'ADMIS' else 0,
            'created': created
        })
    
    @action(detail=False, methods=['get'], url_path='bulletin')
    def bulletin(self, request):
        """
        ✨ NOUVEAU: Bulletin de notes d'un étudiant
        GET /api/resultats/bulletin/?etudiant_id={id}&annee_academique_id={id}
        """
        etudiant_id = request.query_params.get('etudiant_id')
        annee_academique_id = request.query_params.get('annee_academique_id')
        
        if not etudiant_id:
            return Response(
                {'error': 'etudiant_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            etudiant = Etudiant.objects.select_related('user', 'filiere').get(id=etudiant_id)
        except Etudiant.DoesNotExist:
            return Response(
                {'error': 'Étudiant introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Déterminer l'année académique
        if annee_academique_id:
            from apps.academic.models import AnneeAcademique
            try:
                annee_academique = AnneeAcademique.objects.get(id=annee_academique_id)
            except AnneeAcademique.DoesNotExist:
                return Response(
                    {'error': 'Année académique introuvable'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Prendre l'année académique active
            from apps.academic.models import AnneeAcademique
            annee_academique = AnneeAcademique.objects.filter(statut='EN_COURS').first()
            if not annee_academique:
                return Response(
                    {'error': 'Aucune année académique active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Récupérer la filière actuelle de l'étudiant
        filiere_actuelle = etudiant.get_filiere_actuelle()
        if not filiere_actuelle:
            return Response(
                {'error': 'Aucune filière active pour cet étudiant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer toutes les matières de sa filière
        matieres = Matiere.objects.filter(filieres=filiere_actuelle)
        
        bulletin_data = []
        total_points = Decimal(0)
        total_coefs = Decimal(0)
        total_credits = 0
        credits_obtenus = 0
        nb_matieres_acquises = 0
        
        for matiere in matieres:
            # Récupérer toutes les notes de l'étudiant pour cette matière
            notes = Note.objects.filter(
                etudiant=etudiant,
                evaluation__matiere=matiere,
                evaluation__annee_academique=annee_academique,
                absence=False
            ).select_related('evaluation', 'evaluation__type_evaluation')
            
            notes_detail = []
            moyenne_matiere = None
            
            if notes.exists():
                # Calculer la moyenne de la matière
                total_points_matiere = Decimal(0)
                total_coefs_matiere = Decimal(0)
                
                for note in notes:
                    coef = note.evaluation.coefficient
                    note_sur_20 = (note.note_obtenue / note.note_sur) * Decimal(20)
                    total_points_matiere += note_sur_20 * coef
                    total_coefs_matiere += coef
                    
                    notes_detail.append({
                        'evaluation': note.evaluation.titre,
                        'type': note.evaluation.type_evaluation.nom,
                        'note': float(note.note_obtenue),
                        'bareme': float(note.note_sur),
                        'note_sur_20': round(float(note_sur_20), 2),
                        'coefficient': float(coef),
                        'date': str(note.evaluation.date)
                    })
                
                if total_coefs_matiere > 0:
                    moyenne_matiere = total_points_matiere / total_coefs_matiere
            
            # Déterminer si la matière est acquise
            acquis = moyenne_matiere is not None and moyenne_matiere >= 10
            
            # Calcul pour moyenne générale
            if moyenne_matiere is not None:
                total_points += moyenne_matiere * matiere.coefficient
                total_coefs += matiere.coefficient
                
                if acquis:
                    credits_obtenus += matiere.credits
                    nb_matieres_acquises += 1
            
            total_credits += matiere.credits
            
            bulletin_data.append({
                'matiere_code': matiere.code,
                'matiere_nom': matiere.nom,
                'notes': notes_detail,
                'moyenne': round(float(moyenne_matiere), 2) if moyenne_matiere else None,
                'coefficient': float(matiere.coefficient),
                'credits_ects': matiere.credits,
                'acquis': acquis
            })
        
        # Moyenne générale
        moyenne_generale = total_points / total_coefs if total_coefs > 0 else Decimal(0)
        
        # Décision
        if moyenne_generale >= 10:
            decision = 'ADMIS'
        elif moyenne_generale >= 8:
            decision = 'RATTRAPAGE'
        else:
            decision = 'AJOURNE'
        
        # Mention (seulement si ADMIS)
        mention = None
        if decision == 'ADMIS':
            if moyenne_generale >= 16:
                mention = 'EXCELLENT'
            elif moyenne_generale >= 14:
                mention = 'TRES_BIEN'
            elif moyenne_generale >= 12:
                mention = 'BIEN'
            elif moyenne_generale >= 10:
                mention = 'ASSEZ_BIEN'
        
        return Response({
            'etudiant': {
                'id': etudiant.id,
                'matricule': etudiant.matricule,
                'nom_complet': f"{etudiant.user.first_name} {etudiant.user.last_name}",
                'photo_url': etudiant.photo.url if etudiant.photo else None,
                'filiere': etudiant.filiere.nom,
                'code_filiere': etudiant.filiere.code,
                'niveau': etudiant.niveau
            },
            'annee_academique': {
                'id': annee_academique.id,
                'libelle': annee_academique.libelle,
                'annee': annee_academique.annee
            },
            'matieres': bulletin_data,
            'moyenne_generale': round(float(moyenne_generale), 2),
            'total_credits': total_credits,
            'credits_obtenus': credits_obtenus,
            'decision': decision,
            'mention': mention,
            'nb_matieres': len(matieres),
            'nb_matieres_acquises': nb_matieres_acquises
        })

# SESSION DELIBERATION VIEWSET - AMÉLIORÉ
class SessionDeliberationViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les sessions de délibération.
    
    Endpoints:
    - GET    /api/sessions-deliberation/                      → Liste
    - POST   /api/sessions-deliberation/                      → Créer
    - GET    /api/sessions-deliberation/{id}/                 → Détails
    - PUT    /api/sessions-deliberation/{id}/                 → Modifier
    - DELETE /api/sessions-deliberation/{id}/                 → Supprimer
    - GET    /api/sessions-deliberation/{id}/decisions/       → Décisions
    - POST   /api/sessions-deliberation/{id}/generer-decisions/ → ✨ AMÉLIORÉ: Générer décisions
    - POST   /api/sessions-deliberation/{id}/cloturer/        → Clôturer session
    - POST   /api/sessions-deliberation/{id}/valider/         → Valider session
    """
    
    queryset = SessionDeliberation.objects.select_related(
        'annee_academique', 'filiere'
    ).all()
    serializer_class = SessionDeliberationSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['annee_academique', 'filiere', 'niveau', 'semestre', 'statut']
    search_fields = ['president_jury', 'lieu']
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
        ✨ AMÉLIORÉ: Générer automatiquement les décisions du jury pour tous les étudiants
        POST /api/sessions-deliberation/{id}/generer-decisions/
        
        Body: {} (optionnel, utilise les seuils par défaut)
        """
        session = self.get_object()
        
        # Récupérer tous les étudiants de la filière/niveau via les inscriptions
        from apps.students.models import Inscription
        inscriptions = Inscription.objects.filter(
            filiere=session.filiere,
            annee_academique=session.annee_academique,
            niveau=session.niveau,
            statut='INSCRIT'
        ).select_related('etudiant__user')
        
        etudiant_ids = inscriptions.values_list('etudiant_id', flat=True).distinct()
        etudiants = Etudiant.objects.filter(id__in=etudiant_ids).select_related('user')
        
        decisions_creees = 0
        decisions_mises_a_jour = 0
        erreurs = []
        
        for etudiant in etudiants:
            try:
                # Calculer directement la moyenne générale de l'étudiant
                # Récupérer toutes les matières de sa filière
                matieres = Matiere.objects.filter(filiere=session.filiere)
                
                total_points = Decimal(0)
                total_coefs = Decimal(0)
                total_credits = 0
                credits_obtenus = 0
                
                for matiere in matieres:
                    # Récupérer toutes les notes de l'étudiant pour cette matière
                    notes = Note.objects.filter(
                        etudiant=etudiant,
                        evaluation__matiere=matiere,
                        evaluation__annee_academique=session.annee_academique,
                        absence=False
                    ).select_related('evaluation')
                    
                    if notes.exists():
                        # Calculer la moyenne de la matière
                        total_points_matiere = Decimal(0)
                        total_coefs_matiere = Decimal(0)
                        
                        for note in notes:
                            coef = note.evaluation.coefficient
                            note_sur_20 = (note.note_obtenue / note.note_sur) * Decimal(20)
                            total_points_matiere += note_sur_20 * coef
                            total_coefs_matiere += coef
                        
                        if total_coefs_matiere > 0:
                            moyenne_matiere = total_points_matiere / total_coefs_matiere
                            total_points += moyenne_matiere * matiere.coefficient
                            total_coefs += matiere.coefficient
                            
                            if moyenne_matiere >= 10:
                                credits_obtenus += matiere.credits
                    
                    total_credits += matiere.credits
                
                # Moyenne générale
                moyenne = total_points / total_coefs if total_coefs > 0 else Decimal(0)
                credits_requis = total_credits
                
                # Déterminer la décision
                if moyenne >= 10:
                    decision = 'ADMIS'
                elif moyenne >= 8:
                    decision = 'AJOURNE'  # RATTRAPAGE
                else:
                    decision = 'REDOUBLEMENT'
                
                # Créer ou mettre à jour la décision
                decision_obj, created = DecisionJury.objects.update_or_create(
                    session=session,
                    etudiant=etudiant,
                    defaults={
                        'moyenne_generale': moyenne,
                        'total_credits_obtenus': credits_obtenus,
                        'total_credits_requis': credits_requis,
                        'decision': decision,
                        'observations': ''
                    }
                )
                
                if created:
                    decisions_creees += 1
                else:
                    decisions_mises_a_jour += 1
                    
            except Exception as e:
                erreurs.append({
                    'etudiant_id': etudiant.id,
                    'matricule': etudiant.matricule,
                    'error': str(e)
                })
        
        # Calculer les rangs
        decisions = DecisionJury.objects.filter(session=session).order_by('-moyenne_generale')
        for rang, decision in enumerate(decisions, start=1):
            decision.rang_classe = rang
            decision.save()
        
        return Response({
            'success': True,
            'message': f'{decisions_creees + decisions_mises_a_jour} décisions générées',
            'session_id': session.id,
            'decisions_creees': decisions_creees,
            'decisions_mises_a_jour': decisions_mises_a_jour,
            'total': decisions_creees + decisions_mises_a_jour,
            'erreurs': erreurs
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