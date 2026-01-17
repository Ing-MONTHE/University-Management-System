# Endpoints de l'API
# Gère les requêtes HTTP et retourne les réponses JSON

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from .models import User, Role, Permission, AuditLog
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, RoleSerializer, PermissionSerializer,
    AuditLogSerializer, CustomTokenObtainPairSerializer
)

User = get_user_model()

# PERMISSION VIEWSET
class PermissionViewSet(viewsets.ModelViewSet):
    # API endpoint pour les permissions.
    
    # Endpoints disponibles:
    # - GET    /api/permissions/          → Liste de toutes les permissions
    # - POST   /api/permissions/          → Créer une permission
    # - GET    /api/permissions/{id}/     → Détails d'une permission
    # - PUT    /api/permissions/{id}/     → Modifier une permission
    # - PATCH  /api/permissions/{id}/     → Modifier partiellement
    # - DELETE /api/permissions/{id}/     → Supprimer une permission
    
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    
    # Filtres et recherche
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']  # Filtrer par catégorie
    search_fields = ['name', 'code', 'description']  # Rechercher dans ces champs
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['category', 'name']

# ROLE VIEWSET
class RoleViewSet(viewsets.ModelViewSet):
    # API endpoint pour les rôles.
    
    # Endpoints:
    # - GET    /api/roles/          → Liste des rôles
    # - POST   /api/roles/          → Créer un rôle
    # - GET    /api/roles/{id}/     → Détails d'un rôle
    # - PUT    /api/roles/{id}/     → Modifier un rôle
    # - PATCH  /api/roles/{id}/     → Modifier partiellement
    # - DELETE /api/roles/{id}/     → Supprimer un rôle
    
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

# USER VIEWSET
class UserViewSet(viewsets.ModelViewSet):
    # API endpoint pour les utilisateurs.
    
    # Endpoints:
    # - GET    /api/users/                    → Liste des utilisateurs
    # - POST   /api/users/                    → Créer un utilisateur
    # - GET    /api/users/{id}/               → Détails d'un utilisateur
    # - PUT    /api/users/{id}/               → Modifier un utilisateur
    # - PATCH  /api/users/{id}/               → Modifier partiellement
    # - DELETE /api/users/{id}/               → Supprimer un utilisateur
    # - POST   /api/users/{id}/change-password/ → Changer le mot de passe
    # - GET    /api/users/me/                 → Infos de l'utilisateur connecté
    
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        # Retourner le bon serializer selon l'action.
        
        # POURQUOI ?
        # - Pour LIRE : UserSerializer (sans password)
        # - Pour CRÉER : UserCreateSerializer (avec validation password)
        # - Pour MODIFIER : UserUpdateSerializer (sans password)

        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        # Endpoint personnalisé : GET /api/users/me/
        # Retourne les infos de l'utilisateur connecté.
        
        # EXEMPLE D'UTILISATION:
        # Frontend → GET /api/users/me/
        # Backend → Retourne les infos du user connecté

        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        # Endpoint personnalisé : POST /api/users/{id}/change-password/
        # Permet de changer le mot de passe.
        
        # BODY (JSON):
        # {
        #     "old_password": "ancien_mot_de_passe",
        #     "new_password": "nouveau_mot_de_passe",
        #     "new_password_confirm": "nouveau_mot_de_passe"
        # }

        user = self.get_object()
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Mot de passe changé avec succès'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# AUDIT LOG VIEWSET
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    # API endpoint pour les logs d'audit (LECTURE SEULE).
    
    # Endpoints:
    # - GET /api/audit-logs/      → Liste des logs
    # - GET /api/audit-logs/{id}/ → Détails d'un log
    
    # NOTE: ReadOnlyModelViewSet = Seulement GET (pas de POST/PUT/DELETE)
    # On ne modifie JAMAIS les logs d'audit !
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'table_name', 'user']
    search_fields = ['table_name', 'object_id', 'ip_address']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

# LOGIN VIEW (JWT)
class CustomTokenObtainPairView(TokenObtainPairView):
    # Endpoint de connexion JWT personnalisé.
    
    # POST /api/auth/login/
    
    # BODY:
    # {
    #     "username": "admin",
    #     "password": "Admin123!"
    # }
    
    # RESPONSE:
    # {
    #     "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    #     "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    #     "user": {
    #         "id": 1,
    #         "username": "admin",
    #         "email": "admin@university.com",
    #         "full_name": "Admin",
    #         "is_staff": true,
    #         "is_superuser": true,
    #         "roles": ["Super Administrateur"],
    #         "permissions": ["all"]
    #     }
    # }
    
    serializer_class = CustomTokenObtainPairSerializer
