# Routes de l'API pour étudiants et enseignants

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EtudiantViewSet,
    EnseignantViewSet,
    InscriptionViewSet,
    AttributionViewSet
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'etudiants', EtudiantViewSet, basename='etudiant')
router.register(r'enseignants', EnseignantViewSet, basename='enseignant')
router.register(r'inscriptions', InscriptionViewSet, basename='inscription')
router.register(r'attributions', AttributionViewSet, basename='attribution')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]
