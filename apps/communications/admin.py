from django.contrib import admin
from .models import Annonce, Notification, Message, PreferenceNotification

# ADMIN : ANNONCES
@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les annonces.
    
    Permet de gérer les annonces et actualités.
    """
    list_display = [
        'titre',
        'type_annonce',
        'auteur',
        'est_prioritaire',
        'statut',
        'date_publication',
        'date_expiration',
        'est_expiree_display',
    ]
    list_filter = ['type_annonce', 'statut', 'est_prioritaire', 'date_publication']
    search_fields = ['titre', 'contenu', 'auteur__username']
    ordering = ['-date_publication', '-created_at']
    date_hierarchy = 'date_publication'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('auteur', 'titre', 'contenu', 'piece_jointe')
        }),
        ('Type et priorité', {
            'fields': ('type_annonce', 'est_prioritaire')
        }),
        ('Publication', {
            'fields': ('statut', 'date_publication', 'date_expiration')
        }),
    )
    
    readonly_fields = ['date_publication']
    
    def est_expiree_display(self, obj):
        """
        Affiche si l'annonce est expirée.
        
        Returns:
            bool: True si expirée
        """
        return obj.est_expiree()
    
    est_expiree_display.boolean = True
    est_expiree_display.short_description = 'Expirée'
    
    # Actions personnalisées
    actions = ['publier_annonces', 'archiver_annonces']
    
    def publier_annonces(self, request, queryset):
        """Action admin : Publier plusieurs annonces en masse."""
        count = 0
        for annonce in queryset.filter(statut='BROUILLON'):
            annonce.publier()
            count += 1
        
        self.message_user(request, f"{count} annonce(s) publiée(s).")
    
    publier_annonces.short_description = "Publier les annonces sélectionnées"
    
    def archiver_annonces(self, request, queryset):
        """Action admin : Archiver plusieurs annonces en masse."""
        count = queryset.filter(statut='PUBLIEE').update(statut='ARCHIVEE')
        self.message_user(request, f"{count} annonce(s) archivée(s).")
    
    archiver_annonces.short_description = "Archiver les annonces sélectionnées"

# ADMIN : NOTIFICATIONS
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les notifications.
    
    Permet de gérer les notifications envoyées aux utilisateurs.
    """
    list_display = [
        'titre',
        'destinataire',
        'type_notification',
        'canal',
        'est_lue',
        'envoyee',
        'created_at',
    ]
    list_filter = ['type_notification', 'canal', 'est_lue', 'envoyee', 'created_at']
    search_fields = ['titre', 'message', 'destinataire__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('destinataire',)
        }),
        ('Contenu', {
            'fields': ('titre', 'message', 'lien')
        }),
        ('Type et canal', {
            'fields': ('type_notification', 'canal')
        }),
        ('Statut', {
            'fields': ('est_lue', 'date_lecture', 'envoyee', 'date_envoi')
        }),
    )
    
    readonly_fields = ['date_lecture', 'date_envoi']
    
    # Actions personnalisées
    actions = ['marquer_comme_lues', 'marquer_comme_envoyees']
    
    def marquer_comme_lues(self, request, queryset):
        """Action admin : Marquer comme lues."""
        count = 0
        for notif in queryset.filter(est_lue=False):
            notif.marquer_comme_lue()
            count += 1
        
        self.message_user(request, f"{count} notification(s) marquée(s) comme lue(s).")
    
    marquer_comme_lues.short_description = "Marquer comme lues"
    
    def marquer_comme_envoyees(self, request, queryset):
        """Action admin : Marquer comme envoyées."""
        count = 0
        for notif in queryset.filter(envoyee=False):
            notif.marquer_comme_envoyee()
            count += 1
        
        self.message_user(request, f"{count} notification(s) marquée(s) comme envoyée(s).")
    
    marquer_comme_envoyees.short_description = "Marquer comme envoyées"

# ADMIN : MESSAGES
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les messages.
    
    Permet de gérer la messagerie interne.
    """
    list_display = [
        'sujet',
        'expediteur',
        'destinataire',
        'est_lu',
        'est_archive',
        'est_reponse_display',
        'created_at',
    ]
    list_filter = ['est_lu', 'est_archive', 'created_at']
    search_fields = [
        'sujet',
        'corps',
        'expediteur__username',
        'destinataire__username'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Participants', {
            'fields': ('expediteur', 'destinataire')
        }),
        ('Contenu', {
            'fields': ('sujet', 'corps', 'piece_jointe')
        }),
        ('Fil de discussion', {
            'fields': ('message_parent',)
        }),
        ('Statut', {
            'fields': ('est_lu', 'date_lecture', 'est_archive')
        }),
    )
    
    readonly_fields = ['date_lecture']
    
    def est_reponse_display(self, obj):
        """
        Affiche si c'est une réponse.
        
        Returns:
            bool: True si c'est une réponse
        """
        return obj.est_reponse()
    
    est_reponse_display.boolean = True
    est_reponse_display.short_description = 'Réponse'
    
    # Actions personnalisées
    actions = ['marquer_comme_lus', 'archiver_messages']
    
    def marquer_comme_lus(self, request, queryset):
        """Action admin : Marquer comme lus."""
        count = 0
        for msg in queryset.filter(est_lu=False):
            msg.marquer_comme_lu()
            count += 1
        
        self.message_user(request, f"{count} message(s) marqué(s) comme lu(s).")
    
    marquer_comme_lus.short_description = "Marquer comme lus"
    
    def archiver_messages(self, request, queryset):
        """Action admin : Archiver les messages."""
        count = 0
        for msg in queryset.filter(est_archive=False):
            msg.archiver()
            count += 1
        
        self.message_user(request, f"{count} message(s) archivé(s).")
    
    archiver_messages.short_description = "Archiver les messages"

# ADMIN : PRÉFÉRENCES NOTIFICATION
@admin.register(PreferenceNotification)
class PreferenceNotificationAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les préférences de notification.
    
    Permet de gérer les préférences des utilisateurs.
    """
    list_display = [
        'utilisateur',
        'activer_email',
        'activer_sms',
        'activer_push',
        'frequence_digest',
    ]
    list_filter = ['activer_email', 'activer_sms', 'activer_push', 'frequence_digest']
    search_fields = ['utilisateur__username', 'utilisateur__email']
    ordering = ['utilisateur__username']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('utilisateur',)
        }),
        ('Préférences par type d\'événement', {
            'fields': (
                'notif_notes',
                'notif_absences',
                'notif_paiements',
                'notif_bibliotheque',
                'notif_emploi_temps',
                'notif_annonces',
                'notif_messages',
            )
        }),
        ('Préférences par canal', {
            'fields': ('activer_email', 'activer_sms', 'activer_push')
        }),
        ('Paramètres avancés', {
            'fields': ('frequence_digest',)
        }),
    )
    
    readonly_fields = ['utilisateur']
