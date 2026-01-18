# Routes de l'API pour évaluations et notes

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TypeEvaluationViewSet,
    EvaluationViewSet,
    NoteViewSet,
    ResultatViewSet,
    SessionDeliberationViewSet,
    MembreJuryViewSet,
    DecisionJuryViewSet
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'types-evaluations', TypeEvaluationViewSet, basename='typeevaluation')
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'resultats', ResultatViewSet, basename='resultat')
router.register(r'sessions-deliberation', SessionDeliberationViewSet, basename='sessiondeliberation')
router.register(r'membres-jury', MembreJuryViewSet, basename='membrejury')
router.register(r'decisions-jury', DecisionJuryViewSet, basename='decisionjury')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]
