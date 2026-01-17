# Routes de l'API académique

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnneeAcademiqueViewSet,
    FaculteViewSet,
    DepartementViewSet,
    FiliereViewSet,
    MatiereViewSet
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'annees-academiques', AnneeAcademiqueViewSet, basename='anneeacademique')
router.register(r'facultes', FaculteViewSet, basename='faculte')
router.register(r'departements', DepartementViewSet, basename='departement')
router.register(r'filieres', FiliereViewSet, basename='filiere')
router.register(r'matieres', MatiereViewSet, basename='matiere')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]
