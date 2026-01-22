from django.contrib import admin
from .models import CategoriesLivre, Livre, Emprunt

# ADMIN : CATÉGORIES DE LIVRES
@admin.register(CategoriesLivre)
class CategoriesLivreAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les catégories de livres.
    """
    list_display = ['nom', 'nombre_livres', 'created_at']
    search_fields = ['nom']
    ordering = ['nom']
    
    def nombre_livres(self, obj):
        """Affiche le nombre de livres dans la catégorie."""
        return obj.livres.count()
    nombre_livres.short_description = 'Nombre de livres'

# ADMIN : LIVRES
@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les livres.
    """
    list_display = [
        'titre',
        'auteur',
        'isbn',
        'categorie',
        'nombre_exemplaires_disponibles',
        'nombre_exemplaires_total',
        'est_disponible',
    ]
    list_filter = ['categorie', 'annee_publication']
    search_fields = ['titre', 'auteur', 'isbn']
    ordering = ['titre']
    
    fieldsets = (
        ('Informations bibliographiques', {
            'fields': ('isbn', 'titre', 'auteur', 'editeur', 'annee_publication', 'edition')
        }),
        ('Catégorisation', {
            'fields': ('categorie', 'resume')
        }),
        ('Gestion des exemplaires', {
            'fields': ('nombre_exemplaires_total', 'nombre_exemplaires_disponibles', 'emplacement')
        }),
    )
    
    def est_disponible(self, obj):
        """Affiche si le livre est disponible."""
        return obj.est_disponible()
    est_disponible.boolean = True
    est_disponible.short_description = 'Disponible'

# ADMIN : EMPRUNTS
@admin.register(Emprunt)
class EmpruntAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les emprunts.
    """
    list_display = [
        'livre',
        'etudiant',
        'date_emprunt',
        'date_retour_prevue',
        'statut',
        'jours_retard',
        'penalite',
    ]
    list_filter = ['statut', 'date_emprunt']
    search_fields = ['livre__titre', 'etudiant__user__first_name', 'etudiant__user__last_name']
    ordering = ['-date_emprunt']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('livre', 'etudiant')
        }),
        ('Dates', {
            'fields': ('date_emprunt', 'date_retour_prevue', 'date_retour_effective')
        }),
        ('Statut et pénalités', {
            'fields': ('statut', 'penalite', 'notes')
        }),
    )
    
    readonly_fields = ['date_emprunt']
    
    def jours_retard(self, obj):
        """Affiche le nombre de jours de retard."""
        return obj.calculer_jours_retard()
    jours_retard.short_description = 'Jours de retard'
