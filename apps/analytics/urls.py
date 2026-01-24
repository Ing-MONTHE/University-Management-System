from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RapportViewSet,
    DashboardViewSet,
    KPIViewSet,
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'rapports', RapportViewSet, basename='rapport')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'kpis', KPIViewSet, basename='kpi')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]