# Configuration de l'interface d'administration Django pour les modèles User, Role, Permission et AuditLog.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission, AuditLog

# CONFIGURATION ADMIN POUR USER
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Configuration de l'admin pour User.
    
    # Colonnes affichées dans la liste
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at']
    
    # Filtres sur le côté
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    
    # Champs de recherche
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    # Ordre d'affichage
    ordering = ['-created_at']
    
    # Organisation des champs dans le formulaire
    fieldsets = (
        ('Informations de connexion', {
            'fields': ('username', 'email', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'roles')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)  # Section repliable
        }),
    )
    
    # Champs en lecture seule
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    # Champs pour créer un nouvel utilisateur
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

# CONFIGURATION ADMIN POUR PERMISSION
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    # Configuration de l'admin pour Permission.
    
    list_display = ['name', 'code', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['category', 'name']

# CONFIGURATION ADMIN POUR ROLE
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    # Configuration de l'admin pour Role.
    
    list_display = ['name', 'is_active', 'created_at', 'get_permissions_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']  # Interface pour sélectionner plusieurs permissions
    
    def get_permissions_count(self, obj):
        """Afficher le nombre de permissions."""
        return obj.permissions.count()
    get_permissions_count.short_description = 'Nombre de permissions'

# CONFIGURATION ADMIN POUR AUDITLOG
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    # Configuration de l'admin pour AuditLog.
    
    list_display = ['user', 'action', 'table_name', 'object_id', 'timestamp', 'ip_address']
    list_filter = ['action', 'table_name', 'timestamp']
    search_fields = ['user__username', 'table_name', 'object_id', 'ip_address']
    ordering = ['-timestamp']
    
    # Tout en lecture seule (on ne modifie jamais les logs !)
    readonly_fields = ['user', 'action', 'table_name', 'object_id', 'details', 
                      'ip_address', 'user_agent', 'timestamp']
    
    # Désactiver l'ajout et la modification
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
# Fin de la configuration admin.py