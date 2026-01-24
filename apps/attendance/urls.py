from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FeuillePresenceViewSet,
    PresenceViewSet,
    JustificatifAbsenceViewSet,
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'feuilles-presence', FeuillePresenceViewSet, basename='feuille-presence')
router.register(r'presences', PresenceViewSet, basename='presence')
router.register(r'justificatifs', JustificatifAbsenceViewSet, basename='justificatif')

# URL PATTERNS
urlpatterns = [
    # Inclure toutes les URLs générées par le router
    path('', include(router.urls)),
]