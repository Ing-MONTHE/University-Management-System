from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from .models import FeuillePresence, Presence, JustificatifAbsence
from .serializers import (
    FeuillePresenceListSerializer,
    FeuillePresenceDetailSerializer,
    FeuillePresenceCreateSerializer,
    PresenceSerializer,
    MarquerPresencesSerializer,
    JustificatifAbsenceListSerializer,
    JustificatifAbsenceDetailSerializer,
    JustificatifAbsenceCreateSerializer,
    JustificatifValidationSerializer,
)

# VIEWSET : FEUILLES DE PRÉSENCE
class FeuillePresenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les feuilles de présence.
    
    Endpoints générés automatiquement :
    - GET /feuilles-presence/ : Liste toutes les feuilles
    - POST /feuilles-presence/ : Crée une nouvelle feuille
    - GET /feuilles-presence/{id}/ : Détails d'une feuille
    - PUT /feuilles-presence/{id}/ : Mise à jour complète
    - PATCH /feuilles-presence/{id}/ : Mise à jour partielle
    - DELETE /feuilles-presence/{id}/ : Suppression
    
    Actions personnalisées :
    - POST /feuilles-presence/{id}/fermer/ : Ferme/verrouille la feuille
    - POST /feuilles-presence/{id}/marquer-presences/ : Marque plusieurs présences
    - GET /feuilles-presence/{id}/liste-presences/ : Liste des présences
    - GET /feuilles-presence/par-cours/ : Feuilles d'un cours spécifique
    - GET /feuilles-presence/statistiques/ : Stats globales
    
    Filtres :
    - ?cours={id} : Filtrer par cours
    - ?date_cours=YYYY-MM-DD : Par date
    - ?statut=OUVERTE : Par statut
    - ?date_debut=YYYY-MM-DD&date_fin=YYYY-MM-DD : Plage de dates
    
    Permissions : Authentification requise
    """
    queryset = FeuillePresence.objects.select_related(
        'cours__matiere',
        'cours__enseignant__user',
        'cours__filiere'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer approprié selon l'action.
        
        Returns:
            Serializer: Classe de serializer à utiliser
        """
        if self.action == 'create':
            return FeuillePresenceCreateSerializer
        elif self.action == 'retrieve':
            return FeuillePresenceDetailSerializer
        return FeuillePresenceListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Paramètres de requête supportés :
        - cours : ID du cours
        - date_cours : Date spécifique
        - statut : Statut de la feuille
        - date_debut + date_fin : Plage de dates
        
        Returns:
            QuerySet: Feuilles filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par cours
        cours_id = self.request.query_params.get('cours')
        if cours_id:
            queryset = queryset.filter(cours_id=cours_id)
        
        # Filtre par date
        date_cours = self.request.query_params.get('date_cours')
        if date_cours:
            queryset = queryset.filter(date_cours=date_cours)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par plage de dates
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                date_cours__gte=date_debut,
                date_cours__lte=date_fin
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def fermer(self, request, pk=None):
        """
        Action personnalisée : Ferme/verrouille une feuille de présence.
        
        URL: POST /feuilles-presence/{id}/fermer/
        
        Processus :
        1. Recalcule les statistiques (nombre présents/absents/retards)
        2. Change le statut à FERMEE
        3. Empêche toute modification ultérieure
        
        Args:
            request: Requête HTTP
            pk: ID de la feuille
        
        Returns:
            Response: Feuille fermée avec message de confirmation
        """
        feuille = self.get_object()
        
        # Vérifier que la feuille n'est pas déjà fermée
        if feuille.statut == 'FERMEE':
            return Response(
                {'message': 'Cette feuille de présence est déjà fermée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fermer la feuille (méthode du modèle)
        feuille.fermer_feuille()
        
        # Serializer la feuille fermée
        serializer = FeuillePresenceDetailSerializer(feuille)
        
        return Response({
            'message': 'Feuille de présence fermée avec succès.',
            'feuille': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def marquer_presences(self, request, pk=None):
        """
        Action personnalisée : Marque les présences de plusieurs étudiants en une fois.
        
        URL: POST /feuilles-presence/{id}/marquer-presences/
        
        Body attendu :
        {
            "presences": [
                {"etudiant_id": 1, "statut": "PRESENT"},
                {"etudiant_id": 2, "statut": "ABSENT"},
                {"etudiant_id": 3, "statut": "RETARD", "heure_arrivee": "09:15"}
            ]
        }
        
        Args:
            request: Requête HTTP avec liste des présences
            pk: ID de la feuille
        
        Returns:
            Response: Nombre de présences mises à jour + message
        """
        feuille = self.get_object()
        
        # Vérifier que la feuille n'est pas fermée
        if feuille.statut == 'FERMEE':
            return Response(
                {'error': 'Cette feuille de présence est fermée et ne peut plus être modifiée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider les données avec le serializer
        serializer = MarquerPresencesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        presences_data = serializer.validated_data['presences']
        presences_mises_a_jour = 0
        
        # Mettre à jour chaque présence
        for item in presences_data:
            try:
                presence = Presence.objects.get(
                    feuille_presence=feuille,
                    etudiant_id=item['etudiant_id']
                )
                
                # Mettre à jour le statut
                presence.statut = item['statut']
                
                # Ajouter l'heure d'arrivée si RETARD
                if item['statut'] == 'RETARD' and 'heure_arrivee' in item:
                    presence.heure_arrivee = item['heure_arrivee']
                
                # Ajouter la remarque si fournie
                if 'remarque' in item:
                    presence.remarque = item['remarque']
                
                presence.save()
                presences_mises_a_jour += 1
                
            except Presence.DoesNotExist:
                # Ignorer si la présence n'existe pas
                continue
        
        # Recalculer les statistiques de la feuille
        feuille.nombre_presents = feuille.presences.filter(statut='PRESENT').count()
        feuille.nombre_absents = feuille.presences.filter(statut='ABSENT').count()
        feuille.nombre_retards = feuille.presences.filter(statut='RETARD').count()
        feuille.save()
        
        return Response({
            'message': f'{presences_mises_a_jour} présences mises à jour avec succès.',
            'statistiques': {
                'presents': feuille.nombre_presents,
                'absents': feuille.nombre_absents,
                'retards': feuille.nombre_retards,
                'taux_presence': feuille.calculer_taux_presence()
            }
        })
    
    @action(detail=True, methods=['get'])
    def liste_presences(self, request, pk=None):
        """
        Action personnalisée : Liste détaillée des présences de la feuille.
        
        URL: GET /feuilles-presence/{id}/liste-presences/
        
        Retourne la liste de tous les étudiants avec leur statut de présence.
        Utile pour afficher la feuille de présence complète.
        
        Returns:
            Response: Liste des présences avec infos étudiants
        """
        feuille = self.get_object()
        presences = feuille.presences.select_related('etudiant__user').all()
        serializer = PresenceSerializer(presences, many=True)
        
        return Response({
            'feuille': FeuillePresenceDetailSerializer(feuille).data,
            'presences': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_cours(self, request):
        """
        Action personnalisée : Liste les feuilles de présence d'un cours spécifique.
        
        URL: GET /feuilles-presence/par-cours/?cours_id={id}
        
        Paramètres :
        - cours_id : ID du cours (requis)
        
        Returns:
            Response: Liste des feuilles du cours avec statistiques
        """
        cours_id = request.query_params.get('cours_id')
        
        if not cours_id:
            return Response(
                {'error': 'Le paramètre cours_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feuilles = self.get_queryset().filter(cours_id=cours_id)
        serializer = self.get_serializer(feuilles, many=True)
        
        # Calculer les statistiques du cours
        stats = feuilles.aggregate(
            total_feuilles=Count('id'),
            taux_presence_moyen=Avg('nombre_presents') * 100 / (
                Avg('nombre_presents') + Avg('nombre_absents') + Avg('nombre_retards')
            ) if feuilles.exists() else 0
        )
        
        return Response({
            'feuilles': serializer.data,
            'statistiques': stats
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des feuilles de présence.
        
        URL: GET /feuilles-presence/statistiques/
        
        Returns:
            Response: {
                total_feuilles: int,
                feuilles_ouvertes: int,
                feuilles_fermees: int,
                taux_presence_global: float,
                total_presents: int,
                total_absents: int,
                total_retards: int
            }
        """
        total_feuilles = FeuillePresence.objects.count()
        feuilles_ouvertes = FeuillePresence.objects.filter(statut='OUVERTE').count()
        feuilles_fermees = FeuillePresence.objects.filter(statut='FERMEE').count()
        
        # Calculer les totaux
        totaux = FeuillePresence.objects.aggregate(
            total_presents=Sum('nombre_presents'),
            total_absents=Sum('nombre_absents'),
            total_retards=Sum('nombre_retards')
        )
        
        # Calculer le taux de présence global
        total_etudiants = (
            (totaux['total_presents'] or 0) +
            (totaux['total_absents'] or 0) +
            (totaux['total_retards'] or 0)
        )
        
        taux_presence_global = 0
        if total_etudiants > 0:
            taux_presence_global = round(
                ((totaux['total_presents'] or 0) / total_etudiants) * 100,
                2
            )
        
        return Response({
            'total_feuilles': total_feuilles,
            'feuilles_ouvertes': feuilles_ouvertes,
            'feuilles_fermees': feuilles_fermees,
            'taux_presence_global': taux_presence_global,
            'total_presents': totaux['total_presents'] or 0,
            'total_absents': totaux['total_absents'] or 0,
            'total_retards': totaux['total_retards'] or 0,
        })

# VIEWSET : PRÉSENCES
class PresenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les présences individuelles des étudiants.
    
    Endpoints :
    - GET /presences/ : Liste toutes les présences
    - POST /presences/ : Créer une présence (rarement utilisé)
    - GET /presences/{id}/ : Détails d'une présence
    - PUT/PATCH /presences/{id}/ : Modifier une présence
    - DELETE /presences/{id}/ : Supprimer une présence
    
    Actions personnalisées :
    - GET /presences/par-etudiant/ : Présences d'un étudiant
    - GET /presences/absents/ : Liste des absences
    - GET /presences/retards/ : Liste des retards
    - GET /presences/taux-assiduite/ : Taux d'assiduité d'un étudiant
    
    Filtres :
    - ?feuille_presence={id} : Par feuille
    - ?etudiant={id} : Par étudiant
    - ?statut=ABSENT : Par statut
    - ?absence_justifiee=true : Seulement absences justifiées/non justifiées
    """
    queryset = Presence.objects.select_related(
        'feuille_presence__cours__matiere',
        'etudiant__user'
    ).all()
    serializer_class = PresenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Présences filtrées
        """
        queryset = super().get_queryset()
        
        # Filtre par feuille de présence
        feuille_id = self.request.query_params.get('feuille_presence')
        if feuille_id:
            queryset = queryset.filter(feuille_presence_id=feuille_id)
        
        # Filtre par étudiant
        etudiant_id = self.request.query_params.get('etudiant')
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par absence justifiée
        absence_justifiee = self.request.query_params.get('absence_justifiee')
        if absence_justifiee is not None:
            queryset = queryset.filter(
                absence_justifiee=(absence_justifiee.lower() == 'true')
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def par_etudiant(self, request):
        """
        Action personnalisée : Présences d'un étudiant spécifique.
        
        URL: GET /presences/par-etudiant/?etudiant_id={id}
        
        Paramètres :
        - etudiant_id : ID de l'étudiant (requis)
        - date_debut : Date de début (optionnel)
        - date_fin : Date de fin (optionnel)
        
        Returns:
            Response: Liste des présences avec statistiques
        """
        etudiant_id = request.query_params.get('etudiant_id')
        
        if not etudiant_id:
            return Response(
                {'error': 'Le paramètre etudiant_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(etudiant_id=etudiant_id)
        
        # Filtrer par plage de dates si fournie
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                feuille_presence__date_cours__gte=date_debut,
                feuille_presence__date_cours__lte=date_fin
            )
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculer les statistiques
        total = queryset.count()
        presents = queryset.filter(statut='PRESENT').count()
        absents = queryset.filter(statut='ABSENT').count()
        retards = queryset.filter(statut='RETARD').count()
        absences_justifiees = queryset.filter(
            statut='ABSENT',
            absence_justifiee=True
        ).count()
        
        taux_presence = 0
        if total > 0:
            taux_presence = round((presents / total) * 100, 2)
        
        return Response({
            'presences': serializer.data,
            'statistiques': {
                'total_cours': total,
                'presents': presents,
                'absents': absents,
                'retards': retards,
                'absences_justifiees': absences_justifiees,
                'absences_non_justifiees': absents - absences_justifiees,
                'taux_presence': taux_presence
            }
        })
    
    @action(detail=False, methods=['get'])
    def absents(self, request):
        """
        Action personnalisée : Liste des absences.
        
        URL: GET /presences/absents/
        
        Paramètres optionnels :
        - date_debut, date_fin : Plage de dates
        - justifiee : true/false
        
        Returns:
            Response: Liste des absences
        """
        queryset = self.get_queryset().filter(statut='ABSENT')
        
        # Filtre justifié/non justifié
        justifiee = request.query_params.get('justifiee')
        if justifiee is not None:
            queryset = queryset.filter(
                absence_justifiee=(justifiee.lower() == 'true')
            )
        
        # Filtre par dates
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                feuille_presence__date_cours__gte=date_debut,
                feuille_presence__date_cours__lte=date_fin
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def retards(self, request):
        """
        Action personnalisée : Liste des retards.
        
        URL: GET /presences/retards/
        
        Returns:
            Response: Liste des retards avec minutes de retard
        """
        queryset = self.get_queryset().filter(statut='RETARD')
        
        # Filtre par dates
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                feuille_presence__date_cours__gte=date_debut,
                feuille_presence__date_cours__lte=date_fin
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def taux_assiduite(self, request):
        """
        Action personnalisée : Calcule le taux d'assiduité d'un étudiant.
        
        URL: GET /presences/taux-assiduite/?etudiant_id={id}&date_debut=YYYY-MM-DD&date_fin=YYYY-MM-DD
        
        Paramètres :
        - etudiant_id : ID de l'étudiant (requis)
        - date_debut : Date de début (requis)
        - date_fin : Date de fin (requis)
        
        Returns:
            Response: Taux d'assiduité détaillé
        """
        etudiant_id = request.query_params.get('etudiant_id')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        if not all([etudiant_id, date_debut, date_fin]):
            return Response(
                {'error': 'Les paramètres etudiant_id, date_debut et date_fin sont requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        presences = Presence.objects.filter(
            etudiant_id=etudiant_id,
            feuille_presence__date_cours__gte=date_debut,
            feuille_presence__date_cours__lte=date_fin
        )
        
        total = presences.count()
        presents = presences.filter(statut='PRESENT').count()
        absents = presences.filter(statut='ABSENT').count()
        retards = presences.filter(statut='RETARD').count()
        absences_justifiees = presences.filter(
            statut='ABSENT',
            absence_justifiee=True
        ).count()
        
        # Calculer les taux
        taux_presence = 0
        taux_absence = 0
        taux_retard = 0
        
        if total > 0:
            taux_presence = round((presents / total) * 100, 2)
            taux_absence = round((absents / total) * 100, 2)
            taux_retard = round((retards / total) * 100, 2)
        
        # Déterminer le niveau d'assiduité
        if taux_presence >= 90:
            niveau = 'EXCELLENT'
        elif taux_presence >= 75:
            niveau = 'BON'
        elif taux_presence >= 60:
            niveau = 'MOYEN'
        else:
            niveau = 'FAIBLE'
        
        return Response({
            'periode': {
                'date_debut': date_debut,
                'date_fin': date_fin
            },
            'total_cours': total,
            'presents': presents,
            'absents': absents,
            'retards': retards,
            'absences_justifiees': absences_justifiees,
            'absences_non_justifiees': absents - absences_justifiees,
            'taux_presence': taux_presence,
            'taux_absence': taux_absence,
            'taux_retard': taux_retard,
            'niveau_assiduite': niveau
        })

# VIEWSET : JUSTIFICATIFS D'ABSENCE
class JustificatifAbsenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les justificatifs d'absence.
    
    Endpoints :
    - GET /justificatifs/ : Liste tous les justificatifs
    - POST /justificatifs/ : Upload un nouveau justificatif
    - GET /justificatifs/{id}/ : Détails d'un justificatif
    - PUT/PATCH /justificatifs/{id}/ : Modifier un justificatif
    - DELETE /justificatifs/{id}/ : Supprimer un justificatif
    
    Actions personnalisées :
    - POST /justificatifs/{id}/valider/ : Valider un justificatif
    - POST /justificatifs/{id}/rejeter/ : Rejeter un justificatif
    - GET /justificatifs/en-attente/ : Justificatifs en attente
    - GET /justificatifs/par-etudiant/ : Justificatifs d'un étudiant
    - GET /justificatifs/statistiques/ : Stats globales
    
    Filtres :
    - ?etudiant={id} : Par étudiant
    - ?statut=EN_ATTENTE : Par statut
    - ?type=MEDICAL : Par type
    """
    queryset = JustificatifAbsence.objects.select_related('etudiant__user').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action == 'create':
            return JustificatifAbsenceCreateSerializer
        elif self.action == 'retrieve':
            return JustificatifAbsenceDetailSerializer
        return JustificatifAbsenceListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Justificatifs filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par étudiant
        etudiant_id = self.request.query_params.get('etudiant')
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par type
        type_justificatif = self.request.query_params.get('type')
        if type_justificatif:
            queryset = queryset.filter(type_justificatif=type_justificatif)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """
        Action personnalisée : Valide un justificatif.
        
        URL: POST /justificatifs/{id}/valider/
        Body (optionnel): { "commentaire": "Justificatif conforme" }
        
        Processus :
        1. Change le statut à VALIDE
        2. Marque les absences de la période comme justifiées
        3. Enregistre la date de traitement
        
        Returns:
            Response: Justificatif validé avec message
        """
        justificatif = self.get_object()
        
        # Vérifier que le justificatif n'est pas déjà traité
        if justificatif.statut != 'EN_ATTENTE':
            return Response(
                {'error': 'Ce justificatif a déjà été traité.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le commentaire optionnel
        commentaire = request.data.get('commentaire', '')
        
        # Valider le justificatif (méthode du modèle)
        justificatif.valider(commentaire)
        
        serializer = JustificatifAbsenceDetailSerializer(justificatif)
        
        return Response({
            'message': 'Justificatif validé avec succès. Les absences ont été marquées comme justifiées.',
            'justificatif': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        """
        Action personnalisée : Rejette un justificatif.
        
        URL: POST /justificatifs/{id}/rejeter/
        Body (requis): { "commentaire": "Raison du rejet" }
        
        Returns:
            Response: Justificatif rejeté avec message
        """
        justificatif = self.get_object()
        
        # Vérifier que le justificatif n'est pas déjà traité
        if justificatif.statut != 'EN_ATTENTE':
            return Response(
                {'error': 'Ce justificatif a déjà été traité.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Le commentaire est obligatoire pour un rejet
        commentaire = request.data.get('commentaire', '')
        if not commentaire:
            return Response(
                {'error': 'Un commentaire est obligatoire pour rejeter un justificatif.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rejeter le justificatif (méthode du modèle)
        justificatif.rejeter(commentaire)
        
        serializer = JustificatifAbsenceDetailSerializer(justificatif)
        
        return Response({
            'message': 'Justificatif rejeté.',
            'justificatif': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """
        Action personnalisée : Liste les justificatifs en attente de validation.
        
        URL: GET /justificatifs/en-attente/
        
        Returns:
            Response: Liste des justificatifs EN_ATTENTE
        """
        justificatifs = self.get_queryset().filter(statut='EN_ATTENTE').order_by('date_soumission')
        serializer = self.get_serializer(justificatifs, many=True)
        
        return Response({
            'count': justificatifs.count(),
            'justificatifs': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_etudiant(self, request):
        """
        Action personnalisée : Liste les justificatifs d'un étudiant.
        
        URL: GET /justificatifs/par-etudiant/?etudiant_id={id}
        
        Returns:
            Response: Liste avec statistiques
        """
        etudiant_id = request.query_params.get('etudiant_id')
        
        if not etudiant_id:
            return Response(
                {'error': 'Le paramètre etudiant_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        justificatifs = self.get_queryset().filter(etudiant_id=etudiant_id)
        serializer = self.get_serializer(justificatifs, many=True)
        
        # Stats
        total = justificatifs.count()
        valides = justificatifs.filter(statut='VALIDE').count()
        rejetes = justificatifs.filter(statut='REJETE').count()
        en_attente = justificatifs.filter(statut='EN_ATTENTE').count()
        
        return Response({
            'justificatifs': serializer.data,
            'statistiques': {
                'total': total,
                'valides': valides,
                'rejetes': rejetes,
                'en_attente': en_attente
            }
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des justificatifs.
        
        URL: GET /justificatifs/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = JustificatifAbsence.objects.count()
        en_attente = JustificatifAbsence.objects.filter(statut='EN_ATTENTE').count()
        valides = JustificatifAbsence.objects.filter(statut='VALIDE').count()
        rejetes = JustificatifAbsence.objects.filter(statut='REJETE').count()
        
        # Répartition par type
        par_type = JustificatifAbsence.objects.values('type_justificatif').annotate(
            count=Count('id')
        )
        
        # Temps moyen de traitement (en jours)
        justificatifs_traites = JustificatifAbsence.objects.filter(
            date_traitement__isnull=False
        )
        
        delai_moyen = 0
        if justificatifs_traites.exists():
            delais = [
                (j.date_traitement.date() - j.date_soumission.date()).days
                for j in justificatifs_traites
            ]
            delai_moyen = round(sum(delais) / len(delais), 1)
        
        return Response({
            'total_justificatifs': total,
            'en_attente': en_attente,
            'valides': valides,
            'rejetes': rejetes,
            'taux_validation': round((valides / total * 100), 2) if total > 0 else 0,
            'taux_rejet': round((rejetes / total * 100), 2) if total > 0 else 0,
            'repartition_par_type': list(par_type),
            'delai_moyen_traitement_jours': delai_moyen
        })
