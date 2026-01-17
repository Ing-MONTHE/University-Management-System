# Routes de l'API pour le module CORE

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    PermissionViewSet,
    RoleViewSet,
    UserViewSet,
    AuditLogViewSet,
    CustomTokenObtainPairView
)

# ROUTER REST FRAMEWORK
"""
Le Router génère automatiquement les URLs pour les ViewSets.

EXEMPLE:
router.register('permissions', PermissionViewSet)

Génère automatiquement:
- GET    /api/permissions/          → list()
- POST   /api/permissions/          → create()
- GET    /api/permissions/{id}/     → retrieve()
- PUT    /api/permissions/{id}/     → update()
- PATCH  /api/permissions/{id}/     → partial_update()
- DELETE /api/permissions/{id}/     → destroy()
"""

router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

# URL PATTERNS
urlpatterns = [
    # AUTHENTIFICATION JWT
    
    # Login (obtenir les tokens)
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Refresh (obtenir un nouveau access token)
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ROUTES DU ROUTER
    # Inclut toutes les routes générées par le router
    path('', include(router.urls)),
]