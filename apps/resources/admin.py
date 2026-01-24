from django.contrib import admin
from .models import Equipement, Reservation, ReservationEquipement, Maintenance

# ADMIN : ÉQUIPEMENTS
@admin.register(Equipement)
class EquipementAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les équipements.
    
    Permet de gérer l'inventaire des équipements.
    """
    list_display = [
        'nom',
        'reference',
        'categorie',
        'etat',
        'salle',
        'quantite_disponible',
        'quantite_totale',
        'reservable',
        'est_disponible_display',
    ]
    list_filter = ['categorie', 'etat', 'reservable', 'salle__batiment']
    search_fields = ['nom', 'reference', 'description']
    ordering = ['nom']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description', 'reference', 'categorie')
        }),
        ('Emplacement', {
            'fields': ('salle',)
        }),
        ('État et disponibilité', {
            'fields': ('etat', 'quantite_disponible', 'quantite_totale', 'reservable')
        }),
        ('Acquisition', {
            'fields': ('date_acquisition', 'valeur_acquisition')
        }),
        ('Maintenance', {
            'fields': ('dernier_entretien', 'prochain_entretien')
        }),
        ('Notes', {
            'fields': ('observations',)
        }),
    )
    
    def est_disponible_display(self, obj):
        """
        Affiche si l'équipement est disponible.
        
        Returns:
            bool: True si disponible
        """
        return obj.est_disponible()
    
    est_disponible_display.boolean = True
    est_disponible_display.short_description = 'Disponible'
    
    # Actions personnalisées
    actions = ['marquer_disponible', 'marquer_hors_service']
    
    def marquer_disponible(self, request, queryset):
        """Action admin : Marquer comme disponibles."""
        count = queryset.update(etat='DISPONIBLE')
        self.message_user(request, f"{count} équipement(s) marqué(s) comme disponible(s).")
    
    marquer_disponible.short_description = "Marquer comme disponible"
    
    def marquer_hors_service(self, request, queryset):
        """Action admin : Marquer comme hors service."""
        count = queryset.update(etat='HORS_SERVICE')
        self.message_user(request, f"{count} équipement(s) marqué(s) comme hors service.")
    
    marquer_hors_service.short_description = "Marquer comme hors service"

# INLINE : RÉSERVATION ÉQUIPEMENT
class ReservationEquipementInline(admin.TabularInline):
    """
    Inline pour afficher les équipements dans une réservation.
    """
    model = ReservationEquipement
    extra = 1
    fields = ['equipement', 'quantite', 'retourne', 'date_retour', 'etat_retour']
    readonly_fields = ['date_retour']

# ADMIN : RÉSERVATIONS
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les réservations.
    
    Permet de gérer les réservations de salles et équipements.
    """
    list_display = [
        'demandeur',
        'type_reservation',
        'salle',
        'date_debut',
        'date_fin',
        'duree_heures_display',
        'motif',
        'statut',
        'valide_par',
    ]
    list_filter = ['type_reservation', 'statut', 'date_debut']
    search_fields = [
        'demandeur__username',
        'demandeur__first_name',
        'demandeur__last_name',
        'motif',
        'salle__nom'
    ]
    ordering = ['-date_debut']
    date_hierarchy = 'date_debut'
    
    fieldsets = (
        ('Demandeur', {
            'fields': ('demandeur',)
        }),
        ('Type et ressources', {
            'fields': ('type_reservation', 'salle')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin')
        }),
        ('Détails', {
            'fields': ('motif', 'description', 'nombre_participants')
        }),
        ('Validation', {
            'fields': ('statut', 'valide_par', 'date_validation', 'commentaire_validation')
        }),
    )
    
    readonly_fields = ['date_validation']
    
    inlines = [ReservationEquipementInline]
    
    def duree_heures_display(self, obj):
        """
        Affiche la durée en heures.
        
        Returns:
            str: Durée formatée
        """
        return f"{obj.calculer_duree():.1f}h"
    
    duree_heures_display.short_description = 'Durée'
    
    # Actions personnalisées
    actions = ['valider_reservations', 'rejeter_reservations']
    
    def valider_reservations(self, request, queryset):
        """Action admin : Valider plusieurs réservations."""
        count = 0
        for reservation in queryset.filter(statut='EN_ATTENTE'):
            reservation.valider(request.user)
            
            # Réserver les équipements
            for equip_reserve in reservation.equipements_reserves.all():
                equip_reserve.equipement.reserver(equip_reserve.quantite)
            
            count += 1
        
        self.message_user(request, f"{count} réservation(s) validée(s).")
    
    valider_reservations.short_description = "Valider les réservations sélectionnées"
    
    def rejeter_reservations(self, request, queryset):
        """Action admin : Rejeter plusieurs réservations."""
        count = 0
        for reservation in queryset.filter(statut='EN_ATTENTE'):
            reservation.rejeter(request.user, "Rejeté via admin")
            count += 1
        
        self.message_user(request, f"{count} réservation(s) rejetée(s).")
    
    rejeter_reservations.short_description = "Rejeter les réservations sélectionnées"

# ADMIN : RÉSERVATION ÉQUIPEMENT
@admin.register(ReservationEquipement)
class ReservationEquipementAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les équipements réservés.
    """
    list_display = [
        'reservation',
        'equipement',
        'quantite',
        'retourne',
        'date_retour',
    ]
    list_filter = ['retourne', 'equipement__categorie']
    search_fields = [
        'reservation__demandeur__username',
        'equipement__nom',
        'equipement__reference'
    ]
    ordering = ['-reservation__date_debut']
    
    fieldsets = (
        ('Réservation', {
            'fields': ('reservation', 'equipement', 'quantite')
        }),
        ('Retour', {
            'fields': ('retourne', 'date_retour', 'etat_retour')
        }),
    )
    
    readonly_fields = ['date_retour']

# ADMIN : MAINTENANCES
@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les maintenances.
    
    Permet de gérer les maintenances préventives et correctives.
    """
    list_display = [
        'equipement',
        'type_maintenance',
        'statut',
        'date_planifiee',
        'date_debut',
        'date_fin',
        'technicien',
        'cout_total_display',
    ]
    list_filter = ['type_maintenance', 'statut', 'date_planifiee']
    search_fields = [
        'equipement__nom',
        'equipement__reference',
        'technicien__username',
        'description'
    ]
    ordering = ['-date_planifiee']
    date_hierarchy = 'date_planifiee'
    
    fieldsets = (
        ('Équipement', {
            'fields': ('equipement',)
        }),
        ('Type et statut', {
            'fields': ('type_maintenance', 'statut')
        }),
        ('Planification', {
            'fields': ('date_planifiee', 'date_debut', 'date_fin', 'technicien')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Intervention', {
            'fields': ('travaux_effectues', 'pieces_remplacees')
        }),
        ('Coûts', {
            'fields': ('cout_main_oeuvre', 'cout_pieces')
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
    )
    
    readonly_fields = ['date_debut', 'date_fin']
    
    def cout_total_display(self, obj):
        """
        Affiche le coût total.
        
        Returns:
            str: Coût formaté
        """
        return f"{obj.calculer_cout_total()} FCFA"
    
    cout_total_display.short_description = 'Coût total'
    
    # Actions personnalisées
    actions = ['demarrer_maintenances', 'annuler_maintenances']
    
    def demarrer_maintenances(self, request, queryset):
        """Action admin : Démarrer plusieurs maintenances."""
        count = 0
        for maintenance in queryset.filter(statut='PLANIFIEE'):
            maintenance.demarrer()
            count += 1
        
        self.message_user(request, f"{count} maintenance(s) démarrée(s).")
    
    demarrer_maintenances.short_description = "Démarrer les maintenances sélectionnées"
    
    def annuler_maintenances(self, request, queryset):
        """Action admin : Annuler plusieurs maintenances."""
        count = 0
        for maintenance in queryset.exclude(statut='TERMINEE'):
            maintenance.annuler()
            count += 1
        
        self.message_user(request, f"{count} maintenance(s) annulée(s).")
    
    annuler_maintenances.short_description = "Annuler les maintenances sélectionnées"
