"""
Modèles de gestion des emplois du temps
Contient : Batiment, Salle, Creneau, Cours, ConflitSalle
"""

from django.db import models
from django.core.exceptions import ValidationError
from apps.academic.models import Matiere, AnneeAcademique
from apps.students.models import Enseignant, Filiere

# MODÈLE BATIMENT
class Batiment(models.Model):
    # Bâtiment de l'université.
    
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code",
        help_text="Ex: A, B, C, AMPHI"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Bâtiment A, Amphithéâtre"
    )
    
    nombre_etages = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre d'étages"
    )
    
    adresse = models.TextField(
        blank=True,
        verbose_name="Adresse/Localisation"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Le bâtiment est-il en service ?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_batiments'
        verbose_name = 'Bâtiment'
        verbose_name_plural = 'Bâtiments'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def get_nombre_salles(self):
        """Nombre de salles dans le bâtiment."""
        return self.salles.count()

# MODÈLE SALLE
class Salle(models.Model):
    # Salle de cours.
    
    TYPE_CHOICES = [
        ('COURS', 'Salle de cours'),
        ('TD', 'Salle de TD'),
        ('TP', 'Salle de TP/Labo'),
        ('AMPHI', 'Amphithéâtre'),
        ('CONFERENCE', 'Salle de conférence'),
    ]
    
    # RELATION
    batiment = models.ForeignKey(
        Batiment,
        on_delete=models.CASCADE,
        related_name='salles',
        verbose_name="Bâtiment"
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code",
        help_text="Ex: A101, AMPHI-A"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Ex: Salle 101, Amphithéâtre A"
    )
    
    type_salle = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='COURS',
        verbose_name="Type de salle"
    )
    
    capacite = models.PositiveIntegerField(
        verbose_name="Capacité",
        help_text="Nombre de places"
    )
    
    etage = models.PositiveIntegerField(
        default=0,
        verbose_name="Étage",
        help_text="0 = Rez-de-chaussée"
    )
    
    equipements = models.TextField(
        blank=True,
        verbose_name="Équipements",
        help_text="Ex: Projecteur, Ordinateurs, Tableau interactif"
    )
    
    is_disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        help_text="La salle est-elle utilisable ?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_salles'
        verbose_name = 'Salle'
        verbose_name_plural = 'Salles'
        ordering = ['batiment', 'etage', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.nom} ({self.get_type_salle_display()})"
    
    def get_taux_occupation(self, annee_academique):
        """Taux d'occupation de la salle (%)."""
        total_creneaux = Creneau.objects.count()
        if total_creneaux == 0:
            return 0
        
        creneaux_occupes = Cours.objects.filter(
            salle=self,
            annee_academique=annee_academique
        ).values('creneau').distinct().count()
        
        return round((creneaux_occupes / total_creneaux) * 100, 2)

# MODÈLE CRENEAU
class Creneau(models.Model):
    # Créneau horaire.
    
    JOUR_CHOICES = [
        ('LUNDI', 'Lundi'),
        ('MARDI', 'Mardi'),
        ('MERCREDI', 'Mercredi'),
        ('JEUDI', 'Jeudi'),
        ('VENDREDI', 'Vendredi'),
        ('SAMEDI', 'Samedi'),
        ('DIMANCHE', 'Dimanche'),
    ]
    
    jour = models.CharField(
        max_length=10,
        choices=JOUR_CHOICES,
        verbose_name="Jour"
    )
    
    heure_debut = models.TimeField(
        verbose_name="Heure de début"
    )
    
    heure_fin = models.TimeField(
        verbose_name="Heure de fin"
    )
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code",
        help_text="Ex: LUNDI-08H00-10H00"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_creneaux'
        verbose_name = 'Créneau horaire'
        verbose_name_plural = 'Créneaux horaires'
        ordering = ['jour', 'heure_debut']
        unique_together = ['jour', 'heure_debut', 'heure_fin']
    
    def __str__(self):
        return f"{self.get_jour_display()} {self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')}"
    
    def clean(self):
        """Validation : heure_fin > heure_debut."""
        if self.heure_debut and self.heure_fin:
            if self.heure_fin <= self.heure_debut:
                raise ValidationError({
                    'heure_fin': 'L\'heure de fin doit être après l\'heure de début'
                })
    
    def get_duree_minutes(self):
        """Durée du créneau en minutes."""
        from datetime import datetime
        debut = datetime.combine(datetime.today(), self.heure_debut)
        fin = datetime.combine(datetime.today(), self.heure_fin)
        duree = fin - debut
        return int(duree.total_seconds() / 60)

# MODÈLE COURS
class Cours(models.Model):
    # Cours programmé dans l'emploi du temps.
    
    TYPE_CHOICES = [
        ('CM', 'Cours Magistral'),
        ('TD', 'Travaux Dirigés'),
        ('TP', 'Travaux Pratiques'),
    ]
    
    # RELATIONS
    annee_academique = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE,
        related_name='cours',
        verbose_name="Année académique"
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='cours',
        verbose_name="Matière"
    )
    
    enseignant = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cours',
        verbose_name="Enseignant"
    )
    
    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='cours',
        verbose_name="Filière"
    )
    
    salle = models.ForeignKey(
        Salle,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cours',
        verbose_name="Salle"
    )
    
    creneau = models.ForeignKey(
        Creneau,
        on_delete=models.CASCADE,
        related_name='cours',
        verbose_name="Créneau horaire"
    )
    
    # INFORMATIONS
    type_cours = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        verbose_name="Type de cours"
    )
    
    effectif_prevu = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Effectif prévu",
        help_text="Nombre d'étudiants attendus"
    )
    
    semestre = models.PositiveIntegerField(
        choices=[(1, 'Semestre 1'), (2, 'Semestre 2')],
        verbose_name="Semestre"
    )
    
    date_debut = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de début",
        help_text="Date de début effectif du cours"
    )
    
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin",
        help_text="Date de fin effectif du cours"
    )
    
    is_actif = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Le cours est-il programmé ?"
    )
    
    remarques = models.TextField(
        blank=True,
        verbose_name="Remarques"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_cours'
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        ordering = ['annee_academique', 'filiere', 'creneau']
    
    def __str__(self):
        return f"{self.matiere.code} - {self.filiere.code} - {self.creneau}"
    
    def clean(self):
        """Validation des conflits."""
        if not self.pk:  # Nouveau cours uniquement
            # Vérifier conflit salle
            conflit_salle = Cours.objects.filter(
                salle=self.salle,
                creneau=self.creneau,
                annee_academique=self.annee_academique,
                is_actif=True
            ).exclude(pk=self.pk)
            
            if conflit_salle.exists():
                raise ValidationError({
                    'salle': f'Cette salle est déjà occupée à ce créneau par : {conflit_salle.first()}'
                })
            
            # Vérifier conflit enseignant
            if self.enseignant:
                conflit_enseignant = Cours.objects.filter(
                    enseignant=self.enseignant,
                    creneau=self.creneau,
                    annee_academique=self.annee_academique,
                    is_actif=True
                ).exclude(pk=self.pk)
                
                if conflit_enseignant.exists():
                    raise ValidationError({
                        'enseignant': f'Cet enseignant a déjà un cours à ce créneau : {conflit_enseignant.first()}'
                    })
            
            # Vérifier capacité salle
            if self.salle and self.effectif_prevu:
                if self.effectif_prevu > self.salle.capacite:
                    raise ValidationError({
                        'effectif_prevu': f'L\'effectif ({self.effectif_prevu}) dépasse la capacité de la salle ({self.salle.capacite})'
                    })
    
    def save(self, *args, **kwargs):
        """Enregistrer et créer conflit si détecté."""
        self.full_clean()
        super().save(*args, **kwargs)

# MODÈLE CONFLIT SALLE
class ConflitSalle(models.Model):
    # Détection et gestion des conflits de salles.
    
    STATUT_CHOICES = [
        ('DETECTE', 'Détecté'),
        ('EN_COURS', 'En cours de résolution'),
        ('RESOLU', 'Résolu'),
        ('IGNORE', 'Ignoré'),
    ]
    
    TYPE_CHOICES = [
        ('SALLE', 'Conflit de salle'),
        ('ENSEIGNANT', 'Conflit d\'enseignant'),
        ('CAPACITE', 'Capacité dépassée'),
    ]
    
    # RELATIONS
    cours1 = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='conflits_comme_cours1',
        verbose_name="Premier cours"
    )
    
    cours2 = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='conflits_comme_cours2',
        null=True,
        blank=True,
        verbose_name="Deuxième cours"
    )
    
    # INFORMATIONS
    type_conflit = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type de conflit"
    )
    
    description = models.TextField(
        verbose_name="Description du conflit"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='DETECTE',
        verbose_name="Statut"
    )
    
    date_detection = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de détection"
    )
    
    date_resolution = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de résolution"
    )
    
    solution_appliquee = models.TextField(
        blank=True,
        verbose_name="Solution appliquée"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_conflits_salles'
        verbose_name = 'Conflit'
        verbose_name_plural = 'Conflits'
        ordering = ['-date_detection']
    
    def __str__(self):
        return f"{self.get_type_conflit_display()} - {self.get_statut_display()}"
    
    def marquer_resolu(self, solution):
        """Marquer le conflit comme résolu."""
        from django.utils import timezone
        self.statut = 'RESOLU'
        self.date_resolution = timezone.now()
        self.solution_appliquee = solution
        self.save()
    
    @staticmethod
    def detecter_conflits(annee_academique):
        """Détecter tous les conflits pour une année académique."""
        conflits_detectes = []
        
        cours_actifs = Cours.objects.filter(
            annee_academique=annee_academique,
            is_actif=True
        ).select_related('salle', 'enseignant', 'creneau', 'matiere', 'filiere')
        
        for cours in cours_actifs:
            # Conflit de salle
            conflits_salle = cours_actifs.filter(
                salle=cours.salle,
                creneau=cours.creneau
            ).exclude(pk=cours.pk)
            
            for autre_cours in conflits_salle:
                # Vérifier si conflit déjà enregistré
                existe = ConflitSalle.objects.filter(
                    cours1__in=[cours, autre_cours],
                    cours2__in=[cours, autre_cours],
                    type_conflit='SALLE',
                    statut__in=['DETECTE', 'EN_COURS']
                ).exists()
                
                if not existe:
                    conflit = ConflitSalle.objects.create(
                        cours1=cours,
                        cours2=autre_cours,
                        type_conflit='SALLE',
                        description=f"Salle {cours.salle.code} occupée par 2 cours au même créneau"
                    )
                    conflits_detectes.append(conflit)
            
            # Conflit enseignant
            if cours.enseignant:
                conflits_ens = cours_actifs.filter(
                    enseignant=cours.enseignant,
                    creneau=cours.creneau
                ).exclude(pk=cours.pk)
                
                for autre_cours in conflits_ens:
                    existe = ConflitSalle.objects.filter(
                        cours1__in=[cours, autre_cours],
                        cours2__in=[cours, autre_cours],
                        type_conflit='ENSEIGNANT',
                        statut__in=['DETECTE', 'EN_COURS']
                    ).exists()
                    
                    if not existe:
                        conflit = ConflitSalle.objects.create(
                            cours1=cours,
                            cours2=autre_cours,
                            type_conflit='ENSEIGNANT',
                            description=f"Enseignant {cours.enseignant.user.get_full_name()} a 2 cours au même créneau"
                        )
                        conflits_detectes.append(conflit)
            
            # Conflit capacité
            if cours.salle and cours.effectif_prevu:
                if cours.effectif_prevu > cours.salle.capacite:
                    existe = ConflitSalle.objects.filter(
                        cours1=cours,
                        cours2__isnull=True,
                        type_conflit='CAPACITE',
                        statut__in=['DETECTE', 'EN_COURS']
                    ).exists()
                    
                    if not existe:
                        conflit = ConflitSalle.objects.create(
                            cours1=cours,
                            type_conflit='CAPACITE',
                            description=f"Effectif ({cours.effectif_prevu}) > Capacité salle ({cours.salle.capacite})"
                        )
                        conflits_detectes.append(conflit)
        
        return conflits_detectes
