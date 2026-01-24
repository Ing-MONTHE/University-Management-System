from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FraisScolariteViewSet,
    PaiementViewSet,
    BourseViewSet,
    FactureViewSet,
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'frais-scolarite', FraisScolariteViewSet, basename='frais-scolarite')
router.register(r'paiements', PaiementViewSet, basename='paiement')
router.register(r'bourses', BourseViewSet, basename='bourse')
router.register(r'factures', FactureViewSet, basename='facture')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]
