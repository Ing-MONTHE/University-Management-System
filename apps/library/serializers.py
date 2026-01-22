from rest_framework import serializers
from django.db import models
from .models import CategoriesLivre, Livre, Emprunt
from apps.students.models import Etudiant

# SERIALIZER : CATÉGORIE DE LIVRE
class CategoriesLivreSerializer(serializers.ModelSerializer):
    """
    Serializer pour les catégories de livres.
    
    Convertit les objets CategoriesLivre en JSON et vice-versa.
    Ajoute le nombre de livres dans chaque catégorie.
    """
    # Champ calculé : nombre de livres dans cette catégorie
    nombre_livres = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoriesLivre
        fields = [
            'id',
            'nom',
            'description',
            'nombre_livres',  # Champ ajouté
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_nombre_livres(self, obj):
        """
        Calcule le nombre de livres dans cette catégorie.
        
        Args:
            obj (CategoriesLivre): Instance de la catégorie
        
        Returns:
            int: Nombre de livres
        """
        return obj.livres.count()

# SERIALIZER : LIVRE (LISTE)
class LivreListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des livres (vue simplifiée).
    
    Utilisé pour les listes, affiche les informations essentielles.
    Inclut le nom de la catégorie au lieu de juste l'ID.
    """
    # Afficher le nom de la catégorie au lieu de l'ID
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    
    # Champ calculé : disponibilité
    disponible = serializers.SerializerMethodField()
    
    class Meta:
        model = Livre
        fields = [
            'id',
            'isbn',
            'titre',
            'auteur',
            'editeur',
            'annee_publication',
            'categorie',
            'categorie_nom',  # Nom lisible de la catégorie
            'nombre_exemplaires_total',
            'nombre_exemplaires_disponibles',
            'disponible',  # Boolean
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_disponible(self, obj):
        """
        Vérifie si le livre est disponible.
        
        Returns:
            bool: True si au moins 1 exemplaire disponible
        """
        return obj.est_disponible()

# SERIALIZER : LIVRE (DÉTAIL)
class LivreDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un livre.
    
    Utilisé pour l'affichage détaillé d'un livre spécifique.
    Inclut toutes les informations + statistiques d'emprunts.
    """
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    disponible = serializers.SerializerMethodField()
    nombre_emprunts_total = serializers.SerializerMethodField()
    nombre_emprunts_en_cours = serializers.SerializerMethodField()
    
    class Meta:
        model = Livre
        fields = [
            'id',
            'isbn',
            'titre',
            'auteur',
            'editeur',
            'annee_publication',
            'edition',
            'categorie',
            'categorie_nom',
            'resume',
            'nombre_exemplaires_total',
            'nombre_exemplaires_disponibles',
            'emplacement',
            'disponible',
            'nombre_emprunts_total',      # Stats
            'nombre_emprunts_en_cours',   # Stats
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_disponible(self, obj):
        return obj.est_disponible()
    
    def get_nombre_emprunts_total(self, obj):
        """Nombre total d'emprunts de ce livre (historique)."""
        return obj.emprunts.count()
    
    def get_nombre_emprunts_en_cours(self, obj):
        """Nombre d'emprunts actuellement en cours."""
        return obj.emprunts.filter(statut='EN_COURS').count()

# SERIALIZER : ÉTUDIANT (POUR EMPRUNT)
class EtudiantSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour afficher les infos étudiant dans un emprunt.
    """
    nom_complet = serializers.SerializerMethodField()
    
    class Meta:
        model = Etudiant
        fields = ['id', 'matricule', 'nom_complet']
        read_only_fields = ['id', 'matricule']
    
    def get_nom_complet(self, obj):
        """Retourne le nom complet de l'étudiant."""
        return f"{obj.user.first_name} {obj.user.last_name}"

# SERIALIZER : EMPRUNT (LISTE)
class EmpruntListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des emprunts (vue simplifiée).
    
    Affiche les informations de base de l'emprunt avec les noms
    lisibles du livre et de l'étudiant.
    """
    livre_titre = serializers.CharField(source='livre.titre', read_only=True)
    etudiant_nom = serializers.SerializerMethodField()
    jours_retard = serializers.SerializerMethodField()
    en_retard = serializers.SerializerMethodField()
    
    class Meta:
        model = Emprunt
        fields = [
            'id',
            'livre',
            'livre_titre',
            'etudiant',
            'etudiant_nom',
            'date_emprunt',
            'date_retour_prevue',
            'date_retour_effective',
            'statut',
            'penalite',
            'jours_retard',
            'en_retard',
            'created_at',
        ]
        read_only_fields = ['id', 'date_emprunt', 'created_at']
    
    def get_etudiant_nom(self, obj):
        """Nom complet de l'étudiant."""
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_jours_retard(self, obj):
        """Nombre de jours de retard."""
        return obj.calculer_jours_retard()
    
    def get_en_retard(self, obj):
        """Boolean : est en retard."""
        return obj.est_en_retard()

# SERIALIZER : EMPRUNT (DÉTAIL)
class EmpruntDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un emprunt.
    
    Inclut toutes les informations du livre et de l'étudiant.
    """
    livre = LivreListSerializer(read_only=True)
    etudiant = EtudiantSimpleSerializer(read_only=True)
    jours_retard = serializers.SerializerMethodField()
    en_retard = serializers.SerializerMethodField()
    penalite_calculee = serializers.SerializerMethodField()
    
    class Meta:
        model = Emprunt
        fields = [
            'id',
            'livre',
            'etudiant',
            'date_emprunt',
            'date_retour_prevue',
            'date_retour_effective',
            'statut',
            'penalite',
            'penalite_calculee',  # Pénalité recalculée
            'jours_retard',
            'en_retard',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'date_emprunt', 'created_at', 'updated_at']
    
    def get_jours_retard(self, obj):
        return obj.calculer_jours_retard()
    
    def get_en_retard(self, obj):
        return obj.est_en_retard()
    
    def get_penalite_calculee(self, obj):
        """Recalcule la pénalité en temps réel."""
        return float(obj.calculer_penalite())

# SERIALIZER : CRÉATION D'EMPRUNT
class EmpruntCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un nouvel emprunt.
    
    Valide que :
    1. Le livre est disponible
    2. L'étudiant n'a pas trop d'emprunts en cours
    3. L'étudiant n'a pas de pénalités impayées
    """
    
    class Meta:
        model = Emprunt
        fields = [
            'livre',
            'etudiant',
            'date_retour_prevue',
            'notes',
        ]
    
    def validate_livre(self, value):
        """
        Valide que le livre est disponible.
        
        Args:
            value (Livre): Instance du livre
        
        Raises:
            ValidationError: Si aucun exemplaire disponible
        
        Returns:
            Livre: Instance validée
        """
        if not value.est_disponible():
            raise serializers.ValidationError(
                "Ce livre n'est pas disponible actuellement. "
                f"Exemplaires disponibles : {value.nombre_exemplaires_disponibles}"
            )
        return value
    
    def validate_etudiant(self, value):
        """
        Valide que l'étudiant peut emprunter.
        
        Vérifie :
        - Pas plus de 5 emprunts en cours
        - Pas de pénalités impayées
        
        Args:
            value (Etudiant): Instance de l'étudiant
        
        Raises:
            ValidationError: Si l'étudiant ne peut pas emprunter
        
        Returns:
            Etudiant: Instance validée
        """
        # Vérifier le nombre d'emprunts en cours
        emprunts_en_cours = Emprunt.objects.filter(
            etudiant=value,
            statut='EN_COURS'
        ).count()
        
        if emprunts_en_cours >= 5:
            raise serializers.ValidationError(
                f"Limite d'emprunts atteinte. L'étudiant a déjà {emprunts_en_cours} emprunts en cours."
            )
        
        # Vérifier les pénalités impayées
        penalites_totales = Emprunt.objects.filter(
            etudiant=value,
            penalite__gt=0,
            statut__in=['EN_RETARD', 'RETOURNE']
        ).aggregate(total=models.Sum('penalite'))['total'] or 0
        
        if penalites_totales > 0:
            raise serializers.ValidationError(
                f"L'étudiant a des pénalités impayées : {penalites_totales} FCFA"
            )
        
        return value
    
    def validate_date_retour_prevue(self, value):
        """
        Valide que la date de retour est dans le futur.
        
        Args:
            value (date): Date de retour prévue
        
        Raises:
            ValidationError: Si la date est dans le passé
        
        Returns:
            date: Date validée
        """
        from django.utils import timezone
        
        if value <= timezone.now().date():
            raise serializers.ValidationError(
                "La date de retour prévue doit être dans le futur."
            )
        
        return value
    
    def create(self, validated_data):
        """
        Crée un nouvel emprunt et met à jour la disponibilité du livre.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            Emprunt: Instance créée
        """
        livre = validated_data['livre']
        
        # Décrémenter le nombre d'exemplaires disponibles
        livre.nombre_exemplaires_disponibles -= 1
        livre.save()
        
        # Créer l'emprunt
        emprunt = Emprunt.objects.create(**validated_data)
        
        return emprunt


# =========================================
# SERIALIZER : RETOUR D'EMPRUNT
# =========================================
class EmpruntRetourSerializer(serializers.Serializer):
    """
    Serializer pour traiter le retour d'un livre.
    
    Gère :
    1. Calcul automatique de la pénalité si retard
    2. Mise à jour du statut
    3. Incrémentation des exemplaires disponibles
    """
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes sur l'état du livre au retour"
    )
    
    def update(self, instance, validated_data):
        """
        Traite le retour du livre.
        
        Args:
            instance (Emprunt): Instance de l'emprunt
            validated_data (dict): Données du retour
        
        Returns:
            Emprunt: Instance mise à jour
        """
        from django.utils import timezone
        
        # Vérifier que l'emprunt n'est pas déjà retourné
        if instance.statut == 'RETOURNE':
            raise serializers.ValidationError("Ce livre a déjà été retourné.")
        
        # Mettre à jour la date de retour effective
        instance.date_retour_effective = timezone.now().date()
        
        # Calculer et assigner la pénalité si retard
        if instance.est_en_retard():
            instance.penalite = instance.calculer_penalite()
            instance.statut = 'RETOURNE'  # Retourné en retard
        else:
            instance.statut = 'RETOURNE'
        
        # Ajouter les notes si fournies
        if validated_data.get('notes'):
            instance.notes = validated_data['notes']
        
        instance.save()
        
        # Incrémenter le nombre d'exemplaires disponibles
        livre = instance.livre
        livre.nombre_exemplaires_disponibles += 1
        livre.save()
        
        return instance