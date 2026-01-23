from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FraisScolariteViewSet,
    PaiementViewSet,
    BourseViewSet,
    FactureViewSet,
)

# CONFIGURATION DU ROUTER

router = DefaultRouter()
# ENREGISTREMENT DES VIEWSETS

# Frais de scolarité
# Génère : /frais-scolarite/, /frais-scolarite/{id}/, etc.
router.register(
    r'frais-scolarite',
    FraisScolariteViewSet,
    basename='frais-scolarite'
)

# Paiements
# Génère : /paiements/, /paiements/{id}/, etc.
router.register(
    r'paiements',
    PaiementViewSet,
    basename='paiement'
)

# Bourses
# Génère : /bourses/, /bourses/{id}/, etc.
router.register(
    r'bourses',
    BourseViewSet,
    basename='bourse'
)

# Factures
# Génère : /factures/, /factures/{id}/, etc.
router.register(
    r'factures',
    FactureViewSet,
    basename='facture'
)

# PATTERNS D'URLS
urlpatterns = [
    # Inclure toutes les URLs générées par le router
    path('', include(router.urls)),
]
