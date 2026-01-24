from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnnonceViewSet,
    NotificationViewSet,
    MessageViewSet,
    PreferenceNotificationViewSet,
    StatistiquesViewSet,
)

# ROUTER
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'annonces', AnnonceViewSet, basename='annonce')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'preferences', PreferenceNotificationViewSet, basename='preference')
router.register(r'statistiques', StatistiquesViewSet, basename='statistique')

# URL PATTERNS
urlpatterns = [
    path('', include(router.urls)),
]