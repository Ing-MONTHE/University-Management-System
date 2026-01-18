from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    #Admin django
    path('admin/', admin.site.urls),

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
]

#Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

#Personnalisation de l'interface d'administration
admin.site.site_header = "University Management System"
admin.site.site_title = "UMS Admin"
admin.site.index_title = "Administration UMS"
