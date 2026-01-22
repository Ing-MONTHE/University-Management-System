from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import CategoriesLivre, Livre, Emprunt
from .serializers import (
    CategoriesLivreSerializer,
    LivreListSerializer,
    LivreDetailSerializer,
    EmpruntListSerializer,
    EmpruntDetailSerializer,
    EmpruntCreateSerializer,
    EmpruntRetourSerializer,
)

# VIEWSET : CATÉGORIES DE LIVRES
class CategoriesLivreViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les catégories de livres.
    
    Endpoints générés automatiquement :
    - GET /categories/ : Liste toutes les catégories
    - POST /categories/ : Crée une nouvelle catégorie
    - GET /categories/{id}/ : Détails d'une catégorie
    - PUT /categories/{id}/ : Mise à jour complète
    - PATCH /categories/{id}/ : Mise à jour partielle
    - DELETE /categories/{id}/ : Suppression
    
    Permissions : Authentification requise
    """
    queryset = CategoriesLivre.objects.all()
    serializer_class = CategoriesLivreSerializer
    permission_classes = [IsAuthenticated]
    
    # Optimisation : compter les livres en une seule requête
    def get_queryset(self):
        """
        Retourne le queryset optimisé avec annotation du nombre de livres.
        
        Returns:
            QuerySet: Catégories avec nombre de livres annoté
        """
        return CategoriesLivre.objects.annotate(
            nb_livres=Count('livres')
        ).order_by('nom')
    
    @action(detail=True, methods=['get'])
    def livres(self, request, pk=None):
        """
        Action personnalisée : Liste les livres d'une catégorie.
        
        URL: GET /categories/{id}/livres/
        
        Args:
            request: Requête HTTP
            pk: ID de la catégorie
        
        Returns:
            Response: Liste des livres de la catégorie
        """
        categorie = self.get_object()
        livres = categorie.livres.all()
        serializer = LivreListSerializer(livres, many=True)
        return Response(serializer.data)

# VIEWSET : LIVRES
class LivreViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les livres de la bibliothèque.
    
    Endpoints :
    - GET /livres/ : Liste tous les livres (avec filtres)
    - POST /livres/ : Ajoute un nouveau livre
    - GET /livres/{id}/ : Détails d'un livre
    - PUT/PATCH /livres/{id}/ : Mise à jour
    - DELETE /livres/{id}/ : Suppression
    
    Actions personnalisées :
    - GET /livres/disponibles/ : Liste les livres disponibles
    - GET /livres/recherche/?q=terme : Recherche dans titre, auteur, ISBN
    - GET /livres/{id}/historique/ : Historique des emprunts
    
    Filtres :
    - ?categorie={id} : Filtrer par catégorie
    - ?auteur=nom : Filtrer par auteur
    - ?disponible=true : Seulement les disponibles
    """
    queryset = Livre.objects.select_related('categorie').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer approprié selon l'action.
        
        - Liste : Serializer simple
        - Détail : Serializer complet
        
        Returns:
            Serializer: Classe de serializer à utiliser
        """
        if self.action == 'retrieve':
            return LivreDetailSerializer
        return LivreListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Paramètres de requête supportés :
        - categorie : ID de la catégorie
        - auteur : Nom de l'auteur (recherche partielle)
        - disponible : true/false
        - q : Recherche globale (titre, auteur, ISBN)
        
        Returns:
            QuerySet: Livres filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par catégorie
        categorie_id = self.request.query_params.get('categorie')
        if categorie_id:
            queryset = queryset.filter(categorie_id=categorie_id)
        
        # Filtre par auteur
        auteur = self.request.query_params.get('auteur')
        if auteur:
            queryset = queryset.filter(auteur__icontains=auteur)
        
        # Filtre par disponibilité
        disponible = self.request.query_params.get('disponible')
        if disponible and disponible.lower() == 'true':
            queryset = queryset.filter(nombre_exemplaires_disponibles__gt=0)
        
        # Recherche globale
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(titre__icontains=q) |
                Q(auteur__icontains=q) |
                Q(isbn__icontains=q)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        Action personnalisée : Liste seulement les livres disponibles.
        
        URL: GET /livres/disponibles/
        
        Returns:
            Response: Liste des livres avec stock > 0
        """
        livres = self.get_queryset().filter(nombre_exemplaires_disponibles__gt=0)
        serializer = self.get_serializer(livres, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        """
        Action personnalisée : Historique des emprunts d'un livre.
        
        URL: GET /livres/{id}/historique/
        
        Returns:
            Response: Liste des emprunts passés et en cours
        """
        livre = self.get_object()
        emprunts = livre.emprunts.select_related('etudiant__user').all()
        serializer = EmpruntListSerializer(emprunts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales de la bibliothèque.
        
        URL: GET /livres/statistiques/
        
        Returns:
            Response: {
                total_livres: int,
                total_exemplaires: int,
                exemplaires_disponibles: int,
                exemplaires_empruntes: int,
                livres_par_categorie: [{categorie, count}]
            }
        """
        total_livres = Livre.objects.count()
        total_exemplaires = Livre.objects.aggregate(
            total=Sum('nombre_exemplaires_total')
        )['total'] or 0
        exemplaires_disponibles = Livre.objects.aggregate(
            total=Sum('nombre_exemplaires_disponibles')
        )['total'] or 0
        
        livres_par_categorie = CategoriesLivre.objects.annotate(
            count=Count('livres')
        ).values('nom', 'count')
        
        return Response({
            'total_livres': total_livres,
            'total_exemplaires': total_exemplaires,
            'exemplaires_disponibles': exemplaires_disponibles,
            'exemplaires_empruntes': total_exemplaires - exemplaires_disponibles,
            'livres_par_categorie': list(livres_par_categorie),
        })

# VIEWSET : EMPRUNTS
class EmpruntViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les emprunts de livres.
    
    Endpoints :
    - GET /emprunts/ : Liste tous les emprunts
    - POST /emprunts/ : Créer un nouvel emprunt
    - GET /emprunts/{id}/ : Détails d'un emprunt
    - PUT/PATCH /emprunts/{id}/ : Mise à jour
    - DELETE /emprunts/{id}/ : Suppression (annulation)
    
    Actions personnalisées :
    - POST /emprunts/{id}/retour/ : Enregistrer le retour d'un livre
    - GET /emprunts/en_cours/ : Emprunts en cours
    - GET /emprunts/en_retard/ : Emprunts en retard
    - GET /emprunts/historique/ : Historique complet
    - GET /emprunts/statistiques/ : Stats globales
    
    Filtres :
    - ?etudiant={id} : Emprunts d'un étudiant
    - ?livre={id} : Emprunts d'un livre
    - ?statut=EN_COURS : Par statut
    """
    queryset = Emprunt.objects.select_related('livre', 'etudiant__user').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action == 'create':
            return EmpruntCreateSerializer
        elif self.action == 'retour':
            return EmpruntRetourSerializer
        elif self.action == 'retrieve':
            return EmpruntDetailSerializer
        return EmpruntListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Paramètres supportés :
        - etudiant : ID de l'étudiant
        - livre : ID du livre
        - statut : Statut de l'emprunt
        
        Returns:
            QuerySet: Emprunts filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par étudiant
        etudiant_id = self.request.query_params.get('etudiant')
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        
        # Filtre par livre
        livre_id = self.request.query_params.get('livre')
        if livre_id:
            queryset = queryset.filter(livre_id=livre_id)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Logique supplémentaire lors de la création d'un emprunt.
        
        Le serializer gère déjà la décrémentation du stock.
        """
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def retour(self, request, pk=None):
        """
        Action personnalisée : Enregistrer le retour d'un livre.
        
        URL: POST /emprunts/{id}/retour/
        Body (optionnel): { "notes": "Livre en bon état" }
        
        Processus :
        1. Calcule la pénalité si retard
        2. Met à jour le statut à RETOURNE
        3. Incrémente le stock disponible
        
        Returns:
            Response: Détails de l'emprunt mis à jour
        """
        emprunt = self.get_object()
        serializer = EmpruntRetourSerializer(
            emprunt,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            emprunt_retourne = serializer.save()
            detail_serializer = EmpruntDetailSerializer(emprunt_retourne)
            return Response(
                {
                    'message': 'Retour enregistré avec succès',
                    'emprunt': detail_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        """
        Action personnalisée : Liste les emprunts en cours.
        
        URL: GET /emprunts/en_cours/
        
        Returns:
            Response: Liste des emprunts avec statut EN_COURS
        """
        emprunts = self.get_queryset().filter(statut='EN_COURS')
        serializer = self.get_serializer(emprunts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_retard(self, request):
        """
        Action personnalisée : Liste les emprunts en retard.
        
        URL: GET /emprunts/en_retard/
        
        Met à jour automatiquement le statut des emprunts en retard.
        
        Returns:
            Response: Liste des emprunts en retard
        """
        date_actuelle = timezone.now().date()
        
        # Mettre à jour les statuts des emprunts en retard
        emprunts_retard = Emprunt.objects.filter(
            statut='EN_COURS',
            date_retour_prevue__lt=date_actuelle
        )
        emprunts_retard.update(statut='EN_RETARD')
        
        # Récupérer tous les emprunts en retard
        emprunts = self.get_queryset().filter(statut='EN_RETARD')
        serializer = self.get_serializer(emprunts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def historique(self, request):
        """
        Action personnalisée : Historique complet des emprunts.
        
        URL: GET /emprunts/historique/
        
        Returns:
            Response: Tous les emprunts (triés par date décroissante)
        """
        emprunts = self.get_queryset().order_by('-date_emprunt')
        serializer = self.get_serializer(emprunts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques des emprunts.
        
        URL: GET /emprunts/statistiques/
        
        Returns:
            Response: {
                total_emprunts: int,
                emprunts_en_cours: int,
                emprunts_en_retard: int,
                emprunts_retournes: int,
                penalites_totales: float,
                livre_plus_emprunte: {livre, count}
            }
        """
        total_emprunts = Emprunt.objects.count()
        emprunts_en_cours = Emprunt.objects.filter(statut='EN_COURS').count()
        emprunts_en_retard = Emprunt.objects.filter(statut='EN_RETARD').count()
        emprunts_retournes = Emprunt.objects.filter(statut='RETOURNE').count()
        
        penalites_totales = Emprunt.objects.aggregate(
            total=Sum('penalite')
        )['total'] or 0
        
        # Livre le plus emprunté
        livre_plus_emprunte = Livre.objects.annotate(
            nb_emprunts=Count('emprunts')
        ).order_by('-nb_emprunts').first()
        
        livre_data = None
        if livre_plus_emprunte:
            livre_data = {
                'id': livre_plus_emprunte.id,
                'titre': livre_plus_emprunte.titre,
                'auteur': livre_plus_emprunte.auteur,
                'nombre_emprunts': livre_plus_emprunte.nb_emprunts
            }
        
        return Response({
            'total_emprunts': total_emprunts,
            'emprunts_en_cours': emprunts_en_cours,
            'emprunts_en_retard': emprunts_en_retard,
            'emprunts_retournes': emprunts_retournes,
            'penalites_totales': float(penalites_totales),
            'livre_plus_emprunte': livre_data,
        })
