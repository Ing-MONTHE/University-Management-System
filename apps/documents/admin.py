from django.contrib import admin
from .models import Document, TemplateDocument

# ADMIN : DOCUMENTS
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les documents.
    
    Permet de gérer les documents administratifs.
    """
    list_display = [
        'numero_document',
        'type_document',
        'etudiant',
        'statut',
        'date_generation',
        'genere_par',
        'date_delivrance',
        'delivre_par',
    ]
    list_filter = ['type_document', 'statut', 'date_generation']
    search_fields = [
        'numero_document',
        'etudiant__matricule',
        'etudiant__user__first_name',
        'etudiant__user__last_name',
    ]
    ordering = ['-date_generation', '-created_at']
    date_hierarchy = 'date_generation'
    
    fieldsets = (
        ('Étudiant', {
            'fields': ('etudiant',)
        }),
        ('Type de document', {
            'fields': ('type_document', 'numero_document')
        }),
        ('Relations', {
            'fields': ('inscription', 'resultat', 'paiement')
        }),
        ('Fichier', {
            'fields': ('fichier',)
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Génération', {
            'fields': ('genere_par', 'date_generation')
        }),
        ('Délivrance', {
            'fields': ('delivre_par', 'date_delivrance')
        }),
        ('Sécurité', {
            'fields': ('qr_code',)
        }),
        ('Informations complémentaires', {
            'fields': ('motif_demande', 'observations')
        }),
    )
    
    readonly_fields = ['numero_document', 'date_generation', 'date_delivrance', 'qr_code']
    
    # Actions personnalisées
    actions = ['generer_qr_codes', 'annuler_documents']
    
    def generer_qr_codes(self, request, queryset):
        """Action admin : Générer les QR codes."""
        count = 0
        for document in queryset:
            if not document.qr_code:
                document.generer_qr_code()
                count += 1
        
        self.message_user(request, f"{count} QR code(s) généré(s).")
    
    generer_qr_codes.short_description = "Générer les QR codes"
    
    def annuler_documents(self, request, queryset):
        """Action admin : Annuler plusieurs documents."""
        count = 0
        for document in queryset.exclude(statut='DELIVRE'):
            document.annuler()
            count += 1
        
        self.message_user(request, f"{count} document(s) annulé(s).")
    
    annuler_documents.short_description = "Annuler les documents sélectionnés"

# ADMIN : TEMPLATES
@admin.register(TemplateDocument)
class TemplateDocumentAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les templates.
    
    Permet de gérer les templates de documents.
    """
    list_display = [
        'type_document',
        'nom',
        'actif',
        'created_at',
    ]
    list_filter = ['type_document', 'actif']
    search_fields = ['nom', 'description']
    ordering = ['type_document']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('type_document', 'nom', 'description')
        }),
        ('Contenu', {
            'fields': ('contenu_html', 'styles_css')
        }),
        ('En-tête et pied de page', {
            'fields': ('entete_html', 'pied_page_html')
        }),
        ('Personnalisation', {
            'fields': ('logo', 'watermark_texte')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )
    
    # Actions personnalisées
    actions = ['activer_templates', 'desactiver_templates']
    
    def activer_templates(self, request, queryset):
        """Action admin : Activer plusieurs templates."""
        count = queryset.update(actif=True)
        self.message_user(request, f"{count} template(s) activé(s).")
    
    activer_templates.short_description = "Activer les templates sélectionnés"
    
    def desactiver_templates(self, request, queryset):
        """Action admin : Désactiver plusieurs templates."""
        count = queryset.update(actif=False)
        self.message_user(request, f"{count} template(s) désactivé(s).")
    
    desactiver_templates.short_description = "Désactiver les templates sélectionnés"
