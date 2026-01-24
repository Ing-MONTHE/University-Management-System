from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EquipementViewSet,
    ReservationViewSet,
    MaintenanceViewSet,
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'equipements', EquipementViewSet, basename='equipement')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'maintenances', MaintenanceViewSet, basename='maintenance')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]