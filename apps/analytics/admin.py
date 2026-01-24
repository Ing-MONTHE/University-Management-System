from django.contrib import admin
from .models import Rapport, Dashboard, KPI


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = [
        'titre',
        'type_rapport',
        'format_export',
        'date_debut',
        'date_fin',
        'genere',
        'planifie',
        'frequence',
    ]
    list_filter = ['type_rapport', 'format_export', 'genere', 'planifie', 'frequence']
    search_fields = ['titre', 'description']
    ordering = ['-date_generation', '-created_at']
    date_hierarchy = 'date_generation'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'type_rapport', 'format_export')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin')
        }),
        ('Filtres', {
            'fields': ('annee_academique', 'filiere')
        }),
        ('Génération', {
            'fields': ('fichier', 'genere', 'date_generation', 'genere_par')
        }),
        ('Planification', {
            'fields': ('planifie', 'frequence', 'prochaine_execution')
        }),
        ('Paramètres', {
            'fields': ('parametres',)
        }),
    )
    
    readonly_fields = ['date_generation']
    
    actions = ['generer_rapports']
    
    def generer_rapports(self, request, queryset):
        count = 0
        for rapport in queryset.filter(genere=False):
            rapport.generer_rapport(request.user)
            count += 1
        
        self.message_user(request, f"{count} rapport(s) généré(s).")
    
    generer_rapports.short_description = "Générer les rapports sélectionnés"


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_dashboard', 'proprietaire', 'partage', 'par_defaut']
    list_filter = ['type_dashboard', 'partage', 'par_defaut']
    search_fields = ['nom', 'description', 'proprietaire__username']
    ordering = ['nom']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description', 'type_dashboard')
        }),
        ('Propriétaire', {
            'fields': ('proprietaire',)
        }),
        ('Partage', {
            'fields': ('partage', 'utilisateurs_partages')
        }),
        ('Configuration', {
            'fields': ('configuration', 'par_defaut')
        }),
    )


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = [
        'nom',
        'code',
        'categorie',
        'type_valeur',
        'valeur',
        'objectif',
        'date_calcul',
        'actif',
    ]
    list_filter = ['categorie', 'type_valeur', 'actif']
    search_fields = ['nom', 'code', 'description']
    ordering = ['categorie', 'nom']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description', 'code')
        }),
        ('Catégorie et type', {
            'fields': ('categorie', 'type_valeur')
        }),
        ('Valeurs', {
            'fields': ('valeur', 'objectif')
        }),
        ('Période', {
            'fields': ('date_calcul',)
        }),
        ('Filtres', {
            'fields': ('annee_academique', 'filiere')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )
    
    actions = ['activer_kpis', 'desactiver_kpis']
    
    def activer_kpis(self, request, queryset):
        count = queryset.update(actif=True)
        self.message_user(request, f"{count} KPI(s) activé(s).")
    
    activer_kpis.short_description = "Activer les KPIs sélectionnés"
    
    def desactiver_kpis(self, request, queryset):
        count = queryset.update(actif=False)
        self.message_user(request, f"{count} KPI(s) désactivé(s).")
    
    desactiver_kpis.short_description = "Désactiver les KPIs sélectionnés"
