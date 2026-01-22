from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.students.models import Etudiant

# MODÈLE : CATÉGORIE DE LIVRE
class CategoriesLivre(BaseModel):
    """
    Représente une catégorie de livre dans la bibliothèque.
    
    Exemples : Sciences, Littérature, Histoire, Informatique, etc.
    Permet de classer les livres pour faciliter la recherche.
    """
    nom = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nom de la catégorie (ex: Sciences, Littérature)"
    )
    description = models.TextField(
        blank=True,
        help_text="Description détaillée de la catégorie"
    )
    
    class Meta:
        db_table = 'categories_livre'
        verbose_name = 'Catégorie de livre'
        verbose_name_plural = 'Catégories de livres'
        ordering = ['nom']
    
    def __str__(self):
        return self.nom

# MODÈLE : LIVRE
class Livre(BaseModel):
    """
    Représente un livre dans le catalogue de la bibliothèque.
    
    Contient toutes les informations bibliographiques :
    - Identification : ISBN, titre, auteur
    - Publication : éditeur, année, édition
    - Disponibilité : nombre d'exemplaires total et disponible
    """
    # Informations bibliographiques
    isbn = models.CharField(
        max_length=13,
        unique=True,
        help_text="Numéro ISBN du livre (10 ou 13 chiffres)"
    )
    titre = models.CharField(
        max_length=255,
        help_text="Titre complet du livre"
    )
    auteur = models.CharField(
        max_length=200,
        help_text="Nom de l'auteur principal"
    )
    editeur = models.CharField(
        max_length=200,
        help_text="Nom de la maison d'édition"
    )
    annee_publication = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(9999)
        ],
        help_text="Année de publication (ex: 2024)"
    )
    edition = models.CharField(
        max_length=50,
        blank=True,
        help_text="Numéro d'édition (ex: 1ère édition, 2e édition révisée)"
    )
    
    # Catégorisation
    categorie = models.ForeignKey(
        CategoriesLivre,
        on_delete=models.PROTECT,
        related_name='livres',
        help_text="Catégorie du livre"
    )
    
    # Description
    resume = models.TextField(
        blank=True,
        help_text="Résumé du contenu du livre"
    )
    
    # Gestion des exemplaires
    nombre_exemplaires_total = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Nombre total d'exemplaires possédés"
    )
    nombre_exemplaires_disponibles = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Nombre d'exemplaires actuellement disponibles"
    )
    
    # Localisation
    emplacement = models.CharField(
        max_length=100,
        blank=True,
        help_text="Localisation physique dans la bibliothèque (ex: Rayon A3, Étagère 5)"
    )
    
    class Meta:
        db_table = 'livres'
        verbose_name = 'Livre'
        verbose_name_plural = 'Livres'
        ordering = ['titre']
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['titre']),
            models.Index(fields=['auteur']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.auteur}"
    
    def est_disponible(self):
        """
        Vérifie si au moins un exemplaire est disponible.
        
        Returns:
            bool: True si disponible, False sinon
        """
        return self.nombre_exemplaires_disponibles > 0

# MODÈLE : EMPRUNT
class Emprunt(BaseModel):
    """
    Représente un emprunt de livre par un étudiant.
    
    Gère le cycle complet :
    1. Création : étudiant emprunte un livre
    2. En cours : livre entre les mains de l'étudiant
    3. Retour : livre rendu (avec ou sans retard)
    4. Annulé : emprunt annulé avant retrait
    """
    
    # Choix de statuts
    class StatutEmprunt(models.TextChoices):
        EN_COURS = 'EN_COURS', 'En cours'
        RETOURNE = 'RETOURNE', 'Retourné'
        EN_RETARD = 'EN_RETARD', 'En retard'
        ANNULE = 'ANNULE', 'Annulé'
    
    # Relations
    livre = models.ForeignKey(
        Livre,
        on_delete=models.PROTECT,
        related_name='emprunts',
        help_text="Livre emprunté"
    )
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.PROTECT,
        related_name='emprunts',
        help_text="Étudiant emprunteur"
    )
    
    # Dates importantes
    date_emprunt = models.DateField(
        auto_now_add=True,
        help_text="Date à laquelle l'emprunt a été effectué"
    )
    date_retour_prevue = models.DateField(
        help_text="Date à laquelle le livre doit être rendu"
    )
    date_retour_effective = models.DateField(
        null=True,
        blank=True,
        help_text="Date à laquelle le livre a réellement été rendu"
    )
    
    # Statut et pénalités
    statut = models.CharField(
        max_length=20,
        choices=StatutEmprunt.choices,
        default=StatutEmprunt.EN_COURS,
        help_text="État actuel de l'emprunt"
    )
    penalite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Montant de la pénalité en cas de retard (en FCFA)"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Observations sur l'emprunt (état du livre, incidents, etc.)"
    )
    
    class Meta:
        db_table = 'emprunts'
        verbose_name = 'Emprunt'
        verbose_name_plural = 'Emprunts'
        ordering = ['-date_emprunt']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_retour_prevue']),
        ]
    
    def __str__(self):
        return f"{self.etudiant} - {self.livre.titre} ({self.get_statut_display()})"
    
    def calculer_jours_retard(self):
        """
        Calcule le nombre de jours de retard.
        
        Returns:
            int: Nombre de jours de retard (0 si pas de retard)
        """
        from django.utils import timezone
        
        # Si déjà retourné, calculer sur la date de retour effective
        if self.date_retour_effective:
            if self.date_retour_effective > self.date_retour_prevue:
                return (self.date_retour_effective - self.date_retour_prevue).days
            return 0
        
        # Sinon, calculer sur la date actuelle
        date_actuelle = timezone.now().date()
        if date_actuelle > self.date_retour_prevue:
            return (date_actuelle - self.date_retour_prevue).days
        return 0
    
    def calculer_penalite(self, tarif_par_jour=100):
        """
        Calcule le montant de la pénalité basée sur le retard.
        
        Args:
            tarif_par_jour (int): Montant de pénalité par jour de retard (défaut: 100 FCFA)
        
        Returns:
            Decimal: Montant de la pénalité
        """
        from decimal import Decimal
        jours_retard = self.calculer_jours_retard()
        return Decimal(jours_retard * tarif_par_jour)
    
    def est_en_retard(self):
        """
        Vérifie si l'emprunt est en retard.
        
        Returns:
            bool: True si en retard, False sinon
        """
        return self.calculer_jours_retard() > 0