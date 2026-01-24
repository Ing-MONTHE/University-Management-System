from rest_framework import serializers
from .models import FraisScolarite, Paiement, Bourse, Facture
from apps.students.models import Inscription

# SERIALIZER : FRAIS DE SCOLARITÉ (LISTE)
class FraisScolariteListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des frais de scolarité (vue simplifiée).
    
    Affiche les informations essentielles pour les listes.
    Inclut les noms lisibles de la filière et de l'année académique.
    """
    filiere_nom = serializers.CharField(source='filiere.nom', read_only=True)
    annee_academique_nom = serializers.CharField(source='annee_academique.nom', read_only=True)
    montant_tranche = serializers.SerializerMethodField()
    
    class Meta:
        model = FraisScolarite
        fields = [
            'id',
            'filiere',
            'filiere_nom',
            'annee_academique',
            'annee_academique_nom',
            'niveau',
            'montant_total',
            'nombre_tranches',
            'montant_tranche',
            'date_limite_paiement',
            'actif',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_montant_tranche(self, obj):
        """
        Calcule le montant par tranche.
        
        Returns:
            float: Montant de chaque tranche
        """
        return float(obj.montant_par_tranche())

# SERIALIZER : FRAIS DE SCOLARITÉ (DÉTAIL)
class FraisScolariteDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets des frais de scolarité.
    
    Inclut toutes les informations + statistiques d'utilisation.
    """
    filiere_nom = serializers.CharField(source='filiere.nom', read_only=True)
    annee_academique_nom = serializers.CharField(source='annee_academique.nom', read_only=True)
    montant_tranche = serializers.SerializerMethodField()
    nombre_etudiants_inscrits = serializers.SerializerMethodField()
    
    class Meta:
        model = FraisScolarite
        fields = [
            'id',
            'filiere',
            'filiere_nom',
            'annee_academique',
            'annee_academique_nom',
            'niveau',
            'montant_total',
            'nombre_tranches',
            'montant_tranche',
            'date_limite_paiement',
            'actif',
            'description',
            'nombre_etudiants_inscrits',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_montant_tranche(self, obj):
        return float(obj.montant_par_tranche())
    
    def get_nombre_etudiants_inscrits(self, obj):
        """
        Compte le nombre d'étudiants inscrits concernés.
        
        Returns:
            int: Nombre d'étudiants
        """
        return Inscription.objects.filter(
            filiere=obj.filiere,
            annee_academique=obj.annee_academique,
            niveau=obj.niveau
        ).count()

# SERIALIZER : CRÉATION FRAIS DE SCOLARITÉ
class FraisScolariteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer/modifier des frais de scolarité.
    
    Valide que :
    1. Le montant est positif
    2. Le nombre de tranches est entre 1 et 12
    3. Pas de doublon (filière + année + niveau)
    """
    
    class Meta:
        model = FraisScolarite
        fields = [
            'filiere',
            'annee_academique',
            'niveau',
            'montant_total',
            'nombre_tranches',
            'date_limite_paiement',
            'actif',
            'description',
        ]
    
    def validate_montant_total(self, value):
        """
        Valide que le montant est positif.
        
        Args:
            value (Decimal): Montant à valider
        
        Raises:
            ValidationError: Si montant négatif ou nul
        
        Returns:
            Decimal: Montant validé
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant total doit être supérieur à 0."
            )
        return value
    
    def validate(self, data):
        """
        Validation globale : vérifier les doublons.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si doublon trouvé
        
        Returns:
            dict: Données validées
        """
        # Vérifier l'unicité lors de la création
        if not self.instance:
            if FraisScolarite.objects.filter(
                filiere=data['filiere'],
                annee_academique=data['annee_academique'],
                niveau=data['niveau']
            ).exists():
                raise serializers.ValidationError(
                    "Des frais de scolarité existent déjà pour cette combinaison "
                    "(filière, année académique, niveau)."
                )
        
        return data

# SERIALIZER : PAIEMENT (LISTE)
class PaiementListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des paiements (vue simplifiée).
    
    Affiche les informations de base avec les noms lisibles.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='inscription.etudiant.matricule', read_only=True)
    filiere_nom = serializers.CharField(source='inscription.filiere.nom', read_only=True)
    valide_par_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Paiement
        fields = [
            'id',
            'inscription',
            'etudiant_nom',
            'etudiant_matricule',
            'filiere_nom',
            'montant',
            'mode_paiement',
            'date_paiement',
            'numero_recu',
            'statut',
            'valide_par',
            'valide_par_nom',
            'date_validation',
            'created_at',
        ]
        read_only_fields = ['id', 'numero_recu', 'created_at']
    
    def get_etudiant_nom(self, obj):
        """Retourne le nom complet de l'étudiant."""
        return f"{obj.inscription.etudiant.user.first_name} {obj.inscription.etudiant.user.last_name}"
    
    def get_valide_par_nom(self, obj):
        """Retourne le nom de la personne qui a validé."""
        if obj.valide_par:
            return f"{obj.valide_par.first_name} {obj.valide_par.last_name}"
        return None

# SERIALIZER : PAIEMENT (DÉTAIL)
class PaiementDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un paiement.
    
    Inclut toutes les informations du paiement et de l'étudiant.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='inscription.etudiant.matricule', read_only=True)
    filiere_nom = serializers.CharField(source='inscription.filiere.nom', read_only=True)
    annee_academique_nom = serializers.CharField(source='inscription.annee_academique.nom', read_only=True)
    valide_par_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Paiement
        fields = [
            'id',
            'inscription',
            'etudiant_nom',
            'etudiant_matricule',
            'filiere_nom',
            'annee_academique_nom',
            'montant',
            'mode_paiement',
            'date_paiement',
            'numero_recu',
            'reference_transaction',
            'statut',
            'valide_par',
            'valide_par_nom',
            'date_validation',
            'observations',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'numero_recu', 'created_at', 'updated_at']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.inscription.etudiant.user.first_name} {obj.inscription.etudiant.user.last_name}"
    
    def get_valide_par_nom(self, obj):
        if obj.valide_par:
            return f"{obj.valide_par.first_name} {obj.valide_par.last_name}"
        return None

# SERIALIZER : CRÉATION PAIEMENT
class PaiementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un nouveau paiement.
    
    Valide que :
    1. Le montant est positif
    2. L'inscription existe et est active
    3. Le montant ne dépasse pas le solde restant
    """
    
    class Meta:
        model = Paiement
        fields = [
            'inscription',
            'montant',
            'mode_paiement',
            'date_paiement',
            'reference_transaction',
            'observations',
        ]
    
    def validate_montant(self, value):
        """
        Valide que le montant est positif.
        
        Args:
            value (Decimal): Montant à valider
        
        Raises:
            ValidationError: Si montant négatif ou nul
        
        Returns:
            Decimal: Montant validé
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant du paiement doit être supérieur à 0."
            )
        return value
    
    def validate_inscription(self, value):
        """
        Valide que l'inscription existe et a une facture.
        
        Args:
            value (Inscription): Inscription à valider
        
        Raises:
            ValidationError: Si pas de facture
        
        Returns:
            Inscription: Inscription validée
        """
        try:
            facture = value.facture
        except Facture.DoesNotExist:
            raise serializers.ValidationError(
                "Aucune facture n'existe pour cette inscription. "
                "Veuillez d'abord générer une facture."
            )
        
        return value
    
    def validate(self, data):
        """
        Validation globale : vérifier que le montant ne dépasse pas le solde.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si montant > solde
        
        Returns:
            dict: Données validées
        """
        inscription = data['inscription']
        montant = data['montant']
        
        # Récupérer la facture
        try:
            facture = inscription.facture
        except Facture.DoesNotExist:
            raise serializers.ValidationError(
                "Aucune facture n'existe pour cette inscription."
            )
        
        # Vérifier que le montant ne dépasse pas le solde
        if montant > facture.solde:
            raise serializers.ValidationError(
                f"Le montant du paiement ({montant} FCFA) dépasse le solde restant "
                f"({facture.solde} FCFA)."
            )
        
        return data
    
    def create(self, validated_data):
        """
        Crée le paiement et met à jour la facture automatiquement.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            Paiement: Instance créée
        """
        # Créer le paiement
        paiement = Paiement.objects.create(**validated_data)
        
        # Mettre à jour la facture
        facture = paiement.inscription.facture
        facture.enregistrer_paiement(paiement.montant)
        
        return paiement

# SERIALIZER : VALIDATION PAIEMENT
class PaiementValidationSerializer(serializers.Serializer):
    """
    Serializer pour valider un paiement.
    
    Format :
    {
        "observations": "Paiement validé après vérification"
    }
    """
    observations = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Observations lors de la validation"
    )

# SERIALIZER : BOURSE (LISTE)
class BourseListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des bourses (vue simplifiée).
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='etudiant.matricule', read_only=True)
    annee_academique_nom = serializers.CharField(source='annee_academique.nom', read_only=True)
    est_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Bourse
        fields = [
            'id',
            'etudiant',
            'etudiant_nom',
            'etudiant_matricule',
            'annee_academique',
            'annee_academique_nom',
            'type_bourse',
            'pourcentage',
            'montant_fixe',
            'source_financement',
            'statut',
            'date_debut',
            'date_fin',
            'est_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_est_active(self, obj):
        """Vérifie si la bourse est active."""
        return obj.est_active()

# SERIALIZER : BOURSE (DÉTAIL)
class BourseDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'une bourse.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='etudiant.matricule', read_only=True)
    annee_academique_nom = serializers.CharField(source='annee_academique.nom', read_only=True)
    est_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Bourse
        fields = [
            'id',
            'etudiant',
            'etudiant_nom',
            'etudiant_matricule',
            'annee_academique',
            'annee_academique_nom',
            'type_bourse',
            'pourcentage',
            'montant_fixe',
            'source_financement',
            'statut',
            'date_debut',
            'date_fin',
            'nom_organisme',
            'reference_decision',
            'conditions',
            'observations',
            'est_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_est_active(self, obj):
        return obj.est_active()

# SERIALIZER : CRÉATION BOURSE
class BourseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une nouvelle bourse.
    
    Valide que :
    1. Si type PARTIELLE → pourcentage requis (0-100)
    2. Si type MONTANT_FIXE → montant_fixe requis
    3. Date fin > date début
    """
    
    class Meta:
        model = Bourse
        fields = [
            'etudiant',
            'annee_academique',
            'type_bourse',
            'pourcentage',
            'montant_fixe',
            'source_financement',
            'date_debut',
            'date_fin',
            'nom_organisme',
            'reference_decision',
            'conditions',
            'observations',
        ]
    
    def validate(self, data):
        """
        Validation globale selon le type de bourse.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si données manquantes ou incohérentes
        
        Returns:
            dict: Données validées
        """
        type_bourse = data.get('type_bourse')
        
        # Si bourse partielle, le pourcentage est requis
        if type_bourse == 'PARTIELLE':
            if not data.get('pourcentage'):
                raise serializers.ValidationError(
                    "Le pourcentage est requis pour une bourse partielle."
                )
            if data['pourcentage'] <= 0 or data['pourcentage'] > 100:
                raise serializers.ValidationError(
                    "Le pourcentage doit être entre 0 et 100."
                )
        
        # Si montant fixe, le montant est requis
        if type_bourse == 'MONTANT_FIXE':
            if not data.get('montant_fixe'):
                raise serializers.ValidationError(
                    "Le montant fixe est requis pour ce type de bourse."
                )
            if data['montant_fixe'] <= 0:
                raise serializers.ValidationError(
                    "Le montant fixe doit être supérieur à 0."
                )
        
        # Vérifier que date_fin > date_debut
        if data['date_fin'] <= data['date_debut']:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        
        return data

# SERIALIZER : FACTURE (LISTE)
class FactureListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des factures (vue simplifiée).
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='inscription.etudiant.matricule', read_only=True)
    filiere_nom = serializers.CharField(source='inscription.filiere.nom', read_only=True)
    taux_paiement = serializers.SerializerMethodField()
    en_retard = serializers.SerializerMethodField()
    
    class Meta:
        model = Facture
        fields = [
            'id',
            'inscription',
            'etudiant_nom',
            'etudiant_matricule',
            'filiere_nom',
            'numero_facture',
            'montant_brut',
            'montant_reduction',
            'montant_net',
            'montant_paye',
            'solde',
            'statut',
            'taux_paiement',
            'date_emission',
            'date_echeance',
            'en_retard',
        ]
        read_only_fields = ['id', 'numero_facture', 'date_emission']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.inscription.etudiant.user.first_name} {obj.inscription.etudiant.user.last_name}"
    
    def get_taux_paiement(self, obj):
        """Calcule le taux de paiement."""
        return obj.calculer_taux_paiement()
    
    def get_en_retard(self, obj):
        """Vérifie si la facture est en retard."""
        return obj.est_en_retard()

# SERIALIZER : FACTURE (DÉTAIL)
class FactureDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'une facture.
    
    Inclut toutes les informations + liste des paiements.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='inscription.etudiant.matricule', read_only=True)
    filiere_nom = serializers.CharField(source='inscription.filiere.nom', read_only=True)
    annee_academique_nom = serializers.CharField(source='inscription.annee_academique.nom', read_only=True)
    taux_paiement = serializers.SerializerMethodField()
    en_retard = serializers.SerializerMethodField()
    paiements = serializers.SerializerMethodField()
    
    class Meta:
        model = Facture
        fields = [
            'id',
            'inscription',
            'etudiant_nom',
            'etudiant_matricule',
            'filiere_nom',
            'annee_academique_nom',
            'numero_facture',
            'montant_brut',
            'montant_reduction',
            'montant_net',
            'montant_paye',
            'solde',
            'statut',
            'taux_paiement',
            'date_emission',
            'date_echeance',
            'en_retard',
            'observations',
            'paiements',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'numero_facture', 'date_emission', 'created_at', 'updated_at']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.inscription.etudiant.user.first_name} {obj.inscription.etudiant.user.last_name}"
    
    def get_taux_paiement(self, obj):
        return obj.calculer_taux_paiement()
    
    def get_en_retard(self, obj):
        return obj.est_en_retard()
    
    def get_paiements(self, obj):
        """
        Retourne la liste des paiements de cette facture.
        
        Returns:
            list: Liste des paiements
        """
        paiements = obj.inscription.paiements.filter(statut='VALIDE')
        return PaiementListSerializer(paiements, many=True).data

# SERIALIZER : GÉNÉRATION FACTURE
class FactureGenerationSerializer(serializers.Serializer):
    """
    Serializer pour générer une facture pour une inscription.
    
    Processus :
    1. Récupère les frais de scolarité
    2. Calcule les réductions (bourses)
    3. Génère la facture avec montant net
    
    Format :
    {
        "inscription_id": 123,
        "date_echeance": "2026-06-30"
    }
    """
    inscription_id = serializers.IntegerField(
        help_text="ID de l'inscription"
    )
    date_echeance = serializers.DateField(
        required=False,
        help_text="Date limite de paiement (optionnel, par défaut : frais.date_limite_paiement)"
    )
    
    def validate_inscription_id(self, value):
        """
        Valide que l'inscription existe.
        
        Args:
            value (int): ID de l'inscription
        
        Raises:
            ValidationError: Si inscription inexistante
        
        Returns:
            int: ID validé
        """
        try:
            inscription = Inscription.objects.get(id=value)
        except Inscription.DoesNotExist:
            raise serializers.ValidationError(
                f"Aucune inscription trouvée avec l'ID {value}."
            )
        
        # Vérifier si une facture existe déjà
        if hasattr(inscription, 'facture'):
            raise serializers.ValidationError(
                "Une facture existe déjà pour cette inscription."
            )
        
        return value
