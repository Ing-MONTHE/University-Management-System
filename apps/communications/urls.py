from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnnonceViewSet,
    NotificationViewSet,
    MessageViewSet,
    PreferenceNotificationViewSet,
    StatistiquesViewSet,
)

# CONFIGURATION DU ROUTER

router = DefaultRouter()

# ENREGISTREMENT DES VIEWSETS

# Annonces
# Génère : /annonces/, /annonces/{id}/, etc.
router.register(
    r'annonces',
    AnnonceViewSet,
    basename='annonce'
)

# Notifications
# Génère : /notifications/, /notifications/{id}/, etc.
router.register(
    r'notifications',
    NotificationViewSet,
    basename='notification'
)

# Messages
# Génère : /messages/, /messages/{id}/, etc.
router.register(
    r'messages',
    MessageViewSet,
    basename='message'
)

# Préférences de notification
# Génère : /preferences/, /preferences/{id}/, etc.
router.register(
    r'preferences',
    PreferenceNotificationViewSet,
    basename='preference'
)

# Statistiques
# Génère : /statistiques/
router.register(
    r'statistiques',
    StatistiquesViewSet,
    basename='statistique'
)

# PATTERNS D'URLS

urlpatterns = [
    # Inclure toutes les URLs générées par le router
    path('', include(router.urls)),
]