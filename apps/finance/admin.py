from django.contrib import admin
from .models import FraisScolarite, Paiement, Bourse, Facture

# ADMIN : FRAIS DE SCOLARITÉ
@admin.register(FraisScolarite)
class FraisScolariteAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les frais de scolarité.
    
    Permet de gérer les tarifs par filière, niveau et année.
    """
    list_display = [
        'filiere',
        'niveau',
        'annee_academique',
        'montant_total',
        'nombre_tranches',
        'montant_tranche_display',
        'date_limite_paiement',
        'actif',
    ]
    list_filter = ['actif', 'annee_academique', 'filiere__departement__faculte']
    search_fields = ['filiere__nom', 'niveau']
    ordering = ['-annee_academique', 'filiere', 'niveau']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('filiere', 'annee_academique', 'niveau')
        }),
        ('Montants', {
            'fields': ('montant_total', 'nombre_tranches', 'date_limite_paiement')
        }),
        ('Statut', {
            'fields': ('actif', 'description')
        }),
    )
    
    def montant_tranche_display(self, obj):
        """
        Affiche le montant par tranche.
        
        Returns:
            str: Montant formaté
        """
        return f"{obj.montant_par_tranche()} FCFA"
    
    montant_tranche_display.short_description = 'Montant/tranche'

# ADMIN : PAIEMENTS
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les paiements.
    
    Permet de gérer les paiements des étudiants.
    """
    list_display = [
        'numero_recu',
        'inscription',
        'montant',
        'mode_paiement',
        'date_paiement',
        'statut',
        'valide_par',
    ]
    list_filter = ['statut', 'mode_paiement', 'date_paiement']
    search_fields = [
        'numero_recu',
        'inscription__etudiant__user__first_name',
        'inscription__etudiant__user__last_name',
        'inscription__etudiant__matricule'
    ]
    ordering = ['-date_paiement']
    date_hierarchy = 'date_paiement'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('inscription', 'montant', 'mode_paiement', 'date_paiement')
        }),
        ('Références', {
            'fields': ('numero_recu', 'reference_transaction')
        }),
        ('Validation', {
            'fields': ('statut', 'valide_par', 'date_validation')
        }),
        ('Notes', {
            'fields': ('observations',)
        }),
    )
    
    readonly_fields = ['numero_recu', 'valide_par', 'date_validation']
    
    # Actions personnalisées dans l'admin
    actions = ['valider_paiements']
    
    def valider_paiements(self, request, queryset):
        """
        Action admin : Valider plusieurs paiements en masse.
        
        Args:
            request: Requête HTTP
            queryset: Paiements sélectionnés
        """
        count = 0
        for paiement in queryset.filter(statut='EN_ATTENTE'):
            paiement.valider(request.user)
            count += 1
        
        self.message_user(
            request,
            f"{count} paiement(s) validé(s) avec succès."
        )
    
    valider_paiements.short_description = "Valider les paiements sélectionnés"

# ADMIN : BOURSES
@admin.register(Bourse)
class BourseAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les bourses.
    
    Permet de gérer les bourses et exonérations.
    """
    list_display = [
        'etudiant',
        'annee_academique',
        'type_bourse',
        'pourcentage',
        'montant_fixe',
        'source_financement',
        'statut',
        'est_active_display',
    ]
    list_filter = ['type_bourse', 'source_financement', 'statut', 'annee_academique']
    search_fields = [
        'etudiant__user__first_name',
        'etudiant__user__last_name',
        'etudiant__matricule',
        'nom_organisme'
    ]
    ordering = ['-date_debut']
    date_hierarchy = 'date_debut'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('etudiant', 'annee_academique', 'type_bourse')
        }),
        ('Montants', {
            'fields': ('pourcentage', 'montant_fixe')
        }),
        ('Source et statut', {
            'fields': ('source_financement', 'statut', 'nom_organisme')
        }),
        ('Dates', {
            'fields': ('date_debut', 'date_fin')
        }),
        ('Informations complémentaires', {
            'fields': ('reference_decision', 'conditions', 'observations')
        }),
    )
    
    def est_active_display(self, obj):
        """
        Affiche si la bourse est active.
        
        Returns:
            bool: True si active
        """
        return obj.est_active()
    
    est_active_display.boolean = True
    est_active_display.short_description = 'Active'
    
    # Actions personnalisées
    actions = ['suspendre_bourses', 'reactiver_bourses']
    
    def suspendre_bourses(self, request, queryset):
        """Action admin : Suspendre plusieurs bourses en masse."""
        count = queryset.filter(statut='EN_COURS').update(statut='SUSPENDUE')
        self.message_user(request, f"{count} bourse(s) suspendue(s).")
    
    suspendre_bourses.short_description = "Suspendre les bourses sélectionnées"
    
    def reactiver_bourses(self, request, queryset):
        """Action admin : Réactiver plusieurs bourses en masse."""
        count = queryset.filter(statut='SUSPENDUE').update(statut='EN_COURS')
        self.message_user(request, f"{count} bourse(s) réactivée(s).")
    
    reactiver_bourses.short_description = "Réactiver les bourses sélectionnées"

# ADMIN : FACTURES
@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les factures.
    
    Permet de gérer les factures de scolarité.
    """
    list_display = [
        'numero_facture',
        'inscription',
        'montant_net',
        'montant_paye',
        'solde',
        'statut',
        'taux_paiement_display',
        'date_echeance',
        'en_retard_display',
    ]
    list_filter = ['statut', 'date_emission', 'date_echeance']
    search_fields = [
        'numero_facture',
        'inscription__etudiant__user__first_name',
        'inscription__etudiant__user__last_name',
        'inscription__etudiant__matricule'
    ]
    ordering = ['-date_emission']
    date_hierarchy = 'date_emission'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('inscription', 'numero_facture')
        }),
        ('Montants', {
            'fields': ('montant_brut', 'montant_reduction', 'montant_net', 'montant_paye', 'solde')
        }),
        ('Dates', {
            'fields': ('date_emission', 'date_echeance')
        }),
        ('Statut', {
            'fields': ('statut', 'observations')
        }),
    )
    
    readonly_fields = ['numero_facture', 'date_emission', 'solde']
    
    def taux_paiement_display(self, obj):
        """
        Affiche le taux de paiement.
        
        Returns:
            str: Taux formaté (ex: "85.5%")
        """
        return f"{obj.calculer_taux_paiement()}%"
    
    taux_paiement_display.short_description = 'Taux de paiement'
    
    def en_retard_display(self, obj):
        """
        Affiche si la facture est en retard.
        
        Returns:
            bool: True si en retard
        """
        return obj.est_en_retard()
    
    en_retard_display.boolean = True
    en_retard_display.short_description = 'En retard'
