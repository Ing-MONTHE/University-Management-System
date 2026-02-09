from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Q, Count
from datetime import datetime, time

from apps.academic.models import Matiere, AnneeAcademique
from apps.students.models import Enseignant, Filiere

# MODÈLE BATIMENT
class Batiment(models.Model):
    """Bâtiment de l'université."""
    
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code",
        db_index=True
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom"
    )
    
    nombre_etages = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre d'étages"
    )
    
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_batiments'
        verbose_name = 'Bâtiment'
        verbose_name_plural = 'Bâtiments'
        ordering = ['code']
        indexes = [
            models.Index(fields=['is_active', 'code'], name='sched_bat_active_code_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    @property
    def nombre_salles(self):
        return self.salles.count()
    
    @property
    def salles_disponibles_count(self):
        return self.salles.filter(is_disponible=True).count()


# MODÈLE SALLE
class Salle(models.Model):
    """Salle de cours."""
    
    TYPE_CHOICES = [
        ('COURS', 'Salle de cours'),
        ('TD', 'Salle de TD'),
        ('TP', 'Salle de TP/Labo'),
        ('AMPHI', 'Amphithéâtre'),
        ('CONFERENCE', 'Salle de conférence'),
    ]
    
    batiment = models.ForeignKey(
        Batiment,
        on_delete=models.CASCADE,
        related_name='salles',
        verbose_name="Bâtiment",
        db_index=True
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        db_index=True
    )
    
    nom = models.CharField(max_length=200, verbose_name="Nom")
    
    type_salle = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='COURS',
        verbose_name="Type",
        db_index=True
    )
    
    capacite = models.PositiveIntegerField(verbose_name="Capacité")
    
    etage = models.PositiveIntegerField(default=0, verbose_name="Étage")
    
    equipements = models.TextField(blank=True, verbose_name="Équipements")
    
    is_disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_salles'
        verbose_name = 'Salle'
        verbose_name_plural = 'Salles'
        ordering = ['batiment', 'etage', 'code']
        indexes = [
            models.Index(fields=['batiment', 'code'], name='sched_sal_bat_code_idx'),
            models.Index(fields=['type_salle', 'is_disponible'], name='sched_sal_type_dispo_idx'),
            models.Index(fields=['capacite'], name='sched_sal_cap_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    @property
    def nom_complet(self):
        return f"{self.batiment.code} - {self.nom}"
    
    @property
    def est_disponible(self):
        return self.is_disponible
    
    def get_taux_occupation(self, annee_academique):
        from .models import Cours, Creneau
        total_creneaux = Creneau.objects.count()
        if total_creneaux == 0:
            return 0
        occupes = Cours.objects.filter(
            salle=self,
            annee_academique=annee_academique
        ).values('creneau').distinct().count()
        return round((occupes / total_creneaux) * 100, 2)


# MODÈLE CRENEAU
class Creneau(models.Model):
    """Créneau horaire."""
    
    JOUR_CHOICES = [
        ('LUNDI', 'Lundi'),
        ('MARDI', 'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI', 'Samedi'),
    ]
    
    jour = models.CharField(
        max_length=10,
        choices=JOUR_CHOICES,
        verbose_name="Jour",
        db_index=True
    )
    
    heure_debut = models.TimeField(
        verbose_name="Heure début",
        db_index=True
    )
    
    heure_fin = models.TimeField(verbose_name="Heure fin")
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code",
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_creneaux'
        verbose_name = 'Créneau'
        verbose_name_plural = 'Créneaux'
        ordering = ['jour', 'heure_debut']
        unique_together = ['jour', 'heure_debut', 'heure_fin']
        indexes = [
            models.Index(fields=['jour', 'heure_debut'], name='sched_cren_jour_debut_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_jour_display()} {self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')}"
    
    @property
    def duree_minutes(self):
        debut = datetime.combine(datetime.today(), self.heure_debut)
        fin = datetime.combine(datetime.today(), self.heure_fin)
        return int((fin - debut).total_seconds() / 60)
    
    def clean(self):
        if self.heure_debut and self.heure_fin:
            if self.heure_fin <= self.heure_debut:
                raise ValidationError({'heure_fin': 'Heure fin > heure début'})


# MODÈLE COURS
class Cours(models.Model):
    """Cours programmé."""
    
    TYPE_CHOICES = [
        ('CM', 'Cours Magistral'),
        ('TD', 'Travaux Dirigés'),
        ('TP', 'Travaux Pratiques'),
    ]
    
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='cours',
        db_index=True
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='cours',
        db_index=True
    )
    
    enseignant = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cours',
        db_index=True
    )
    
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='cours',
        db_index=True
    )
    
    salle = models.ForeignKey(
        Salle,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cours',
        db_index=True
    )
    
    creneau = models.ForeignKey(
        Creneau,
        on_delete=models.CASCADE,
        related_name='cours',
        db_index=True
    )
    
    type_cours = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        verbose_name="Type",
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_cours'
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        ordering = ['creneau__jour', 'creneau__heure_debut']
        indexes = [
            models.Index(fields=['matiere', 'annee_academique'], name='sched_cours_mat_annee_idx'),
            models.Index(fields=['enseignant', 'creneau'], name='sched_cours_ens_cren_idx'),
            models.Index(fields=['salle', 'creneau'], name='sched_cours_sal_cren_idx'),
            models.Index(fields=['filiere', 'annee_academique'], name='sched_cours_fil_annee_idx'),
        ]
    
    def __str__(self):
        return f"{self.matiere.code} - {self.filiere.code} - {self.creneau}"
    
    @property
    def nom_complet(self):
        return f"{self.matiere.nom} ({self.get_type_cours_display()})"
    
    @property
    def jour_nom(self):
        return self.creneau.get_jour_display()
    
    @property
    def horaire(self):
        return f"{self.creneau.heure_debut.strftime('%H:%M')}-{self.creneau.heure_fin.strftime('%H:%M')}"


# MODÈLE CONFLIT SALLE
class ConflitSalle(models.Model):
    """Détection conflits salles."""
    
    salle = models.ForeignKey(Salle, on_delete=models.CASCADE, db_index=True)
    cours1 = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='conflits_cours1', db_index=True)
    cours2 = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='conflits_cours2')
    
    date_detection = models.DateTimeField(auto_now_add=True, db_index=True)
    resolu = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        db_table = 'schedule_conflits'
        verbose_name = 'Conflit salle'
        verbose_name_plural = 'Conflits salles'
        ordering = ['-date_detection']
        indexes = [
            models.Index(fields=['resolu', '-date_detection'], name='sched_conf_res_date_idx'),
        ]
    
    def __str__(self):
        return f"Conflit {self.salle.code} - {self.cours1.creneau}"
    
    def resoudre(self):
        self.resolu = True
        self.save(update_fields=['resolu'])
    
    @classmethod
    def get_actifs(cls):
        return cls.objects.filter(resolu=False)
    