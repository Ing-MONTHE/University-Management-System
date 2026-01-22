from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriesLivreViewSet,
    LivreViewSet,
    EmpruntViewSet,
)

# CONFIGURATION DU ROUTER
"""
Le DefaultRouter de Django REST Framework génère automatiquement
les URLs pour toutes les actions standard d'un ViewSet :
- list (GET /)
- create (POST /)
- retrieve (GET /{pk}/)
- update (PUT /{pk}/)
- partial_update (PATCH /{pk}/)
- destroy (DELETE /{pk}/)

Il génère aussi automatiquement les URLs pour les actions custom
décorées avec @action.
"""

router = DefaultRouter()

# ENREGISTREMENT DES VIEWSETS

# Catégories de livres
# Génère : /categories/, /categories/{id}/, /categories/{id}/livres/
router.register(
    r'categories',
    CategoriesLivreViewSet,
    basename='categorie'
)

# Livres
# Génère : /livres/, /livres/{id}/, /livres/disponibles/, /livres/statistiques/, etc.
router.register(
    r'livres',
    LivreViewSet,
    basename='livre'
)

# Emprunts
# Génère : /emprunts/, /emprunts/{id}/, /emprunts/{id}/retour/, /emprunts/en_cours/, etc.
router.register(
    r'emprunts',
    EmpruntViewSet,
    basename='emprunt'
)

# PATTERNS D'URLS
urlpatterns = [
    # Inclure toutes les URLs générées par le router
    path('', include(router.urls)),
]