# Configuration de l'interface d'administration pour évaluations

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TypeEvaluation,
    Evaluation,
    Note,
    Resultat,
    SessionDeliberation,
    MembreJury,
    DecisionJury
)

# TYPE EVALUATION ADMIN
@admin.register(TypeEvaluation)
class TypeEvaluationAdmin(admin.ModelAdmin):
    """Configuration admin pour Type d'évaluation."""
    
    list_display = ['code', 'nom', 'coefficient_min', 'coefficient_max', 'created_at']
    list_filter = ['code', 'created_at']
    search_fields = ['nom', 'description']
    ordering = ['code']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'nom', 'description')
        }),
        ('Coefficients', {
            'fields': ('coefficient_min', 'coefficient_max')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

# EVALUATION ADMIN
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """Configuration admin pour Évaluation."""
    
    list_display = [
        'titre', 'matiere', 'type_evaluation', 'date',
        'coefficient', 'note_totale', 'get_moyenne_classe',
        'get_nombre_presents', 'get_nombre_absents'
    ]
    list_filter = [
        'type_evaluation', 'annee_academique', 'matiere',
        'date', 'created_at'
    ]
    search_fields = ['titre', 'matiere__nom', 'matiere__code']
    ordering = ['-date']
    
    fieldsets = (
        ('Identification', {
            'fields': ('matiere', 'type_evaluation', 'annee_academique')
        }),
        ('Détails', {
            'fields': ('titre', 'date', 'duree', 'description')
        }),
        ('Notation', {
            'fields': ('coefficient', 'note_totale')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_moyenne_classe(self, obj):
        """Moyenne de la classe."""
        return round(obj.get_moyenne_classe(), 2)
    get_moyenne_classe.short_description = 'Moyenne classe'
    
    def get_nombre_presents(self, obj):
        """Nombre de présents."""
        return obj.get_nombre_presents()
    get_nombre_presents.short_description = 'Présents'
    
    def get_nombre_absents(self, obj):
        """Nombre d'absents."""
        absents = obj.get_nombre_absents()
        if absents > 0:
            return format_html('<span style="color: red;">{}</span>', absents)
        return absents
    get_nombre_absents.short_description = 'Absents'

# NOTE ADMIN
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Configuration admin pour Note."""
    
    list_display = [
        'get_etudiant', 'get_evaluation', 'note_obtenue',
        'note_sur', 'get_note_sur_20', 'get_appreciation',
        'absence', 'date_saisie'
    ]
    list_filter = [
        'evaluation__type_evaluation', 'evaluation__matiere',
        'absence', 'date_saisie'
    ]
    search_fields = [
        'etudiant__matricule', 'etudiant__user__first_name',
        'etudiant__user__last_name', 'evaluation__titre'
    ]
    ordering = ['-date_saisie']
    
    fieldsets = (
        ('Évaluation', {
            'fields': ('evaluation', 'etudiant')
        }),
        ('Note', {
            'fields': ('note_obtenue', 'note_sur', 'absence')
        }),
        ('Appréciations', {
            'fields': ('appreciations',)
        }),
        ('Dates', {
            'fields': ('date_saisie', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_saisie', 'created_at', 'updated_at']
    
    def get_etudiant(self, obj):
        """Afficher l'étudiant."""
        return f"{obj.etudiant.matricule} - {obj.etudiant.user.get_full_name()}"
    get_etudiant.short_description = 'Étudiant'
    
    def get_evaluation(self, obj):
        """Afficher l'évaluation."""
        return f"{obj.evaluation.matiere.code} - {obj.evaluation.titre}"
    get_evaluation.short_description = 'Évaluation'
    
    def get_note_sur_20(self, obj):
        """Note sur 20."""
        note = obj.get_note_sur_20()
        if note >= 10:
            return format_html('<span style="color: green; font-weight: bold;">{}/20</span>', round(note, 2))
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}/20</span>', round(note, 2))
    get_note_sur_20.short_description = 'Note /20'
    
    def get_appreciation(self, obj):
        """Appréciation."""
        appreciation = obj.get_appreciation_auto()
        colors = {
            'Excellent': 'green',
            'Très bien': 'blue',
            'Bien': 'blue',
            'Assez bien': 'orange',
            'Passable': 'orange',
            'Insuffisant': 'red',
            'Absent': 'gray'
        }
        color = colors.get(appreciation, 'black')
        return format_html('<span style="color: {};">{}</span>', color, appreciation)
    get_appreciation.short_description = 'Appréciation'

# RESULTAT ADMIN
@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    """Configuration admin pour Résultat."""
    
    list_display = [
        'get_etudiant', 'matiere', 'annee_academique',
        'get_moyenne_coloree', 'mention', 'statut',
        'credits_obtenus', 'rang'
    ]
    list_filter = [
        'annee_academique', 'matiere', 'statut',
        'mention', 'created_at'
    ]
    search_fields = [
        'etudiant__matricule', 'etudiant__user__first_name',
        'etudiant__user__last_name', 'matiere__nom'
    ]
    ordering = ['-moyenne_generale', 'rang']
    
    fieldsets = (
        ('Étudiant et Matière', {
            'fields': ('etudiant', 'matiere', 'annee_academique')
        }),
        ('Résultats', {
            'fields': ('moyenne_generale', 'credits_obtenus', 'rang')
        }),
        ('Décision', {
            'fields': ('statut', 'mention')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['mention', 'statut', 'credits_obtenus', 'created_at', 'updated_at']
    
    def get_etudiant(self, obj):
        """Afficher l'étudiant."""
        return f"{obj.etudiant.matricule} - {obj.etudiant.user.get_full_name()}"
    get_etudiant.short_description = 'Étudiant'
    
    def get_moyenne_coloree(self, obj):
        """Moyenne colorée."""
        moyenne = obj.moyenne_generale
        if moyenne >= 16:
            color = 'green'
        elif moyenne >= 14:
            color = 'blue'
        elif moyenne >= 12:
            color = 'orange'
        elif moyenne >= 10:
            color = 'darkorange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{}/20</span>',
            color, moyenne
        )
    get_moyenne_coloree.short_description = 'Moyenne'

# SESSION DELIBERATION ADMIN
@admin.register(SessionDeliberation)
class SessionDeliberationAdmin(admin.ModelAdmin):
    """Configuration admin pour Session de délibération."""
    
    list_display = [
        'get_session_titre', 'date_deliberation', 'lieu',
        'president_jury', 'get_statut_coloré', 'get_nombre_etudiants',
        'get_taux_reussite_coloré'
    ]
    list_filter = [
        'annee_academique', 'filiere', 'niveau',
        'semestre', 'statut', 'date_deliberation'
    ]
    search_fields = ['filiere__nom', 'president_jury', 'lieu']
    ordering = ['-date_deliberation']
    
    fieldsets = (
        ('Identification', {
            'fields': ('annee_academique', 'filiere', 'niveau', 'semestre')
        }),
        ('Organisation', {
            'fields': ('date_deliberation', 'lieu', 'president_jury')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Procès-verbal', {
            'fields': ('proces_verbal',),
            'classes': ('collapse',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_session_titre(self, obj):
        """Titre de la session."""
        return f"{obj.filiere.code} - Niveau {obj.niveau} - S{obj.semestre}"
    get_session_titre.short_description = 'Session'
    
    def get_statut_coloré(self, obj):
        """Statut coloré."""
        colors = {
            'PREVUE': 'gray',
            'EN_COURS': 'blue',
            'TERMINEE': 'orange',
            'VALIDEE': 'green'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    get_statut_coloré.short_description = 'Statut'
    
    def get_nombre_etudiants(self, obj):
        """Nombre d'étudiants."""
        return obj.get_nombre_etudiants()
    get_nombre_etudiants.short_description = 'Nb étudiants'
    
    def get_taux_reussite_coloré(self, obj):
        """Taux de réussite coloré."""
        taux = obj.get_taux_reussite()
        if taux >= 75:
            color = 'green'
        elif taux >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} %</span>',
            color, taux
        )
    get_taux_reussite_coloré.short_description = 'Taux réussite'
    
    actions = ['cloturer_session', 'valider_session']
    
    def cloturer_session(self, request, queryset):
        """Action pour clôturer des sessions."""
        count = 0
        for session in queryset:
            if session.statut not in ['TERMINEE', 'VALIDEE']:
                session.statut = 'TERMINEE'
                session.save()
                count += 1
        self.message_user(request, f"{count} session(s) clôturée(s).")
    cloturer_session.short_description = "Clôturer les sessions sélectionnées"
    
    def valider_session(self, request, queryset):
        """Action pour valider des sessions."""
        count = 0
        for session in queryset:
            if session.statut == 'TERMINEE':
                session.statut = 'VALIDEE'
                session.save()
                count += 1
        self.message_user(request, f"{count} session(s) validée(s).")
    valider_session.short_description = "Valider les sessions terminées"

# MEMBRE JURY ADMIN
@admin.register(MembreJury)
class MembreJuryAdmin(admin.ModelAdmin):
    """Configuration admin pour Membre du jury."""
    
    list_display = [
        'get_session', 'get_enseignant', 'role',
        'get_presence'
    ]
    list_filter = ['session', 'role', 'present']
    search_fields = [
        'enseignant__matricule', 'enseignant__user__first_name',
        'enseignant__user__last_name'
    ]
    ordering = ['session', 'role']
    
    fieldsets = (
        ('Session', {
            'fields': ('session',)
        }),
        ('Membre', {
            'fields': ('enseignant', 'role', 'present')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_session(self, obj):
        """Session."""
        return str(obj.session)
    get_session.short_description = 'Session'
    
    def get_enseignant(self, obj):
        """Enseignant."""
        return f"{obj.enseignant.user.get_full_name()} ({obj.enseignant.get_grade_display()})"
    get_enseignant.short_description = 'Enseignant'
    
    def get_presence(self, obj):
        """Présence."""
        if obj.present:
            return format_html('<span style="color: green;">✓ Présent</span>')
        return format_html('<span style="color: red;">✗ Absent</span>')
    get_presence.short_description = 'Présence'

# DECISION JURY ADMIN
@admin.register(DecisionJury)
class DecisionJuryAdmin(admin.ModelAdmin):
    """Configuration admin pour Décision du jury."""
    
    list_display = [
        'rang_classe', 'get_etudiant', 'get_session',
        'get_moyenne_coloree', 'mention', 'get_decision_coloree',
        'get_credits'
    ]
    list_filter = [
        'session', 'decision', 'mention', 'created_at'
    ]
    search_fields = [
        'etudiant__matricule', 'etudiant__user__first_name',
        'etudiant__user__last_name'
    ]
    ordering = ['session', 'rang_classe']
    
    fieldsets = (
        ('Session et Étudiant', {
            'fields': ('session', 'etudiant')
        }),
        ('Résultats', {
            'fields': (
                'moyenne_generale', 'total_credits_obtenus',
                'total_credits_requis', 'rang_classe'
            )
        }),
        ('Décision', {
            'fields': ('decision', 'mention', 'observations')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['mention', 'created_at', 'updated_at']
    
    def get_etudiant(self, obj):
        """Étudiant."""
        return f"{obj.etudiant.matricule} - {obj.etudiant.user.get_full_name()}"
    get_etudiant.short_description = 'Étudiant'
    
    def get_session(self, obj):
        """Session."""
        return str(obj.session)
    get_session.short_description = 'Session'
    
    def get_moyenne_coloree(self, obj):
        """Moyenne colorée."""
        moyenne = obj.moyenne_generale
        if moyenne >= 16:
            color = 'green'
        elif moyenne >= 14:
            color = 'blue'
        elif moyenne >= 12:
            color = 'orange'
        elif moyenne >= 10:
            color = 'darkorange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{}/20</span>',
            color, moyenne
        )
    get_moyenne_coloree.short_description = 'Moyenne'
    
    def get_decision_coloree(self, obj):
        """Décision colorée."""
        colors = {
            'ADMIS': 'green',
            'ADMIS_RESERVE': 'orange',
            'AJOURNE': 'red',
            'REDOUBLEMENT': 'darkred',
            'EXCLUSION': 'black'
        }
        color = colors.get(obj.decision, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_decision_display()
        )
    get_decision_coloree.short_description = 'Décision'
    
    def get_credits(self, obj):
        """Crédits."""
        taux = obj.get_taux_credits()
        if taux >= 75:
            color = 'green'
        elif taux >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '{}/{} <span style="color: {};">({} %)</span>',
            obj.total_credits_obtenus, obj.total_credits_requis, color, taux
        )
    get_credits.short_description = 'Crédits'
