# Configuration de l'interface d'administration académique

from django.contrib import admin
from .models import AnneeAcademique, Faculte, Departement, Filiere, Matiere

# ANNEE ACADEMIQUE ADMIN
@admin.register(AnneeAcademique)
class AnneeAcademiqueAdmin(admin.ModelAdmin):
    # Configuration admin pour Année Académique
    
    list_display = ['code', 'date_debut', 'date_fin', 'is_active', 'created_at']
    list_filter = ['is_active', 'date_debut']
    search_fields = ['code']
    ordering = ['-date_debut']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'date_debut', 'date_fin')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activer_annees']
    
    def activer_annees(self, request, queryset):
        # Action pour activer les années sélectionnées.
        if queryset.count() > 1:
            self.message_user(request, "Vous ne pouvez activer qu'une seule année à la fois.", level='error')
            return
        
        annee = queryset.first()
        annee.activate()
        self.message_user(request, f"Année {annee.code} activée avec succès.")
    
    activer_annees.short_description = "Activer l'année sélectionnée"

# FACULTE ADMIN
@admin.register(Faculte)
class FaculteAdmin(admin.ModelAdmin):
    # Configuration admin pour Faculté.
    
    list_display = ['code', 'nom', 'doyen', 'get_departements_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'nom', 'doyen']
    ordering = ['nom']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'nom', 'description')
        }),
        ('Responsable', {
            'fields': ('doyen',)
        }),
        ('Contact', {
            'fields': ('email', 'telephone')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_departements_count(self, obj):
        # Afficher le nombre de départements.
        return obj.departements.count()
    get_departements_count.short_description = 'Nb départements'

# DEPARTEMENT ADMIN
@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    # Configuration admin pour Département.
    
    list_display = ['code', 'nom', 'faculte', 'chef_departement', 'get_filieres_count', 'created_at']
    list_filter = ['faculte', 'created_at']
    search_fields = ['code', 'nom', 'chef_departement']
    ordering = ['faculte', 'nom']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('faculte', 'code', 'nom', 'description')
        }),
        ('Responsable', {
            'fields': ('chef_departement',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_filieres_count(self, obj):
        """Afficher le nombre de filières."""
        return obj.filieres.count()
    get_filieres_count.short_description = 'Nb filières'

# FILIERE ADMIN
@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    # Configuration admin pour Filière.
    
    list_display = [
        'code', 'nom', 'cycle', 'departement', 
        'duree_annees', 'frais_inscription', 'get_matieres_count', 'is_active'
    ]
    list_filter = ['cycle', 'departement', 'is_active', 'created_at']
    search_fields = ['code', 'nom']
    ordering = ['departement', 'cycle', 'nom']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('departement', 'code', 'nom', 'description')
        }),
        ('Cycle et durée', {
            'fields': ('cycle', 'duree_annees')
        }),
        ('Frais', {
            'fields': ('frais_inscription',)
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_matieres_count(self, obj):
        # Afficher le nombre de matières.
        return obj.matieres.count()
    get_matieres_count.short_description = 'Nb matières'

# MATIERE ADMIN
@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    # Configuration admin pour Matière.
    
    list_display = [
        'code', 'nom', 'coefficient', 'credits', 
        'get_volume_total', 'semestre', 'is_optionnelle'
    ]
    list_filter = ['semestre', 'is_optionnelle', 'created_at']
    search_fields = ['code', 'nom']
    ordering = ['semestre', 'nom']
    
    filter_horizontal = ['filieres']  # Interface pour sélectionner plusieurs filières
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'nom', 'description')
        }),
        ('Filières', {
            'fields': ('filieres',)
        }),
        ('Pondération', {
            'fields': ('coefficient', 'credits')
        }),
        ('Volume horaire', {
            'fields': ('volume_horaire_cm', 'volume_horaire_td', 'volume_horaire_tp')
        }),
        ('Organisation', {
            'fields': ('semestre', 'is_optionnelle')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_volume_total(self, obj):
        # Afficher le volume horaire total.
        return obj.get_volume_horaire_total()
    get_volume_total.short_description = 'Volume total (h)'
