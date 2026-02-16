from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    #Grappelli URLS
    path("grappelli/", include("grappelli.urls")),
    
    #Admin django
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),

    #Documentation API (Swagger)
    #Schema OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    #Interface Swagger
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    #API - Module CORE
    path('api/core/', include('apps.core.urls')),

    #API - Module Academic
    path('api/', include('apps.academic.urls')),

    #API - Module Students
    path('api/', include('apps.students.urls')),

    #API - Module evaluations
    path('api/', include('apps.evaluations.urls')),

    #API - Module Emploi du Temps
    path('api/schedule/', include('apps.schedule.urls')),

    #API - Module bibliotheque
    path('api/', include('apps.library.urls')),

    #API - Module Presence
    path('api/', include('apps.attendance.urls')),

    #API - Module Finance
    path('api/', include('apps.finance.urls')),

    #API - Module Communication
    path('api/', include('apps.communications.urls')),

    #API - Module resources
    path('api/', include('apps.resources.urls')),

    #API - Module documents
    path('api/', include('apps.documents.urls')),

    #API - Module d'analytics
    path('api/', include('apps.analytics.urls')),
]

#Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

#Personnalisation de l'interface d'administration
admin.site.site_header = "University Management System"
admin.site.site_title = "UMS Admin"
admin.site.index_title = "Administration UMS"