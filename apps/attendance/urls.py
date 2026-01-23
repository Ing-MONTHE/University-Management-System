from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FeuillePresenceViewSet,
    PresenceViewSet,
    JustificatifAbsenceViewSet,
)

# CONFIGURATION DU ROUTER
router = DefaultRouter()

# =========================================
# ENREGISTREMENT DES VIEWSETS
# =========================================

# Feuilles de présence
# Génère : /feuilles-presence/, /feuilles-presence/{id}/, etc.
router.register(
    r'feuilles-presence',
    FeuillePresenceViewSet,
    basename='feuille-presence'
)

# Présences individuelles
# Génère : /presences/, /presences/{id}/, etc.
router.register(
    r'presences',
    PresenceViewSet,
    basename='presence'
)

# Justificatifs d'absence
# Génère : /justificatifs/, /justificatifs/{id}/, etc.
router.register(
    r'justificatifs',
    JustificatifAbsenceViewSet,
    basename='justificatif'
)

# PATTERNS D'URLS
urlpatterns = [
    # Inclure toutes les URLs générées par le router
    path('', include(router.urls)),
]