# Modèles de gestion des notes et évaluations
# Contient : TypeEvaluation, Evaluation, Note, Resultat

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Sum, Count
from apps.academic.models import Matiere, AnneeAcademique
from apps.students.models import Etudiant

# MODÈLE TYPE EVALUATION
class TypeEvaluation(models.Model):
    """
    Types d'évaluations possibles.
    Exemples : Devoir, Examen, Rattrapage, TD, TP, Projet
    """

    CODE_CHOICES = [
        ('DEVOIR', 'Devoir'),
        ('EXAMEN', 'Examen'),
        ('RATTRAPAGE', 'Rattrapage'),
        ('TD', 'Travaux Dirigés'),
        ('TP', 'Travaux Pratiques'),
        ('PROJET', 'Projet'),
    ]
    
    code = models.CharField(
        max_length=20,
        choices=CODE_CHOICES,
        unique=True,
        verbose_name="Code"
    )
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom",
        help_text="Ex: Devoir, Examen final"
    )
    
    coefficient_min = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        verbose_name="Coefficient minimum"
    )
    
    coefficient_max = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=3.0,
        verbose_name="Coefficient maximum"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_types'
        verbose_name = 'Type d\'évaluation'
        verbose_name_plural = 'Types d\'évaluations'
        ordering = ['code']
    
    def __str__(self):
        return self.nom

# MODÈLE EVALUATION
class Evaluation(models.Model):
    """
    Une évaluation pour une matière.
    Exemples : Devoir 1, Examen final, TP 3
    """
    
    # RELATIONS
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name="Matière"
    )
    
    type_evaluation = models.ForeignKey(
        TypeEvaluation,
        on_delete=models.PROTECT,
        related_name='evaluations',
        verbose_name="Type d'évaluation"
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name="Année académique"
    )
    
    # INFORMATIONS
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre",
        help_text="Ex: Devoir 1, Examen final"
    )
    
    date = models.DateField(
        verbose_name="Date de l'évaluation"
    )
    
    coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="Coefficient",
        help_text="Coefficient de cette évaluation"
    )
    
    note_totale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name="Note totale",
        help_text="Ex: 20, 100"
    )
    
    duree = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Durée (minutes)",
        help_text="Durée de l'évaluation en minutes"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_evaluations'
        verbose_name = 'Évaluation'
        verbose_name_plural = 'Évaluations'
        ordering = ['-date']
        unique_together = ['matiere', 'titre', 'annee_academique']
    
    def __str__(self):
        return f"{self.matiere.code} - {self.titre} ({self.annee_academique.code})"
    
    def get_moyenne_classe(self):
        # Moyenne de la classe pour cette évaluation.
        moyenne = self.notes.filter(absence=False).aggregate(
            moyenne=Avg('note_obtenue')
        )['moyenne']
        return moyenne or 0
    
    def get_nombre_presents(self):
        # Nombre d'étudiants présents.
        return self.notes.filter(absence=False).count()
    
    def get_nombre_absents(self):
        # Nombre d'étudiants absents.
        return self.notes.filter(absence=True).count()

# MODÈLE NOTE
class Note(models.Model):
    # Note d'un étudiant à une évaluation.
    
    # RELATIONS
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Évaluation"
    )
    
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Étudiant"
    )
    
    # NOTE
    note_obtenue = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Note obtenue",
        help_text="Note de l'étudiant"
    )
    
    note_sur = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name="Note sur",
        help_text="Barème (ex: 20, 100)"
    )
    
    # APPRÉCIATIONS
    appreciations = models.TextField(
        blank=True,
        verbose_name="Appréciations",
        help_text="Commentaires de l'enseignant"
    )
    
    # ABSENCE
    absence = models.BooleanField(
        default=False,
        verbose_name="Absent",
        help_text="L'étudiant était absent ?"
    )
    
    # Métadonnées
    date_saisie = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de saisie"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_notes'
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['-date_saisie']
        unique_together = ['evaluation', 'etudiant']
    
    def __str__(self):
        if self.absence:
            return f"{self.etudiant.matricule} - {self.evaluation.titre} : Absent"
        return f"{self.etudiant.matricule} - {self.evaluation.titre} : {self.note_obtenue}/{self.note_sur}"
    
    def get_note_sur_20(self):
        # Convertir la note sur 20.
        if self.absence or not self.note_obtenue:
            return 0
        return (float(self.note_obtenue) / float(self.note_sur)) * 20
    
    def get_appreciation_auto(self):
        # Génération automatique d'appréciation.
        if self.absence:
            return "Absent"
        
        note_sur_20 = self.get_note_sur_20()
        
        if note_sur_20 >= 18:
            return "Excellent"
        elif note_sur_20 >= 16:
            return "Très bien"
        elif note_sur_20 >= 14:
            return "Bien"
        elif note_sur_20 >= 12:
            return "Assez bien"
        elif note_sur_20 >= 10:
            return "Passable"
        else:
            return "Insuffisant"

# MODÈLE RESULTAT
class Resultat(models.Model):
    # Résultat final d'un étudiant pour une matière.
    
    MENTION_CHOICES = [
        ('PASSABLE', 'Passable'),
        ('AB', 'Assez Bien'),
        ('B', 'Bien'),
        ('TB', 'Très Bien'),
        ('EXCELLENT', 'Excellent'),
    ]
    
    STATUT_CHOICES = [
        ('ADMIS', 'Admis'),
        ('AJOURNE', 'Ajourné'),
        ('RATTRAPAGE', 'Rattrapage'),
    ]
    
    # RELATIONS
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='resultats',
        verbose_name="Étudiant"
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='resultats',
        verbose_name="Matière"
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='resultats',
        verbose_name="Année académique"
    )
    
    # RÉSULTATS
    moyenne_generale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Moyenne générale",
        help_text="Moyenne sur 20"
    )
    
    mention = models.CharField(
        max_length=20,
        choices=MENTION_CHOICES,
        blank=True,
        verbose_name="Mention"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        verbose_name="Statut"
    )
    
    credits_obtenus = models.PositiveIntegerField(
        default=0,
        verbose_name="Crédits obtenus"
    )
    
    rang = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Rang/Classement",
        help_text="Position dans la classe"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_resultats'
        verbose_name = 'Résultat'
        verbose_name_plural = 'Résultats'
        ordering = ['-moyenne_generale']
        unique_together = ['etudiant', 'matiere', 'annee_academique']
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.matiere.code} : {self.moyenne_generale}/20"
    
    def save(self, *args, **kwargs):
        # Calcul automatique de la mention et du statut.
        
        # Calculer la mention
        if self.moyenne_generale >= 18:
            self.mention = 'EXCELLENT'
        elif self.moyenne_generale >= 16:
            self.mention = 'TB'
        elif self.moyenne_generale >= 14:
            self.mention = 'B'
        elif self.moyenne_generale >= 12:
            self.mention = 'AB'
        elif self.moyenne_generale >= 10:
            self.mention = 'PASSABLE'
        else:
            self.mention = ''
        
        # Calculer le statut
        if self.moyenne_generale >= 10:
            self.statut = 'ADMIS'
            self.credits_obtenus = self.matiere.credits
        elif self.moyenne_generale >= 7:
            self.statut = 'RATTRAPAGE'
            self.credits_obtenus = 0
        else:
            self.statut = 'AJOURNE'
            self.credits_obtenus = 0
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def calculer_moyenne(etudiant, matiere, annee_academique):
        # Calculer la moyenne d'un étudiant pour une matière.
        # Récupérer toutes les notes de l'étudiant pour cette matière
        notes = Note.objects.filter(
            etudiant=etudiant,
            evaluation__matiere=matiere,
            evaluation__annee_academique=annee_academique,
            absence=False
        ).select_related('evaluation')
        
        if not notes.exists():
            return 0
        
        # Calculer la moyenne pondérée
        total_points = 0
        total_coefficients = 0
        
        for note in notes:
            note_sur_20 = note.get_note_sur_20()
            coefficient = float(note.evaluation.coefficient)
            total_points += note_sur_20 * coefficient
            total_coefficients += coefficient
        
        if total_coefficients == 0:
            return 0
        
        return round(total_points / total_coefficients, 2)

# MODÈLE SESSION DELIBERATION
class SessionDeliberation(models.Model):
    """
    Session de délibération pour une filière/niveau.
    """
    
    STATUT_CHOICES = [
        ('PREVUE', 'Prévue'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('VALIDEE', 'Validée'),
    ]
    
    # RELATIONS
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='sessions_deliberation',
        verbose_name="Année académique"
    )
    
    filiere = models.ForeignKey(
        'academic.Filiere',
        on_delete=models.CASCADE,
        related_name='sessions_deliberation',
        verbose_name="Filière"
    )
    
    # INFORMATIONS
    niveau = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        verbose_name="Niveau",
        help_text="Ex: 1 (L1), 2 (L2), 3 (L3)"
    )
    
    semestre = models.PositiveIntegerField(
        choices=[(1, 'Semestre 1'), (2, 'Semestre 2')],
        verbose_name="Semestre"
    )
    
    date_deliberation = models.DateTimeField(
        verbose_name="Date et heure de délibération"
    )
    
    lieu = models.CharField(
        max_length=200,
        verbose_name="Lieu",
        help_text="Ex: Salle de conférence A"
    )
    
    president_jury = models.CharField(
        max_length=200,
        verbose_name="Président du jury",
        help_text="Nom du président"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PREVUE',
        verbose_name="Statut"
    )
    
    proces_verbal = models.TextField(
        blank=True,
        verbose_name="Procès-verbal",
        help_text="Compte-rendu de la délibération"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_sessions_deliberation'
        verbose_name = 'Session de délibération'
        verbose_name_plural = 'Sessions de délibération'
        ordering = ['-date_deliberation']
        unique_together = ['annee_academique', 'filiere', 'niveau', 'semestre']
    
    def __str__(self):
        return f"{self.filiere.code} - Niveau {self.niveau} - S{self.semestre} ({self.annee_academique.code})"
    
    def get_nombre_etudiants(self):
        """Nombre d'étudiants concernés."""
        return self.decisions.count()
    
    def get_taux_reussite(self):
        """Taux de réussite (%)."""
        total = self.decisions.count()
        if total == 0:
            return 0
        admis = self.decisions.filter(decision='ADMIS').count()
        return round((admis / total) * 100, 2)

# MODÈLE MEMBRE JURY
class MembreJury(models.Model):
    """
    Membre du jury de délibération.
    """
    
    ROLE_CHOICES = [
        ('PRESIDENT', 'Président'),
        ('MEMBRE', 'Membre'),
        ('SECRETAIRE', 'Secrétaire'),
    ]
    
    # RELATIONS
    session = models.ForeignKey(
        SessionDeliberation,
        on_delete=models.CASCADE,
        related_name='membres_jury',
        verbose_name="Session de délibération"
    )
    
    enseignant = models.ForeignKey(
        'students.Enseignant',
        on_delete=models.CASCADE,
        related_name='participations_jury',
        verbose_name="Enseignant"
    )
    
    # INFORMATIONS
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="Rôle"
    )
    
    present = models.BooleanField(
        default=True,
        verbose_name="Présent",
        help_text="L'enseignant était présent à la délibération ?"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_membres_jury'
        verbose_name = 'Membre du jury'
        verbose_name_plural = 'Membres du jury'
        ordering = ['role', 'enseignant']
        unique_together = ['session', 'enseignant']
    
    def __str__(self):
        return f"{self.enseignant.user.get_full_name()} - {self.get_role_display()}"

# MODÈLE DECISION JURY
class DecisionJury(models.Model):
    """
    Décision du jury pour un étudiant.
    """
    
    DECISION_CHOICES = [
        ('ADMIS', 'Admis'),
        ('ADMIS_RESERVE', 'Admis avec réserve'),
        ('AJOURNE', 'Ajourné'),
        ('REDOUBLEMENT', 'Redoublement'),
        ('EXCLUSION', 'Exclusion'),
    ]
    
    MENTION_CHOICES = [
        ('PASSABLE', 'Passable'),
        ('AB', 'Assez Bien'),
        ('B', 'Bien'),
        ('TB', 'Très Bien'),
        ('EXCELLENT', 'Excellent'),
    ]
    
    # RELATIONS
    session = models.ForeignKey(
        SessionDeliberation,
        on_delete=models.CASCADE,
        related_name='decisions',
        verbose_name="Session de délibération"
    )
    
    etudiant = models.ForeignKey(
        'students.Etudiant',
        on_delete=models.CASCADE,
        related_name='decisions_jury',
        verbose_name="Étudiant"
    )
    
    # RÉSULTATS
    moyenne_generale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Moyenne générale",
        help_text="Moyenne sur 20"
    )
    
    total_credits_obtenus = models.PositiveIntegerField(
        verbose_name="Total crédits obtenus"
    )
    
    total_credits_requis = models.PositiveIntegerField(
        verbose_name="Total crédits requis",
        help_text="Nombre de crédits nécessaires"
    )
    
    # DÉCISION
    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        verbose_name="Décision du jury"
    )
    
    mention = models.CharField(
        max_length=20,
        choices=MENTION_CHOICES,
        blank=True,
        verbose_name="Mention"
    )
    
    rang_classe = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Rang dans la classe"
    )
    
    observations = models.TextField(
        blank=True,
        verbose_name="Observations",
        help_text="Commentaires du jury"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_decisions_jury'
        verbose_name = 'Décision du jury'
        verbose_name_plural = 'Décisions du jury'
        ordering = ['-moyenne_generale']
        unique_together = ['session', 'etudiant']
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.get_decision_display()} ({self.moyenne_generale}/20)"
    
    def save(self, *args, **kwargs):
        """Calcul automatique de la mention."""
        
        # Calculer la mention si admis
        if self.decision in ['ADMIS', 'ADMIS_RESERVE']:
            if self.moyenne_generale >= 18:
                self.mention = 'EXCELLENT'
            elif self.moyenne_generale >= 16:
                self.mention = 'TB'
            elif self.moyenne_generale >= 14:
                self.mention = 'B'
            elif self.moyenne_generale >= 12:
                self.mention = 'AB'
            elif self.moyenne_generale >= 10:
                self.mention = 'PASSABLE'
            else:
                self.mention = ''
        else:
            self.mention = ''
        
        super().save(*args, **kwargs)
    
    def get_taux_credits(self):
        """Pourcentage de crédits obtenus."""
        if self.total_credits_requis == 0:
            return 0
        return round((self.total_credits_obtenus / self.total_credits_requis) * 100, 2)
