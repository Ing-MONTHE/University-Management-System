# Routes de l'API pour emploi du temps

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BatimentViewSet,
    SalleViewSet,
    CreneauViewSet,
    CoursViewSet,
    ConflitSalleViewSet
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'batiments', BatimentViewSet, basename='batiment')
router.register(r'salles', SalleViewSet, basename='salle')
router.register(r'creneaux', CreneauViewSet, basename='creneau')
router.register(r'cours', CoursViewSet, basename='cours')
router.register(r'conflits', ConflitSalleViewSet, basename='conflit')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]
