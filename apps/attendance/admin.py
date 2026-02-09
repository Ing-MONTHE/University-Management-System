"""
Configuration de l'interface d'administration pour attendance
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import FeuillePresence, Presence


# ADMIN : FEUILLES DE PRÉSENCE
@admin.register(FeuillePresence)
class FeuillePresenceAdmin(admin.ModelAdmin):
    """Configuration admin pour les feuilles de présence."""
    
    list_display = [
        'get_cours_info',
        'date_cours',
        'heure_debut',
        'heure_fin',
        'get_statut_colore',
        'get_nombre_presents',
        'get_nombre_absents',
        'get_taux_presence_colore',
    ]
    list_filter = ['statut', 'date_cours', 'cours__matiere']
    search_fields = [
        'cours__matiere__nom',
        'cours__enseignant__user__first_name',
        'cours__enseignant__user__last_name'
    ]
    ordering = ['-date_cours', '-heure_debut']
    date_hierarchy = 'date_cours'
    
    fieldsets = (
        ('Informations du cours', {
            'fields': ('cours', 'date_cours', 'heure_debut', 'heure_fin')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_cours_info(self, obj):
        """Affiche les informations du cours."""
        return f"{obj.cours.matiere.code} - {obj.cours.filiere.code}"
    get_cours_info.short_description = 'Cours'
    
    def get_statut_colore(self, obj):
        """Statut coloré."""
        colors = {
            'OUVERTE': 'blue',
            'FERMEE': 'green',
            'ANNULEE': 'red'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    get_statut_colore.short_description = 'Statut'
    
    def get_nombre_presents(self, obj):
        """Nombre de présents."""
        return obj.nombre_presents
    get_nombre_presents.short_description = 'Présents'
    
    def get_nombre_absents(self, obj):
        """Nombre d'absents."""
        absents = obj.nombre_absents
        if absents > 0:
            return format_html('<span style="color: red;">{}</span>', absents)
        return absents
    get_nombre_absents.short_description = 'Absents'
    
    def get_taux_presence_colore(self, obj):
        """Taux de présence coloré."""
        taux = obj.taux_presence
        if taux >= 80:
            color = 'green'
        elif taux >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} %</span>',
            color, taux
        )
    get_taux_presence_colore.short_description = 'Taux présence'
    
    actions = ['fermer_feuilles', 'annuler_feuilles']
    
    def fermer_feuilles(self, request, queryset):
        """Fermer les feuilles sélectionnées."""
        count = 0
        for feuille in queryset.filter(statut='OUVERTE'):
            feuille.fermer()
            count += 1
        self.message_user(request, f"{count} feuille(s) fermée(s).")
    fermer_feuilles.short_description = "Fermer les feuilles sélectionnées"
    
    def annuler_feuilles(self, request, queryset):
        """Annuler les feuilles sélectionnées."""
        count = 0
        for feuille in queryset:
            feuille.annuler()
            count += 1
        self.message_user(request, f"{count} feuille(s) annulée(s).")
    annuler_feuilles.short_description = "Annuler les feuilles sélectionnées"


# ADMIN : PRÉSENCES
@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    """Configuration admin pour les présences individuelles."""
    
    list_display = [
        'get_etudiant',
        'get_cours',
        'get_date_cours',
        'get_statut_colore',
        'get_justification',
    ]
    list_filter = [
        'statut',
        'feuille__date_cours',
        'feuille__cours__matiere'
    ]
    search_fields = [
        'etudiant__user__first_name',
        'etudiant__user__last_name',
        'etudiant__matricule',
        'feuille__cours__matiere__nom'
    ]
    ordering = ['-feuille__date_cours', 'etudiant__user__last_name']
    date_hierarchy = 'feuille__date_cours'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('feuille', 'etudiant')
        }),
        ('Statut de présence', {
            'fields': ('statut', 'justificatif')
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_etudiant(self, obj):
        """Affiche l'étudiant."""
        return f"{obj.etudiant.matricule} - {obj.etudiant.user.get_full_name()}"
    get_etudiant.short_description = 'Étudiant'
    
    def get_cours(self, obj):
        """Affiche le cours."""
        return f"{obj.feuille.cours.matiere.code}"
    get_cours.short_description = 'Matière'
    
    def get_date_cours(self, obj):
        """Affiche la date du cours."""
        return obj.feuille.date_cours
    get_date_cours.short_description = 'Date'
    get_date_cours.admin_order_field = 'feuille__date_cours'
    
    def get_statut_colore(self, obj):
        """Statut coloré."""
        colors = {
            'PRESENT': 'green',
            'ABSENT': 'red',
            'RETARD': 'orange',
            'ABSENT_JUSTIFIE': 'blue'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    get_statut_colore.short_description = 'Statut'
    
    def get_justification(self, obj):
        """Affiche si justifié."""
        if obj.est_justifie:
            return format_html('<span style="color: green;">✓ Justifié</span>')
        elif obj.est_absent:
            return format_html('<span style="color: red;">✗ Non justifié</span>')
        return '-'
    get_justification.short_description = 'Justification'
    
    actions = ['marquer_present', 'marquer_absent', 'marquer_retard']
    
    def marquer_present(self, request, queryset):
        """Marquer comme présent."""
        count = 0
        for presence in queryset:
            presence.marquer_present()
            count += 1
        self.message_user(request, f"{count} présence(s) marquée(s).")
    marquer_present.short_description = "Marquer comme PRÉSENT"
    
    def marquer_absent(self, request, queryset):
        """Marquer comme absent."""
        count = 0
        for presence in queryset:
            presence.marquer_absent()
            count += 1
        self.message_user(request, f"{count} absence(s) marquée(s).")
    marquer_absent.short_description = "Marquer comme ABSENT"
    
    def marquer_retard(self, request, queryset):
        """Marquer comme en retard."""
        count = 0
        for presence in queryset:
            presence.marquer_retard()
            count += 1
        self.message_user(request, f"{count} retard(s) marqué(s).")
    marquer_retard.short_description = "Marquer comme RETARD"
    