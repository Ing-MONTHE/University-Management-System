from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriesLivreViewSet,
    LivreViewSet,
    EmpruntViewSet,
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'categories', CategoriesLivreViewSet, basename='categorie')
router.register(r'livres', LivreViewSet, basename='livre')
router.register(r'emprunts', EmpruntViewSet, basename='emprunt')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]
