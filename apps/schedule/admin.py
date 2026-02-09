"""
Configuration de l'interface d'administration pour schedule
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Batiment, Salle, Creneau, Cours, ConflitSalle


# BATIMENT ADMIN
@admin.register(Batiment)
class BatimentAdmin(admin.ModelAdmin):
    """Configuration admin pour Bâtiment."""
    
    list_display = [
        'code', 'nom', 'nombre_etages', 'get_nombre_salles',
        'get_is_active', 'created_at'
    ]
    list_filter = ['is_active', 'nombre_etages', 'created_at']
    search_fields = ['code', 'nom', 'adresse']
    ordering = ['code']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'nom', 'nombre_etages')
        }),
        ('Localisation', {
            'fields': ('adresse',)
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
    
    def get_nombre_salles(self, obj):
        """Nombre de salles."""
        count = obj.nombre_salles  # ✓ CORRIGÉ: utilise la property
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    get_nombre_salles.short_description = 'Nb salles'
    
    def get_is_active(self, obj):
        """Statut actif."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    get_is_active.short_description = 'Statut'


# SALLE ADMIN
@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    """Configuration admin pour Salle."""
    
    list_display = [
        'code', 'nom', 'batiment', 'type_salle',
        'capacite', 'etage', 'get_is_disponible', 'created_at'
    ]
    list_filter = [
        'batiment', 'type_salle', 'is_disponible',
        'etage', 'created_at'
    ]
    search_fields = ['code', 'nom', 'equipements']
    ordering = ['batiment', 'etage', 'code']
    
    fieldsets = (
        ('Localisation', {
            'fields': ('batiment', 'etage')
        }),
        ('Identification', {
            'fields': ('code', 'nom', 'type_salle')
        }),
        ('Caractéristiques', {
            'fields': ('capacite', 'equipements')
        }),
        ('Statut', {
            'fields': ('is_disponible',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_is_disponible(self, obj):
        """Statut disponible."""
        if obj.is_disponible:
            return format_html('<span style="color: green;">✓ Disponible</span>')
        return format_html('<span style="color: red;">✗ Indisponible</span>')
    get_is_disponible.short_description = 'Disponibilité'


# CRENEAU ADMIN
@admin.register(Creneau)
class CreneauAdmin(admin.ModelAdmin):
    """Configuration admin pour Créneau."""
    
    list_display = [
        'code', 'jour', 'heure_debut', 'heure_fin',
        'get_duree', 'created_at'
    ]
    list_filter = ['jour', 'created_at']
    search_fields = ['code']
    ordering = ['jour', 'heure_debut']
    
    fieldsets = (
        ('Identification', {
            'fields': ('code',)
        }),
        ('Horaire', {
            'fields': ('jour', 'heure_debut', 'heure_fin')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_duree(self, obj):
        """Durée du créneau."""
        duree = obj.duree_minutes  # ✓ CORRIGÉ: utilise la property
        heures = duree // 60
        minutes = duree % 60
        
        if minutes == 0:
            texte = f"{heures}h"
        else:
            texte = f"{heures}h{minutes:02d}"
        
        return format_html('<span style="font-weight: bold;">{}</span>', texte)
    get_duree.short_description = 'Durée'


# COURS ADMIN
@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    """Configuration admin pour Cours."""
    
    list_display = [
        'get_matiere', 'get_filiere', 'get_enseignant',
        'get_creneau', 'salle', 'type_cours',
        'annee_academique'
    ]
    list_filter = [
        'annee_academique', 'filiere', 'matiere',
        'type_cours', 'creneau__jour', 'created_at'
    ]
    search_fields = [
        'matiere__nom', 'matiere__code',
        'filiere__nom', 'filiere__code',
        'enseignant__user__first_name',
        'enseignant__user__last_name',
        'salle__code'
    ]
    ordering = ['creneau__jour', 'creneau__heure_debut']
    
    fieldsets = (
        ('Année académique', {
            'fields': ('annee_academique',)
        }),
        ('Cours', {
            'fields': ('matiere', 'enseignant', 'filiere', 'type_cours')
        }),
        ('Programmation', {
            'fields': ('creneau', 'salle')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_matiere(self, obj):
        """Matière."""
        return f"{obj.matiere.code} - {obj.matiere.nom}"
    get_matiere.short_description = 'Matière'
    
    def get_filiere(self, obj):
        """Filière."""
        return obj.filiere.code
    get_filiere.short_description = 'Filière'
    
    def get_enseignant(self, obj):
        """Enseignant."""
        if obj.enseignant:
            return obj.enseignant.user.get_full_name()
        return format_html('<span style="color: gray;">Non assigné</span>')
    get_enseignant.short_description = 'Enseignant'
    
    def get_creneau(self, obj):
        """Créneau."""
        return format_html(
            '<span style="font-weight: bold;">{} {}-{}</span>',
            obj.creneau.get_jour_display(),
            obj.creneau.heure_debut.strftime('%H:%M'),
            obj.creneau.heure_fin.strftime('%H:%M')
        )
    get_creneau.short_description = 'Créneau'


# CONFLIT SALLE ADMIN
@admin.register(ConflitSalle)
class ConflitSalleAdmin(admin.ModelAdmin):
    """Configuration admin pour Conflit de salle."""
    
    list_display = [
        'id', 'salle', 'get_cours1_info', 'get_cours2_info',
        'get_resolu_colore', 'date_detection'
    ]
    list_filter = ['resolu', 'salle', 'date_detection']
    search_fields = [
        'salle__code',
        'cours1__matiere__nom',
        'cours2__matiere__nom'
    ]
    ordering = ['-date_detection']
    
    fieldsets = (
        ('Conflit', {
            'fields': ('salle', 'cours1', 'cours2')
        }),
        ('Résolution', {
            'fields': ('resolu',)
        }),
        ('Dates', {
            'fields': ('date_detection', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_detection', 'created_at', 'updated_at']
    
    def get_cours1_info(self, obj):
        """Premier cours."""
        return format_html(
            '{} - {} - {}',
            obj.cours1.matiere.code,
            obj.cours1.filiere.code,
            obj.cours1.creneau
        )
    get_cours1_info.short_description = 'Cours 1'
    
    def get_cours2_info(self, obj):
        """Deuxième cours."""
        return format_html(
            '{} - {} - {}',
            obj.cours2.matiere.code,
            obj.cours2.filiere.code,
            obj.cours2.creneau
        )
    get_cours2_info.short_description = 'Cours 2'
    
    def get_resolu_colore(self, obj):
        """Statut résolu coloré."""
        if obj.resolu:
            return format_html('<span style="color: green;">✓ Résolu</span>')
        return format_html('<span style="color: red;">✗ Non résolu</span>')
    get_resolu_colore.short_description = 'Statut'
    
    actions = ['marquer_resolu']
    
    def marquer_resolu(self, request, queryset):
        """Marquer comme résolu."""
        count = 0
        for conflit in queryset:
            conflit.resoudre()
            count += 1
        self.message_user(request, f"{count} conflit(s) marqué(s) comme résolu(s).")
    marquer_resolu.short_description = "Marquer comme résolu"
