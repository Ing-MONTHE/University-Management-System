# Configuration de l'interface d'administration pour étudiants/enseignants

from django.contrib import admin
from django.utils.html import format_html
from .models import Etudiant, Enseignant, Inscription, Attribution

# ETUDIANT ADMIN
@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    # Configuration admin pour Étudiant.
    
    list_display = [
        'matricule', 'get_nom_complet', 'sexe', 'telephone',
        'get_filiere_actuelle', 'statut', 'created_at'
    ]
    list_filter = ['statut', 'sexe', 'nationalite', 'ville', 'created_at']
    search_fields = [
        'matricule', 'user__first_name', 'user__last_name',
        'telephone', 'email_personnel'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Compte utilisateur', {
            'fields': ('user',)
        }),
        ('Identification', {
            'fields': ('matricule', 'date_naissance', 'lieu_naissance', 'sexe', 'nationalite')
        }),
        ('Contact', {
            'fields': ('telephone', 'email_personnel', 'adresse', 'ville', 'pays')
        }),
        ('Photo', {
            'fields': ('photo',)
        }),
        ('Tuteur/Parent', {
            'fields': ('tuteur_nom', 'tuteur_telephone', 'tuteur_email'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['matricule', 'created_at', 'updated_at']
    
    def get_nom_complet(self, obj):
        # Afficher le nom complet.
        return obj.user.get_full_name()
    get_nom_complet.short_description = 'Nom complet'
    
    def get_filiere_actuelle(self, obj):
        # Afficher la filière actuelle.
        filiere = obj.get_filiere_actuelle()
        if filiere:
            return filiere.nom
        return '-'
    get_filiere_actuelle.short_description = 'Filière actuelle'
    
    def save_model(self, request, obj, form, change):
        # Générer le matricule si nouveau.
        if not change:  # Si c'est une création
            from datetime import datetime
            annee = datetime.now().year
            obj.matricule = Etudiant.generer_matricule(annee)
        super().save_model(request, obj, form, change)

# ENSEIGNANT ADMIN
@admin.register(Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    # Configuration admin pour Enseignant.
    
    list_display = [
        'matricule', 'get_nom_complet', 'grade', 'departement',
        'specialite', 'telephone', 'statut', 'date_embauche'
    ]
    list_filter = ['grade', 'departement', 'statut', 'sexe', 'date_embauche']
    search_fields = [
        'matricule', 'user__first_name', 'user__last_name',
        'specialite', 'telephone', 'email_personnel'
    ]
    ordering = ['-date_embauche']
    
    fieldsets = (
        ('Compte utilisateur', {
            'fields': ('user',)
        }),
        ('Identification', {
            'fields': ('matricule', 'departement', 'specialite', 'grade')
        }),
        ('Informations personnelles', {
            'fields': ('date_naissance', 'sexe', 'date_embauche')
        }),
        ('Contact', {
            'fields': ('telephone', 'email_personnel', 'adresse')
        }),
        ('Documents', {
            'fields': ('photo', 'cv'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['matricule', 'created_at', 'updated_at']
    
    def get_nom_complet(self, obj):
        # Afficher le nom complet.
        return obj.user.get_full_name()
    get_nom_complet.short_description = 'Nom complet'
    
    def save_model(self, request, obj, form, change):
        # Générer le matricule si nouveau.
        if not change:  # Si c'est une création
            from datetime import datetime
            annee = datetime.now().year
            obj.matricule = Enseignant.generer_matricule(annee)
        super().save_model(request, obj, form, change)

# INSCRIPTION ADMIN
@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    # Configuration admin pour Inscription.
    
    list_display = [
        'get_etudiant', 'filiere', 'annee_academique', 'niveau',
        'montant_inscription', 'montant_paye', 'get_reste_a_payer',
        'statut_paiement', 'statut', 'date_inscription'
    ]
    list_filter = [
        'filiere', 'annee_academique', 'niveau',
        'statut_paiement', 'statut', 'date_inscription'
    ]
    search_fields = [
        'etudiant__matricule', 'etudiant__user__first_name',
        'etudiant__user__last_name', 'filiere__nom'
    ]
    ordering = ['-date_inscription']
    
    fieldsets = (
        ('Étudiant et Filière', {
            'fields': ('etudiant', 'filiere', 'annee_academique', 'niveau')
        }),
        ('Paiement', {
            'fields': ('montant_inscription', 'montant_paye', 'statut_paiement')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Dates', {
            'fields': ('date_inscription', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_inscription', 'created_at', 'updated_at', 'statut_paiement']
    
    def get_etudiant(self, obj):
        # Afficher l'étudiant.
        return f"{obj.etudiant.matricule} - {obj.etudiant.user.get_full_name()}"
    get_etudiant.short_description = 'Étudiant'
    
    def get_reste_a_payer(self, obj):
        # Afficher le reste à payer.
        reste = obj.get_reste_a_payer()
        if reste > 0:
            return f"{int(reste)} FCFA"
        return "Soldé ✓"
    get_reste_a_payer.short_description = 'Reste à payer'
    
    actions = ['marquer_solde']
    
    def marquer_solde(self, request, queryset):
        # Action pour marquer comme soldé.
        for inscription in queryset:
            inscription.montant_paye = inscription.montant_inscription
            inscription.save()
        self.message_user(request, f"{queryset.count()} inscription(s) marquée(s) comme soldée(s).")
    marquer_solde.short_description = "Marquer comme soldé"

# ATTRIBUTION ADMIN
@admin.register(Attribution)
class AttributionAdmin(admin.ModelAdmin):
    # Configuration admin pour Attribution.
    
    list_display = [
        'get_enseignant', 'matiere', 'type_enseignement',
        'volume_horaire_assigne', 'annee_academique', 'created_at'
    ]
    list_filter = [
        'type_enseignement', 'annee_academique',
        'enseignant__departement', 'created_at'
    ]
    search_fields = [
        'enseignant__matricule', 'enseignant__user__first_name',
        'enseignant__user__last_name', 'matiere__code', 'matiere__nom'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Attribution', {
            'fields': ('enseignant', 'matiere', 'annee_academique')
        }),
        ('Détails', {
            'fields': ('type_enseignement', 'volume_horaire_assigne')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_enseignant(self, obj):
        # Afficher l'enseignant.
        return f"{obj.enseignant.matricule} - {obj.enseignant.user.get_full_name()}"
    get_enseignant.short_description = 'Enseignant'
