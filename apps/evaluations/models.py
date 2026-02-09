from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Sum, Q, F, Max, Min
from django.utils import timezone
from decimal import Decimal

from apps.academic.models import Matiere, AnneeAcademique
from apps.students.models import Etudiant, Enseignant


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE TYPE EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

class TypeEvaluation(models.Model):
    """
    Types d'évaluations possibles.
    
    Exemples : Devoir, Examen, Rattrapage, TD, TP, Projet
    
    Optimisations :
    - Index sur code (unique)
    - Properties pour coefficient moyen
    - Validators sur coefficients
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
        verbose_name="Code",
        db_index=True  # Index unique automatique + db_index pour clarté
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
        verbose_name="Coefficient minimum",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    coefficient_max = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=3.0,
        verbose_name="Coefficient maximum",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'evaluations_types'
        verbose_name = 'Type d\'évaluation'
        verbose_name_plural = 'Types d\'évaluations'
        ordering = ['code']
    
    def __str__(self):
        return self.nom
    
    def __repr__(self):
        return f"<TypeEvaluation {self.code} coef={self.coefficient_min}-{self.coefficient_max}>"
    
    @property
    def coefficient_moyen(self):
        """Coefficient moyen (moyenne entre min et max)."""
        return (self.coefficient_min + self.coefficient_max) / 2


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

class Evaluation(models.Model):
    """
    Une évaluation pour une matière.
    
    Exemples : Devoir 1, Examen final, TP 3
    
    Optimisations :
    - Index sur matiere, type_evaluation, annee_academique, date
    - Index composite (matiere, annee_academique, type_evaluation)
    - Validators sur note_totale et coefficient
    - Properties pour statistiques (moyenne, présents, absents)
    - Méthodes de calcul
    """
    
    # RELATIONS
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name="Matière",
        db_index=True
    )
    
    type_evaluation = models.ForeignKey(
        TypeEvaluation,
        on_delete=models.PROTECT,
        related_name='evaluations',
        verbose_name="Type d'évaluation",
        db_index=True
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name="Année académique",
        db_index=True
    )
    
    # INFORMATIONS
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre",
        help_text="Ex: Devoir 1, Examen final",
        db_index=True  # Index pour recherches
    )
    
    date_evaluation = models.DateField(
        verbose_name="Date de l'évaluation",
        db_index=True  # Index pour tri et filtrage temporel
    )
    
    coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="Coefficient",
        help_text="Coefficient de cette évaluation",
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('10.00'))]
    )
    
    note_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name="Note maximale",
        help_text="Ex: 20, 100",
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))]
    )
    
    duree_minutes = models.PositiveIntegerField(
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
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'evaluations_evaluations'
        verbose_name = 'Évaluation'
        verbose_name_plural = 'Évaluations'
        ordering = ['-date_evaluation']
        unique_together = ['matiere', 'titre', 'annee_academique']
        indexes = [
            models.Index(fields=['matiere', 'annee_academique', 'type_evaluation'], 
                        name='eval_eval_mat_annee_type_idx'),
            models.Index(fields=['annee_academique', '-date_evaluation'], 
                        name='eval_eval_annee_date_idx'),
            models.Index(fields=['type_evaluation', '-date_evaluation'], 
                        name='eval_eval_type_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.matiere.code} - {self.titre} ({self.annee_academique.code})"
    
    def __repr__(self):
        return f"<Evaluation {self.titre} mat={self.matiere.code} coef={self.coefficient}>"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def nombre_notes(self):
        """Nombre total de notes saisies."""
        return self.notes.count()
    
    @property
    def nombre_presents(self):
        """Nombre d'étudiants présents."""
        return self.notes.filter(absence=False).count()
    
    @property
    def nombre_absents(self):
        """Nombre d'étudiants absents."""
        return self.notes.filter(absence=True).count()
    
    @property
    def moyenne_classe(self):
        """Moyenne de la classe pour cette évaluation."""
        result = self.notes.filter(
            absence=False,
            note_obtenue__isnull=False
        ).aggregate(moyenne=Avg('note_obtenue'))
        
        return round(result['moyenne'], 2) if result['moyenne'] else 0
    
    @property
    def est_passee(self):
        """Vérifie si l'évaluation est passée."""
        from datetime import date
        return self.date_evaluation < date.today()
    
    @property
    def taux_presence_pourcent(self):
        """Taux de présence en pourcentage."""
        total = self.notes.count()
        if total == 0:
            return 0
        presents = self.nombre_presents
        return round((presents / total) * 100, 2)
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTHODES
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_statistiques(self):
        """
        Calcule les statistiques de l'évaluation.
        
        Returns:
            dict: Statistiques complètes
        """
        notes_presentes = self.notes.filter(
            absence=False,
            note_obtenue__isnull=False
        )
        
        stats = notes_presentes.aggregate(
            moyenne=Avg('note_obtenue'),
            note_min=Min('note_obtenue'),
            note_max=Max('note_obtenue'),
            count=Count('id')
        )
        
        return {
            'moyenne': round(stats['moyenne'], 2) if stats['moyenne'] else 0,
            'note_min': stats['note_min'] or 0,
            'note_max': stats['note_max'] or 0,
            'nombre_copies': stats['count'] or 0,
            'nombre_absents': self.nombre_absents,
            'taux_presence': self.taux_presence_pourcent,
        }
    
    def get_notes_non_saisies(self):
        """Récupère les notes non saisies (NULL ou absents non marqués)."""
        return self.notes.filter(
            Q(note_obtenue__isnull=True) & Q(absence=False)
        )
    
    @classmethod
    def get_par_matiere(cls, matiere, annee_academique=None):
        """Récupère les évaluations d'une matière."""
        qs = cls.objects.filter(matiere=matiere)
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        return qs.select_related('type_evaluation', 'annee_academique')
    
    @classmethod
    def get_par_type(cls, type_evaluation, annee_academique=None):
        """Récupère les évaluations d'un type."""
        qs = cls.objects.filter(type_evaluation=type_evaluation)
        if annee_academique:
            qs = qs.filter(annee_academique=annee_academique)
        return qs.select_related('matiere', 'annee_academique')


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE NOTE
# ═══════════════════════════════════════════════════════════════════════════════

class Note(models.Model):
    """
    Note d'un étudiant à une évaluation.
    
    Optimisations :
    - Index sur evaluation, etudiant, saisie_par
    - Index composite (evaluation, etudiant)
    - Index composite (etudiant, evaluation__matiere) pour bulletin
    - Validators sur notes
    - Properties pour calculs (note sur 20, pourcentage, appréciation)
    - Méthodes de validation
    """
    
    # RELATIONS
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Évaluation",
        db_index=True
    )
    
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Étudiant",
        db_index=True
    )
    
    saisie_par = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_saisies',
        verbose_name="Saisi par",
        db_index=True  # Index pour audit
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
        help_text="L'étudiant était absent ?",
        db_index=True  # Index pour statistiques présence
    )
    
    # VALIDATION
    est_validee = models.BooleanField(
        default=False,
        verbose_name="Note validée",
        help_text="La note a été validée par l'enseignant",
        db_index=True
    )
    
    # Métadonnées
    date_saisie = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de saisie"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'evaluations_notes'
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['-date_saisie']
        unique_together = ['evaluation', 'etudiant']
        indexes = [
            models.Index(fields=['evaluation', 'etudiant'], name='eval_note_eval_etu_idx'),
            models.Index(fields=['etudiant', 'evaluation__matiere'], name='eval_note_etu_mat_idx'),
            models.Index(fields=['absence', 'est_validee'], name='eval_note_abs_val_idx'),
            models.Index(fields=['saisie_par', '-date_saisie'], name='eval_note_saisie_date_idx'),
        ]
    
    def __str__(self):
        if self.absence:
            return f"{self.etudiant.matricule} - {self.evaluation.titre} : Absent"
        note_str = f"{self.note_obtenue}/{self.evaluation.note_max}" if self.note_obtenue else "Non saisi"
        return f"{self.etudiant.matricule} - {self.evaluation.titre} : {note_str}"
    
    def __repr__(self):
        return f"<Note eval={self.evaluation_id} etu={self.etudiant.matricule} note={self.note_obtenue}>"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def note_sur_20(self):
        """Convertir la note sur 20."""
        if self.absence or not self.note_obtenue:
            return 0
        return round((float(self.note_obtenue) / float(self.evaluation.note_max)) * 20, 2)
    
    @property
    def pourcentage(self):
        """Pourcentage de la note."""
        if self.absence or not self.note_obtenue:
            return 0
        return round((float(self.note_obtenue) / float(self.evaluation.note_max)) * 100, 2)
    
    @property
    def appreciation_auto(self):
        """Génération automatique d'appréciation basée sur la note."""
        if self.absence:
            return "Absent"
        
        if not self.note_obtenue:
            return "Non saisi"
        
        note_sur_20 = self.note_sur_20
        
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTHODES
    # ═══════════════════════════════════════════════════════════════════════
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        
        # Vérifier que la note n'excède pas le maximum
        if self.note_obtenue and self.note_obtenue > self.evaluation.note_max:
            raise ValidationError({
                'note_obtenue': f"La note ne peut pas dépasser {self.evaluation.note_max}"
            })
        
        # Si absent, pas de note
        if self.absence and self.note_obtenue:
            raise ValidationError({
                'absence': "Un étudiant absent ne peut pas avoir de note"
            })
    
    def valider(self):
        """Valider la note."""
        self.est_validee = True
        self.save(update_fields=['est_validee', 'updated_at'])
    
    def invalider(self):
        """Invalider la note."""
        self.est_validee = False
        self.save(update_fields=['est_validee', 'updated_at'])
    
    @classmethod
    def get_par_etudiant(cls, etudiant, annee_academique=None):
        """Récupère toutes les notes d'un étudiant."""
        qs = cls.objects.filter(etudiant=etudiant)
        if annee_academique:
            qs = qs.filter(evaluation__annee_academique=annee_academique)
        return qs.select_related('evaluation__matiere', 'evaluation__type_evaluation')
    
    @classmethod
    def get_non_validees(cls):
        """Récupère toutes les notes non validées."""
        return cls.objects.filter(est_validee=False, absence=False)


# ═══════════════════════════════════════════════════════════════════════════════
# FIN PARTIE 1/2 - SUITE DANS PARTIE 2
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 2/2 - MODÈLES EVALUATIONS (suite)
# ═══════════════════════════════════════════════════════════════════════════════

# MODÈLE RESULTAT
class Resultat(models.Model):
    """
    Résultat final d'un étudiant pour une matière.
    
    Optimisations :
    - Index sur etudiant, matiere, annee_academique, statut
    - Index composites pour requêtes fréquentes
    - Properties pour moyenne, admission, mention
    - Méthodes de calcul automatique
    """
    
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
        verbose_name="Étudiant",
        db_index=True
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='resultats',
        verbose_name="Matière",
        db_index=True
    )
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='resultats',
        verbose_name="Année académique",
        db_index=True
    )
    
    # RÉSULTATS
    moyenne = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Moyenne",
        help_text="Moyenne sur 20",
        db_index=True  # Index pour tri et classement
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
        verbose_name="Statut",
        db_index=True  # Index pour filtrage
    )
    
    credits_obtenus = models.PositiveIntegerField(
        default=0,
        verbose_name="Crédits obtenus"
    )
    
    observations = models.TextField(
        blank=True,
        verbose_name="Observations"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_resultats'
        verbose_name = 'Résultat'
        verbose_name_plural = 'Résultats'
        ordering = ['-moyenne']
        unique_together = ['etudiant', 'matiere', 'annee_academique']
        indexes = [
            models.Index(fields=['etudiant', 'annee_academique'], name='eval_res_etu_annee_idx'),
            models.Index(fields=['matiere', 'statut'], name='eval_res_mat_stat_idx'),
            models.Index(fields=['annee_academique', '-moyenne'], name='eval_res_annee_moy_idx'),
        ]
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.matiere.code} : {self.moyenne}/20"
    
    def __repr__(self):
        return f"<Resultat etu={self.etudiant.matricule} mat={self.matiere.code} moy={self.moyenne}>"
    
    @property
    def est_admis(self):
        """Vérifie si l'étudiant est admis."""
        return self.statut == 'ADMIS'
    
    @property
    def mention_display(self):
        """Retourne l'affichage de la mention."""
        return self.get_mention_display() if self.mention else ''
    
    def calculer_moyenne(self):
        """
        Calcule la moyenne pondérée à partir des notes.
        """
        notes = self.etudiant.notes.filter(
            evaluation__matiere=self.matiere,
            evaluation__annee_academique=self.annee_academique,
            absence=False,
            note_obtenue__isnull=False
        ).select_related('evaluation')
        
        if not notes.exists():
            return 0
        
        total_points = 0
        total_coefficients = 0
        
        for note in notes:
            note_sur_20 = note.note_sur_20
            coefficient = float(note.evaluation.coefficient)
            total_points += note_sur_20 * coefficient
            total_coefficients += coefficient
        
        if total_coefficients == 0:
            return 0
        
        return round(total_points / total_coefficients, 2)
    
    def determiner_statut(self):
        """Détermine le statut basé sur la moyenne."""
        if self.moyenne >= 10:
            return 'ADMIS'
        elif self.moyenne >= 7:
            return 'RATTRAPAGE'
        else:
            return 'AJOURNE'
    
    def get_mention(self):
        """Détermine la mention basée sur la moyenne."""
        if self.moyenne >= 18:
            return 'EXCELLENT'
        elif self.moyenne >= 16:
            return 'TB'
        elif self.moyenne >= 14:
            return 'B'
        elif self.moyenne >= 12:
            return 'AB'
        elif self.moyenne >= 10:
            return 'PASSABLE'
        return ''
    
    def save(self, *args, **kwargs):
        """Calcul automatique de la mention."""
        if self.statut == 'ADMIS':
            self.mention = self.get_mention()
        else:
            self.mention = ''
        
        super().save(*args, **kwargs)


# MODÈLE SESSION DELIBERATION
class SessionDeliberation(models.Model):
    """
    Session de délibération pour une filière/niveau.
    
    Optimisations :
    - Index sur annee_academique, filiere, date_deliberation, statut
    - Properties pour statistiques
    - Méthodes de calcul
    """
    
    STATUT_CHOICES = [
        ('PREVUE', 'Prévue'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('VALIDEE', 'Validée'),
    ]
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='sessions_deliberation',
        verbose_name="Année académique",
        db_index=True
    )
    
    filiere = models.ForeignKey(
        'academic.Filiere',
        on_delete=models.CASCADE,
        related_name='sessions_deliberation',
        verbose_name="Filière",
        db_index=True
    )
    
    niveau = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        verbose_name="Niveau"
    )
    
    semestre = models.PositiveIntegerField(
        choices=[(1, 'Semestre 1'), (2, 'Semestre 2')],
        verbose_name="Semestre"
    )
    
    date_deliberation = models.DateTimeField(
        verbose_name="Date et heure",
        db_index=True
    )
    
    lieu = models.CharField(
        max_length=200,
        verbose_name="Lieu"
    )
    
    president_jury = models.CharField(
        max_length=200,
        verbose_name="Président du jury"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PREVUE',
        verbose_name="Statut",
        db_index=True
    )
    
    proces_verbal = models.TextField(
        blank=True,
        verbose_name="Procès-verbal"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_sessions_deliberation'
        verbose_name = 'Session de délibération'
        verbose_name_plural = 'Sessions de délibération'
        ordering = ['-date_deliberation']
        unique_together = ['annee_academique', 'filiere', 'niveau', 'semestre']
        indexes = [
            models.Index(fields=['filiere', '-date_deliberation'], name='eval_sess_fil_date_idx'),
            models.Index(fields=['statut', 'date_deliberation'], name='eval_sess_stat_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.filiere.code} - Niveau {self.niveau} - S{self.semestre} ({self.annee_academique.code})"
    
    @property
    def est_cloturee(self):
        """Vérifie si la session est clôturée."""
        return self.statut in ['TERMINEE', 'VALIDEE']
    
    @property
    def nombre_etudiants(self):
        """Nombre d'étudiants concernés."""
        return self.decisions.count()
    
    def get_taux_reussite(self):
        """Taux de réussite (%)."""
        total = self.decisions.count()
        if total == 0:
            return 0
        admis = self.decisions.filter(decision__in=['ADMIS', 'ADMIS_RESERVE']).count()
        return round((admis / total) * 100, 2)


# MODÈLE MEMBRE JURY
class MembreJury(models.Model):
    """
    Membre du jury de délibération.
    
    Optimisations :
    - Index sur session, enseignant, role
    - Unique together (session, enseignant)
    """
    
    ROLE_CHOICES = [
        ('PRESIDENT', 'Président'),
        ('MEMBRE', 'Membre'),
        ('SECRETAIRE', 'Secrétaire'),
    ]
    
    session = models.ForeignKey(
        SessionDeliberation,
        on_delete=models.CASCADE,
        related_name='membres_jury',
        verbose_name="Session",
        db_index=True
    )
    
    enseignant = models.ForeignKey(
        'students.Enseignant',
        on_delete=models.CASCADE,
        related_name='participations_jury',
        verbose_name="Enseignant",
        db_index=True
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="Rôle",
        db_index=True
    )
    
    present = models.BooleanField(
        default=True,
        verbose_name="Présent"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_membres_jury'
        verbose_name = 'Membre du jury'
        verbose_name_plural = 'Membres du jury'
        ordering = ['role', 'enseignant']
        unique_together = ['session', 'enseignant']
    
    def __str__(self):
        return f"{self.enseignant.nom_complet} - {self.get_role_display()}"


# MODÈLE DECISION JURY
class DecisionJury(models.Model):
    """
    Décision du jury pour un étudiant.
    
    Optimisations :
    - Index sur session, etudiant, decision
    - Unique together (session, etudiant)
    - Calcul automatique de la mention
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
    
    session = models.ForeignKey(
        SessionDeliberation,
        on_delete=models.CASCADE,
        related_name='decisions',
        verbose_name="Session",
        db_index=True
    )
    
    etudiant = models.ForeignKey(
        'students.Etudiant',
        on_delete=models.CASCADE,
        related_name='decisions_jury',
        verbose_name="Étudiant",
        db_index=True
    )
    
    moyenne_generale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Moyenne générale"
    )
    
    total_credits_obtenus = models.PositiveIntegerField(
        verbose_name="Crédits obtenus"
    )
    
    total_credits_requis = models.PositiveIntegerField(
        verbose_name="Crédits requis"
    )
    
    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        verbose_name="Décision",
        db_index=True
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
        verbose_name="Rang"
    )
    
    observations = models.TextField(
        blank=True,
        verbose_name="Observations"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluations_decisions_jury'
        verbose_name = 'Décision du jury'
        verbose_name_plural = 'Décisions du jury'
        ordering = ['-moyenne_generale']
        unique_together = ['session', 'etudiant']
        indexes = [
            models.Index(fields=['session', 'decision'], name='eval_dec_sess_dec_idx'),
            models.Index(fields=['decision', '-moyenne_generale'], name='eval_dec_dec_moy_idx'),
        ]
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.get_decision_display()} ({self.moyenne_generale}/20)"
    
    @property
    def taux_credits_pourcent(self):
        """Pourcentage de crédits obtenus."""
        if self.total_credits_requis == 0:
            return 0
        return round((self.total_credits_obtenus / self.total_credits_requis) * 100, 2)
    
    def save(self, *args, **kwargs):
        """Calcul automatique de la mention."""
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
