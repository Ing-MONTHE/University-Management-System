from django.contrib import admin
from .models import FeuillePresence, Presence, JustificatifAbsence

# ADMIN : FEUILLES DE PRÉSENCE
@admin.register(FeuillePresence)
class FeuillePresenceAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les feuilles de présence.
    
    Affiche les informations essentielles et permet de filtrer/rechercher.
    """
    list_display = [
        'cours',
        'date_cours',
        'heure_debut',
        'heure_fin',
        'statut',
        'nombre_presents',
        'nombre_absents',
        'nombre_retards',
        'taux_presence_display',
    ]
    list_filter = ['statut', 'date_cours', 'cours__matiere']
    search_fields = [
        'cours__matiere__nom',
        'cours__enseignant__user__first_name',
        'cours__enseignant__user__last_name'
    ]
    ordering = ['-date_cours', '-heure_debut']
    date_hierarchy = 'date_cours'
    
    # Organisation des champs dans le formulaire
    fieldsets = (
        ('Informations du cours', {
            'fields': ('cours', 'date_cours', 'heure_debut', 'heure_fin')
        }),
        ('Statut et statistiques', {
            'fields': ('statut', 'nombre_presents', 'nombre_absents', 'nombre_retards')
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
    )
    
    readonly_fields = ['nombre_presents', 'nombre_absents', 'nombre_retards']
    
    def taux_presence_display(self, obj):
        """
        Affiche le taux de présence avec formatage coloré.
        
        Returns:
            str: Taux formaté (ex: "85.5%")
        """
        taux = obj.calculer_taux_presence()
        return f"{taux}%"
    
    taux_presence_display.short_description = 'Taux de présence'

# ADMIN : PRÉSENCES
@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les présences individuelles.
    
    Permet de gérer les présences/absences/retards des étudiants.
    """
    list_display = [
        'etudiant',
        'feuille_presence',
        'statut',
        'heure_arrivee',
        'absence_justifiee',
        'minutes_retard_display',
    ]
    list_filter = ['statut', 'absence_justifiee', 'feuille_presence__date_cours']
    search_fields = [
        'etudiant__user__first_name',
        'etudiant__user__last_name',
        'etudiant__matricule',
        'feuille_presence__cours__matiere__nom'
    ]
    ordering = ['-feuille_presence__date_cours', 'etudiant__user__last_name']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('feuille_presence', 'etudiant')
        }),
        ('Statut de présence', {
            'fields': ('statut', 'heure_arrivee', 'absence_justifiee')
        }),
        ('Remarques', {
            'fields': ('remarque',)
        }),
    )
    
    def minutes_retard_display(self, obj):
        """
        Affiche les minutes de retard.
        
        Returns:
            str: Minutes de retard ou "-"
        """
        if obj.statut == 'RETARD':
            minutes = obj.calculer_minutes_retard()
            return f"{minutes} min"
        return "-"
    
    minutes_retard_display.short_description = 'Retard'

# ADMIN : JUSTIFICATIFS D'ABSENCE
@admin.register(JustificatifAbsence)
class JustificatifAbsenceAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les justificatifs d'absence.
    
    Permet de valider/rejeter les justificatifs soumis par les étudiants.
    """
    list_display = [
        'etudiant',
        'date_debut',
        'date_fin',
        'duree_display',
        'type_justificatif',
        'statut',
        'date_soumission',
        'date_traitement',
    ]
    list_filter = ['statut', 'type_justificatif', 'date_soumission']
    search_fields = [
        'etudiant__user__first_name',
        'etudiant__user__last_name',
        'etudiant__matricule',
        'motif'
    ]
    ordering = ['-date_soumission']
    date_hierarchy = 'date_soumission'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('etudiant', 'date_debut', 'date_fin', 'type_justificatif')
        }),
        ('Justificatif', {
            'fields': ('motif', 'document')
        }),
        ('Traitement', {
            'fields': ('statut', 'commentaire_validation', 'date_traitement')
        }),
    )
    
    readonly_fields = ['date_soumission', 'date_traitement']
    
    def duree_display(self, obj):
        """
        Affiche la durée en jours.
        
        Returns:
            str: Durée formatée (ex: "3 jours")
        """
        duree = obj.calculer_duree()
        return f"{duree} jour{'s' if duree > 1 else ''}"
    
    duree_display.short_description = 'Durée'
    
    # Actions personnalisées dans l'admin
    actions = ['valider_justificatifs', 'rejeter_justificatifs']
    
    def valider_justificatifs(self, request, queryset):
        """
        Action admin : Valider plusieurs justificatifs en masse.
        
        Args:
            request: Requête HTTP
            queryset: Justificatifs sélectionnés
        """
        count = 0
        for justificatif in queryset.filter(statut='EN_ATTENTE'):
            justificatif.valider(commentaire='Validé en masse via admin')
            count += 1
        
        self.message_user(
            request,
            f"{count} justificatif(s) validé(s) avec succès."
        )
    
    valider_justificatifs.short_description = "Valider les justificatifs sélectionnés"
    
    def rejeter_justificatifs(self, request, queryset):
        """
        Action admin : Rejeter plusieurs justificatifs en masse.
        
        Args:
            request: Requête HTTP
            queryset: Justificatifs sélectionnés
        """
        count = 0
        for justificatif in queryset.filter(statut='EN_ATTENTE'):
            justificatif.rejeter(commentaire='Rejeté en masse via admin')
            count += 1
        
        self.message_user(
            request,
            f"{count} justificatif(s) rejeté(s)."
        )
    
    rejeter_justificatifs.short_description = "Rejeter les justificatifs sélectionnés"
