from django.db import models
from django.db.models import Count, Q
from django.utils import timezone

from apps.core.models import BaseModel
from apps.students.models import Etudiant
from apps.schedule.models import Cours

# MODÈLE FEUILLE PRESENCE
class FeuillePresence(BaseModel):
    """Feuille de présence pour un cours."""
    
    class StatutFeuille(models.TextChoices):
        OUVERTE = 'OUVERTE', 'Ouverte'
        FERMEE = 'FERMEE', 'Fermée'
        ANNULEE = 'ANNULEE', 'Annulée'
    
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='feuilles_presence',
        db_index=True
    )
    
    date_cours = models.DateField(
        verbose_name="Date du cours",
        db_index=True
    )
    
    heure_debut = models.TimeField(verbose_name="Heure début")
    heure_fin = models.TimeField(verbose_name="Heure fin")
    
    statut = models.CharField(
        max_length=10,
        choices=StatutFeuille.choices,
        default=StatutFeuille.OUVERTE,
        verbose_name="Statut",
        db_index=True
    )
    
    observations = models.TextField(blank=True, verbose_name="Observations")
    
    class Meta:
        db_table = 'attendance_feuilles_presence'
        verbose_name = 'Feuille de présence'
        verbose_name_plural = 'Feuilles de présence'
        ordering = ['-date_cours', '-heure_debut']
        indexes = [
            models.Index(fields=['cours', 'date_cours'], name='attend_feuil_cours_date_idx'),
            models.Index(fields=['statut', '-date_cours'], name='attend_feuil_stat_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.cours.matiere.code} - {self.date_cours}"
    
    @property
    def nombre_presents(self):
        return self.presences.filter(statut='PRESENT').count()
    
    @property
    def nombre_absents(self):
        return self.presences.filter(statut='ABSENT').count()
    
    @property
    def nombre_total(self):
        return self.presences.count()
    
    @property
    def taux_presence(self):
        total = self.nombre_total
        if total == 0:
            return 0
        return round((self.nombre_presents / total) * 100, 2)
    
    @property
    def taux_absence(self):
        return 100 - self.taux_presence if self.nombre_total > 0 else 0
    
    def fermer(self):
        """Fermer la feuille de présence."""
        self.statut = self.StatutFeuille.FERMEE
        self.save(update_fields=['statut', 'updated_at'])
    
    def annuler(self):
        """Annuler la feuille de présence."""
        self.statut = self.StatutFeuille.ANNULEE
        self.save(update_fields=['statut', 'updated_at'])
    
    def get_statistiques(self):
        """Statistiques de présence."""
        return {
            'total': self.nombre_total,
            'presents': self.nombre_presents,
            'absents': self.nombre_absents,
            'taux_presence': self.taux_presence,
            'taux_absence': self.taux_absence,
        }


# MODÈLE PRESENCE
class Presence(BaseModel):
    """Enregistrement présence/absence étudiant."""
    
    class StatutPresence(models.TextChoices):
        PRESENT = 'PRESENT', 'Présent'
        ABSENT = 'ABSENT', 'Absent'
        RETARD = 'RETARD', 'Retard'
        ABSENT_JUSTIFIE = 'ABSENT_JUSTIFIE', 'Absent justifié'
    
    feuille = models.ForeignKey(
        FeuillePresence,
        on_delete=models.CASCADE,
        related_name='presences',
        db_index=True
    )
    
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='presences',
        db_index=True
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutPresence.choices,
        default=StatutPresence.PRESENT,
        verbose_name="Statut",
        db_index=True
    )
    
    justificatif = models.FileField(
        upload_to='justificatifs/',
        blank=True,
        null=True,
        verbose_name="Justificatif"
    )
    
    observations = models.TextField(blank=True, verbose_name="Observations")
    
    class Meta:
        db_table = 'attendance_presences'
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'
        ordering = ['feuille', 'etudiant']
        unique_together = ['feuille', 'etudiant']
        indexes = [
            models.Index(fields=['feuille', 'etudiant'], name='attend_pres_feuil_etu_idx'),
            models.Index(fields=['etudiant', 'statut'], name='attend_pres_etu_stat_idx'),
            models.Index(fields=['statut'], name='attend_pres_stat_idx'),
        ]
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.feuille.cours.matiere.code} : {self.get_statut_display()}"
    
    @property
    def est_present(self):
        return self.statut == self.StatutPresence.PRESENT
    
    @property
    def est_absent(self):
        return self.statut in [self.StatutPresence.ABSENT, self.StatutPresence.ABSENT_JUSTIFIE]
    
    @property
    def est_justifie(self):
        return self.statut == self.StatutPresence.ABSENT_JUSTIFIE or bool(self.justificatif)
    
    def marquer_present(self):
        """Marquer comme présent."""
        self.statut = self.StatutPresence.PRESENT
        self.save(update_fields=['statut', 'updated_at'])
    
    def marquer_absent(self):
        """Marquer comme absent."""
        self.statut = self.StatutPresence.ABSENT
        self.save(update_fields=['statut', 'updated_at'])
    
    def marquer_retard(self):
        """Marquer comme en retard."""
        self.statut = self.StatutPresence.RETARD
        self.save(update_fields=['statut', 'updated_at'])
    
    def justifier(self, justificatif=None):
        """Justifier une absence."""
        self.statut = self.StatutPresence.ABSENT_JUSTIFIE
        if justificatif:
            self.justificatif = justificatif
        self.save(update_fields=['statut', 'justificatif', 'updated_at'])
    
    @classmethod
    def get_par_etudiant(cls, etudiant, annee_academique=None):
        """Récupérer les présences d'un étudiant."""
        qs = cls.objects.filter(etudiant=etudiant)
        if annee_academique:
            qs = qs.filter(feuille__cours__annee_academique=annee_academique)
        return qs.select_related('feuille__cours__matiere')
    
    @classmethod
    def get_absents_non_justifies(cls):
        """Récupérer les absences non justifiées."""
        return cls.objects.filter(
            statut=cls.StatutPresence.ABSENT,
            justificatif__isnull=True
        )