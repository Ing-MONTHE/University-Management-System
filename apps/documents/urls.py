from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet,
    TemplateDocumentViewSet,
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'templates', TemplateDocumentViewSet, basename='template')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]