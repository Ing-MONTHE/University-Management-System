from django.db import models
from apps.core.models import BaseModel
from apps.students.models import Etudiant
from apps.schedule.models import Cours

# MODÈLE : FEUILLE DE PRÉSENCE
class FeuillePresence(BaseModel):
    """
    Représente une feuille de présence pour un cours donné.
    
    Une feuille de présence est créée pour chaque cours dispensé.
    Elle contient la liste des étudiants présents/absents.
    L'enseignant peut marquer les présences pendant ou après le cours.
    
    Relations :
    - Liée à un cours spécifique (date, heure, matière, enseignant)
    - Contient plusieurs enregistrements de présence (1 par étudiant)
    """
    
    # Choix de statuts
    class StatutFeuille(models.TextChoices):
        """
        Statuts possibles d'une feuille de présence.
        
        - OUVERTE : Feuille en cours de remplissage
        - FERMEE : Feuille validée, plus de modifications possibles
        - ANNULEE : Cours annulé, feuille non valide
        """
        OUVERTE = 'OUVERTE', 'Ouverte'
        FERMEE = 'FERMEE', 'Fermée'
        ANNULEE = 'ANNULEE', 'Annulée'
    
    # Relation avec le cours
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='feuilles_presence',
        help_text="Cours concerné par cette feuille de présence"
    )
    
    # Date et heure du cours
    date_cours = models.DateField(
        help_text="Date à laquelle le cours a eu lieu"
    )
    heure_debut = models.TimeField(
        help_text="Heure de début du cours"
    )
    heure_fin = models.TimeField(
        help_text="Heure de fin du cours"
    )
    
    # Statut et métadonnées
    statut = models.CharField(
        max_length=20,
        choices=StatutFeuille.choices,
        default=StatutFeuille.OUVERTE,
        help_text="État actuel de la feuille de présence"
    )
    
    # Statistiques calculées
    nombre_presents = models.PositiveIntegerField(
        default=0,
        help_text="Nombre d'étudiants présents"
    )
    nombre_absents = models.PositiveIntegerField(
        default=0,
        help_text="Nombre d'étudiants absents"
    )
    nombre_retards = models.PositiveIntegerField(
        default=0,
        help_text="Nombre d'étudiants en retard"
    )
    
    # Notes de l'enseignant
    observations = models.TextField(
        blank=True,
        help_text="Observations de l'enseignant sur le déroulement du cours"
    )
    
    class Meta:
        db_table = 'feuilles_presence'
        verbose_name = 'Feuille de présence'
        verbose_name_plural = 'Feuilles de présence'
        ordering = ['-date_cours', '-heure_debut']
        # Contrainte : une seule feuille par cours et par date
        unique_together = [['cours', 'date_cours']]
        indexes = [
            models.Index(fields=['date_cours']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"Présence {self.cours.matiere.nom} - {self.date_cours}"
    
    def calculer_taux_presence(self):
        """
        Calcule le taux de présence du cours.
        
        Formule : (nombre_presents / total_etudiants) * 100
        
        Returns:
            float: Taux de présence en pourcentage (0-100)
        """
        total = self.nombre_presents + self.nombre_absents + self.nombre_retards
        if total == 0:
            return 0.0
        return round((self.nombre_presents / total) * 100, 2)
    
    def fermer_feuille(self):
        """
        Ferme la feuille de présence (verrouillage).
        
        Une fois fermée, la feuille ne peut plus être modifiée.
        Recalcule automatiquement les statistiques avant fermeture.
        """
        # Recalculer les statistiques
        self.nombre_presents = self.presences.filter(statut='PRESENT').count()
        self.nombre_absents = self.presences.filter(statut='ABSENT').count()
        self.nombre_retards = self.presences.filter(statut='RETARD').count()
        
        # Changer le statut
        self.statut = self.StatutFeuille.FERMEE
        self.save()

# MODÈLE : PRÉSENCE ÉTUDIANT
class Presence(BaseModel):
    """
    Enregistre la présence/absence d'un étudiant à un cours spécifique.
    
    Pour chaque cours, un enregistrement de présence est créé par étudiant.
    L'enseignant marque l'étudiant comme PRESENT, ABSENT ou en RETARD.
    
    Relations :
    - Liée à une feuille de présence
    - Liée à un étudiant
    """
    
    # Choix de statuts de présence
    class StatutPresence(models.TextChoices):
        """
        Statuts possibles de présence d'un étudiant.
        
        - PRESENT : Étudiant présent et à l'heure
        - ABSENT : Étudiant absent (justifié ou non)
        - RETARD : Étudiant arrivé en retard
        """
        PRESENT = 'PRESENT', 'Présent'
        ABSENT = 'ABSENT', 'Absent'
        RETARD = 'RETARD', 'En retard'
    
    # Relations
    feuille_presence = models.ForeignKey(
        FeuillePresence,
        on_delete=models.CASCADE,
        related_name='presences',
        help_text="Feuille de présence concernée"
    )
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='presences',
        help_text="Étudiant concerné"
    )
    
    # Statut de présence
    statut = models.CharField(
        max_length=20,
        choices=StatutPresence.choices,
        default=StatutPresence.ABSENT,
        help_text="Statut de présence de l'étudiant"
    )
    
    # Heure d'arrivée (pour les retards)
    heure_arrivee = models.TimeField(
        null=True,
        blank=True,
        help_text="Heure d'arrivée de l'étudiant (si en retard)"
    )
    
    # Justification pour les absences
    absence_justifiee = models.BooleanField(
        default=False,
        help_text="True si l'absence est justifiée"
    )
    
    # Notes
    remarque = models.TextField(
        blank=True,
        help_text="Remarques de l'enseignant sur la présence/absence"
    )
    
    class Meta:
        db_table = 'presences'
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'
        ordering = ['etudiant__user__last_name']
        # Contrainte : un seul enregistrement par étudiant et par feuille
        unique_together = [['feuille_presence', 'etudiant']]
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['absence_justifiee']),
        ]
    
    def __str__(self):
        return f"{self.etudiant} - {self.get_statut_display()} - {self.feuille_presence.date_cours}"
    
    def calculer_minutes_retard(self):
        """
        Calcule le nombre de minutes de retard de l'étudiant.
        
        Returns:
            int: Nombre de minutes de retard (0 si pas de retard)
        """
        if self.statut != 'RETARD' or not self.heure_arrivee:
            return 0
        
        from datetime import datetime
        
        # Convertir les heures en datetime pour calculer la différence
        debut = datetime.combine(datetime.today(), self.feuille_presence.heure_debut)
        arrivee = datetime.combine(datetime.today(), self.heure_arrivee)
        
        # Calculer la différence en minutes
        difference = (arrivee - debut).total_seconds() / 60
        
        return max(0, int(difference))

# MODÈLE : JUSTIFICATIF D'ABSENCE
class JustificatifAbsence(BaseModel):
    """
    Représente un justificatif d'absence uploadé par un étudiant.
    
    Les étudiants peuvent uploader des documents (certificats médicaux,
    convocations, etc.) pour justifier leurs absences.
    L'administration valide ou rejette le justificatif.
    
    Workflow :
    1. Étudiant upload le justificatif (statut EN_ATTENTE)
    2. Administration examine le document
    3. Validation (VALIDE) ou rejet (REJETE)
    4. Si validé, les absences liées deviennent justifiées
    """
    
    # Choix de types de justificatifs
    class TypeJustificatif(models.TextChoices):
        """
        Types de justificatifs acceptés.
        
        - MEDICAL : Certificat médical
        - ADMINISTRATIF : Document administratif (convocation, etc.)
        - FAMILIAL : Événement familial (décès, mariage, etc.)
        - AUTRE : Autre type de justificatif
        """
        MEDICAL = 'MEDICAL', 'Certificat médical'
        ADMINISTRATIF = 'ADMINISTRATIF', 'Document administratif'
        FAMILIAL = 'FAMILIAL', 'Événement familial'
        AUTRE = 'AUTRE', 'Autre'
    
    # Choix de statuts de validation
    class StatutValidation(models.TextChoices):
        """
        Statuts de validation du justificatif.
        
        - EN_ATTENTE : En attente de validation
        - VALIDE : Justificatif accepté
        - REJETE : Justificatif refusé
        """
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        VALIDE = 'VALIDE', 'Validé'
        REJETE = 'REJETE', 'Rejeté'
    
    # Relations
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='justificatifs',
        help_text="Étudiant qui a soumis le justificatif"
    )
    
    # Période couverte
    date_debut = models.DateField(
        help_text="Date de début de la période d'absence"
    )
    date_fin = models.DateField(
        help_text="Date de fin de la période d'absence"
    )
    
    # Type et statut
    type_justificatif = models.CharField(
        max_length=20,
        choices=TypeJustificatif.choices,
        help_text="Type de justificatif"
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutValidation.choices,
        default=StatutValidation.EN_ATTENTE,
        help_text="Statut de validation"
    )
    
    # Document uploadé
    document = models.FileField(
        upload_to='justificatifs/%Y/%m/',
        help_text="Document justificatif (PDF, image, etc.)"
    )
    
    # Métadonnées
    motif = models.TextField(
        help_text="Motif de l'absence expliqué par l'étudiant"
    )
    commentaire_validation = models.TextField(
        blank=True,
        help_text="Commentaire de l'administrateur lors de la validation/rejet"
    )
    
    # Dates de traitement
    date_soumission = models.DateTimeField(
        auto_now_add=True,
        help_text="Date et heure de soumission du justificatif"
    )
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de validation/rejet"
    )
    
    class Meta:
        db_table = 'justificatifs_absence'
        verbose_name = 'Justificatif d\'absence'
        verbose_name_plural = 'Justificatifs d\'absence'
        ordering = ['-date_soumission']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_debut', 'date_fin']),
        ]
    
    def __str__(self):
        return f"Justificatif {self.etudiant} - {self.date_debut} au {self.date_fin}"
    
    def valider(self, commentaire=''):
        """
        Valide le justificatif et marque les absences comme justifiées.
        
        Args:
            commentaire (str): Commentaire de validation (optionnel)
        """
        from django.utils import timezone
        
        # Mettre à jour le statut
        self.statut = self.StatutValidation.VALIDE
        self.commentaire_validation = commentaire
        self.date_traitement = timezone.now()
        self.save()
        
        # Marquer les absences de la période comme justifiées
        Presence.objects.filter(
            etudiant=self.etudiant,
            statut='ABSENT',
            feuille_presence__date_cours__gte=self.date_debut,
            feuille_presence__date_cours__lte=self.date_fin
        ).update(absence_justifiee=True)
    
    def rejeter(self, commentaire=''):
        """
        Rejette le justificatif.
        
        Args:
            commentaire (str): Raison du rejet
        """
        from django.utils import timezone
        
        self.statut = self.StatutValidation.REJETE
        self.commentaire_validation = commentaire
        self.date_traitement = timezone.now()
        self.save()
    
    def calculer_duree(self):
        """
        Calcule la durée couverte par le justificatif en jours.
        
        Returns:
            int: Nombre de jours
        """
        return (self.date_fin - self.date_debut).days + 1
