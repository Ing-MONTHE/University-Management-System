# Configuration de l'interface d'administration pour emploi du temps

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
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
        count = obj.get_nombre_salles()
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )
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
        duree = obj.get_duree_minutes()
        heures = duree // 60
        minutes = duree % 60
        
        if minutes == 0:
            texte = f"{heures}h"
        else:
            texte = f"{heures}h{minutes:02d}"
        
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            texte
        )
    get_duree.short_description = 'Durée'

# COURS ADMIN
@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    """Configuration admin pour Cours."""
    
    list_display = [
        'get_matiere', 'get_filiere', 'get_enseignant',
        'get_creneau', 'salle', 'type_cours', 'effectif_prevu',
        'semestre', 'get_is_actif'
    ]
    list_filter = [
        'annee_academique', 'filiere', 'matiere',
        'type_cours', 'semestre', 'is_actif',
        'creneau__jour', 'created_at'
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
            'fields': ('matiere', 'enseignant', 'filiere', 'type_cours', 'semestre')
        }),
        ('Programmation', {
            'fields': ('creneau', 'salle')
        }),
        ('Effectif', {
            'fields': ('effectif_prevu',)
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_actif', 'remarques')
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
    
    def get_is_actif(self, obj):
        """Statut actif."""
        if obj.is_actif:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    get_is_actif.short_description = 'Statut'
    
    actions = ['dupliquer_cours', 'desactiver_cours', 'activer_cours']
    
    def dupliquer_cours(self, request, queryset):
        """Action pour dupliquer des cours."""
        count = 0
        for cours in queryset:
            # Créer une copie
            cours.pk = None
            cours.is_actif = False
            cours.save()
            count += 1
        self.message_user(request, f"{count} cours dupliqué(s). Modifiez les créneaux/salles avant activation.")
    dupliquer_cours.short_description = "Dupliquer les cours sélectionnés"
    
    def desactiver_cours(self, request, queryset):
        """Action pour désactiver des cours."""
        count = queryset.update(is_actif=False)
        self.message_user(request, f"{count} cours désactivé(s).")
    desactiver_cours.short_description = "Désactiver les cours sélectionnés"
    
    def activer_cours(self, request, queryset):
        """Action pour activer des cours."""
        count = queryset.update(is_actif=True)
        self.message_user(request, f"{count} cours activé(s).")
    activer_cours.short_description = "Activer les cours sélectionnés"

# CONFLIT SALLE ADMIN
@admin.register(ConflitSalle)
class ConflitSalleAdmin(admin.ModelAdmin):
    """Configuration admin pour Conflit de salle."""
    
    list_display = [
        'id', 'get_type_coloré', 'get_statut_coloré',
        'get_cours1', 'get_cours2', 'date_detection'
    ]
    list_filter = ['type_conflit', 'statut', 'date_detection']
    search_fields = [
        'description', 'solution_appliquee',
        'cours1__matiere__nom', 'cours2__matiere__nom'
    ]
    ordering = ['-date_detection']
    
    fieldsets = (
        ('Type de conflit', {
            'fields': ('type_conflit', 'description')
        }),
        ('Cours en conflit', {
            'fields': ('cours1', 'cours2')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Résolution', {
            'fields': ('solution_appliquee',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_detection', 'date_resolution', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_detection', 'created_at', 'updated_at']
    
    def get_type_coloré(self, obj):
        """Type de conflit coloré."""
        colors = {
            'SALLE': 'red',
            'ENSEIGNANT': 'orange',
            'CAPACITE': 'darkred'
        }
        color = colors.get(obj.type_conflit, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_type_conflit_display()
        )
    get_type_coloré.short_description = 'Type'
    
    def get_statut_coloré(self, obj):
        """Statut coloré."""
        colors = {
            'DETECTE': 'red',
            'EN_COURS': 'orange',
            'RESOLU': 'green',
            'IGNORE': 'gray'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    get_statut_coloré.short_description = 'Statut'
    
    def get_cours1(self, obj):
        """Premier cours."""
        return format_html(
            '{} - {} - {}',
            obj.cours1.matiere.code,
            obj.cours1.filiere.code,
            obj.cours1.creneau
        )
    get_cours1.short_description = 'Cours 1'
    
    def get_cours2(self, obj):
        """Deuxième cours."""
        if obj.cours2:
            return format_html(
                '{} - {} - {}',
                obj.cours2.matiere.code,
                obj.cours2.filiere.code,
                obj.cours2.creneau
            )
        return format_html('<span style="color: gray;">N/A</span>')
    get_cours2.short_description = 'Cours 2'
    
    actions = ['marquer_en_cours', 'marquer_resolu', 'marquer_ignore']
    
    def marquer_en_cours(self, request, queryset):
        """Action pour marquer en cours."""
        count = queryset.update(statut='EN_COURS')
        self.message_user(request, f"{count} conflit(s) marqué(s) en cours de résolution.")
    marquer_en_cours.short_description = "Marquer comme en cours"
    
    def marquer_resolu(self, request, queryset):
        """Action pour marquer résolu."""
        from django.utils import timezone
        count = 0
        for conflit in queryset:
            conflit.statut = 'RESOLU'
            conflit.date_resolution = timezone.now()
            conflit.save()
            count += 1
        self.message_user(request, f"{count} conflit(s) marqué(s) comme résolu(s).")
    marquer_resolu.short_description = "Marquer comme résolu"
    
    def marquer_ignore(self, request, queryset):
        """Action pour ignorer."""
        count = queryset.update(statut='IGNORE')
        self.message_user(request, f"{count} conflit(s) ignoré(s).")
    marquer_ignore.short_description = "Ignorer"
