from rest_framework import serializers
from django.utils import timezone
from .models import Equipement, Reservation, ReservationEquipement, Maintenance

# SERIALIZER : ÉQUIPEMENT (LISTE)
class EquipementListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des équipements (vue simplifiée).
    
    Affiche les informations essentielles pour les listes.
    """
    salle_nom = serializers.CharField(source='salle.nom', read_only=True, allow_null=True)
    est_disponible = serializers.SerializerMethodField()
    
    class Meta:
        model = Equipement
        fields = [
            'id',
            'nom',
            'reference',
            'categorie',
            'etat',
            'salle',
            'salle_nom',
            'quantite_disponible',
            'quantite_totale',
            'reservable',
            'est_disponible',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_est_disponible(self, obj):
        """
        Vérifie si l'équipement est disponible.
        
        Returns:
            bool: True si disponible
        """
        return obj.est_disponible()

# SERIALIZER : ÉQUIPEMENT (DÉTAIL)
class EquipementDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un équipement.
    
    Inclut toutes les informations + historique des maintenances.
    """
    salle_nom = serializers.CharField(source='salle.nom', read_only=True, allow_null=True)
    batiment_nom = serializers.CharField(source='salle.batiment.nom', read_only=True, allow_null=True)
    est_disponible = serializers.SerializerMethodField()
    nombre_maintenances = serializers.SerializerMethodField()
    
    class Meta:
        model = Equipement
        fields = [
            'id',
            'nom',
            'description',
            'reference',
            'categorie',
            'etat',
            'salle',
            'salle_nom',
            'batiment_nom',
            'quantite_disponible',
            'quantite_totale',
            'date_acquisition',
            'valeur_acquisition',
            'dernier_entretien',
            'prochain_entretien',
            'reservable',
            'est_disponible',
            'nombre_maintenances',
            'observations',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_est_disponible(self, obj):
        return obj.est_disponible()
    
    def get_nombre_maintenances(self, obj):
        """
        Compte le nombre de maintenances de cet équipement.
        
        Returns:
            int: Nombre de maintenances
        """
        return obj.maintenances.count()

# SERIALIZER : CRÉATION ÉQUIPEMENT
class EquipementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer/modifier un équipement.
    
    Valide que :
    1. La référence est unique
    2. quantite_disponible <= quantite_totale
    3. Les quantités sont positives
    """
    
    class Meta:
        model = Equipement
        fields = [
            'nom',
            'description',
            'reference',
            'categorie',
            'salle',
            'quantite_disponible',
            'quantite_totale',
            'date_acquisition',
            'valeur_acquisition',
            'prochain_entretien',
            'reservable',
            'observations',
        ]
    
    def validate(self, data):
        """
        Validation globale.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si données incohérentes
        
        Returns:
            dict: Données validées
        """
        quantite_dispo = data.get('quantite_disponible', 0)
        quantite_totale = data.get('quantite_totale', 1)
        
        # Vérifier que disponible <= total
        if quantite_dispo > quantite_totale:
            raise serializers.ValidationError(
                "La quantité disponible ne peut pas dépasser la quantité totale."
            )
        
        return data

# SERIALIZER : RÉSERVATION ÉQUIPEMENT (NESTED)
class ReservationEquipementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les équipements réservés (utilisé dans les réservations).
    """
    equipement_nom = serializers.CharField(source='equipement.nom', read_only=True)
    equipement_reference = serializers.CharField(source='equipement.reference', read_only=True)
    
    class Meta:
        model = ReservationEquipement
        fields = [
            'id',
            'equipement',
            'equipement_nom',
            'equipement_reference',
            'quantite',
            'retourne',
            'date_retour',
            'etat_retour',
        ]
        read_only_fields = ['id', 'retourne', 'date_retour']

# SERIALIZER : RÉSERVATION (LISTE)
class ReservationListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des réservations (vue simplifiée).
    """
    demandeur_nom = serializers.SerializerMethodField()
    salle_nom = serializers.CharField(source='salle.nom', read_only=True, allow_null=True)
    duree_heures = serializers.SerializerMethodField()
    
    class Meta:
        model = Reservation
        fields = [
            'id',
            'demandeur',
            'demandeur_nom',
            'type_reservation',
            'salle',
            'salle_nom',
            'date_debut',
            'date_fin',
            'duree_heures',
            'motif',
            'statut',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_demandeur_nom(self, obj):
        """Retourne le nom du demandeur."""
        return f"{obj.demandeur.first_name} {obj.demandeur.last_name}"
    
    def get_duree_heures(self, obj):
        """Calcule la durée en heures."""
        return obj.calculer_duree()

# SERIALIZER : RÉSERVATION (DÉTAIL)
class ReservationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'une réservation.
    
    Inclut la liste des équipements réservés.
    """
    demandeur_nom = serializers.SerializerMethodField()
    salle_nom = serializers.CharField(source='salle.nom', read_only=True, allow_null=True)
    valide_par_nom = serializers.SerializerMethodField()
    duree_heures = serializers.SerializerMethodField()
    equipements_reserves = ReservationEquipementSerializer(many=True, read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id',
            'demandeur',
            'demandeur_nom',
            'type_reservation',
            'salle',
            'salle_nom',
            'date_debut',
            'date_fin',
            'duree_heures',
            'motif',
            'description',
            'nombre_participants',
            'statut',
            'valide_par',
            'valide_par_nom',
            'date_validation',
            'commentaire_validation',
            'equipements_reserves',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_demandeur_nom(self, obj):
        return f"{obj.demandeur.first_name} {obj.demandeur.last_name}"
    
    def get_valide_par_nom(self, obj):
        """Retourne le nom du validateur."""
        if obj.valide_par:
            return f"{obj.valide_par.first_name} {obj.valide_par.last_name}"
        return None
    
    def get_duree_heures(self, obj):
        return obj.calculer_duree()

# SERIALIZER : CRÉATION RÉSERVATION
class ReservationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une nouvelle réservation.
    
    Valide que :
    1. date_fin > date_debut
    2. Dates dans le futur
    3. Salle obligatoire si type SALLE ou SALLE_EQUIPEMENT
    4. Équipements fournis si type EQUIPEMENT ou SALLE_EQUIPEMENT
    """
    equipements = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
        help_text="Liste des équipements : [{'equipement_id': 1, 'quantite': 2}, ...]"
    )
    
    class Meta:
        model = Reservation
        fields = [
            'type_reservation',
            'salle',
            'date_debut',
            'date_fin',
            'motif',
            'description',
            'nombre_participants',
            'equipements',
        ]
    
    def validate(self, data):
        """
        Validation globale.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si données incohérentes
        
        Returns:
            dict: Données validées
        """
        type_reservation = data.get('type_reservation')
        salle = data.get('salle')
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        equipements = data.get('equipements', [])
        
        # Vérifier que date_fin > date_debut
        if date_fin <= date_debut:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        
        # Vérifier que les dates sont dans le futur
        if date_debut < timezone.now():
            raise serializers.ValidationError(
                "La date de début doit être dans le futur."
            )
        
        # Vérifier salle si type SALLE ou SALLE_EQUIPEMENT
        if type_reservation in ['SALLE', 'SALLE_EQUIPEMENT'] and not salle:
            raise serializers.ValidationError(
                "Une salle est requise pour ce type de réservation."
            )
        
        # Vérifier équipements si type EQUIPEMENT ou SALLE_EQUIPEMENT
        if type_reservation in ['EQUIPEMENT', 'SALLE_EQUIPEMENT'] and not equipements:
            raise serializers.ValidationError(
                "Au moins un équipement est requis pour ce type de réservation."
            )
        
        return data
    
    def create(self, validated_data):
        """
        Crée la réservation avec les équipements associés.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            Reservation: Instance créée
        """
        # Extraire les équipements
        equipements_data = validated_data.pop('equipements', [])
        
        # Récupérer le demandeur depuis le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['demandeur'] = request.user
        
        # Créer la réservation
        reservation = Reservation.objects.create(**validated_data)
        
        # Créer les liens avec les équipements
        for equip_data in equipements_data:
            equipement_id = equip_data.get('equipement_id')
            quantite = equip_data.get('quantite', 1)
            
            ReservationEquipement.objects.create(
                reservation=reservation,
                equipement_id=equipement_id,
                quantite=quantite
            )
        
        return reservation

# SERIALIZER : VALIDATION RÉSERVATION
class ReservationValidationSerializer(serializers.Serializer):
    """
    Serializer pour valider/rejeter une réservation.
    
    Format :
    {
        "action": "VALIDER|REJETER",
        "commentaire": "..."
    }
    """
    action = serializers.ChoiceField(
        choices=['VALIDER', 'REJETER'],
        help_text="Action à effectuer"
    )
    commentaire = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Commentaire optionnel (obligatoire si REJETER)"
    )
    
    def validate(self, data):
        """
        Validation : commentaire obligatoire si REJETER.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si commentaire manquant pour rejet
        
        Returns:
            dict: Données validées
        """
        if data['action'] == 'REJETER' and not data.get('commentaire'):
            raise serializers.ValidationError(
                "Un commentaire est obligatoire pour rejeter une réservation."
            )
        
        return data

# SERIALIZER : MAINTENANCE (LISTE)
class MaintenanceListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des maintenances (vue simplifiée).
    """
    equipement_nom = serializers.CharField(source='equipement.nom', read_only=True)
    equipement_reference = serializers.CharField(source='equipement.reference', read_only=True)
    technicien_nom = serializers.SerializerMethodField()
    cout_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Maintenance
        fields = [
            'id',
            'equipement',
            'equipement_nom',
            'equipement_reference',
            'type_maintenance',
            'statut',
            'date_planifiee',
            'date_debut',
            'date_fin',
            'technicien',
            'technicien_nom',
            'cout_total',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_technicien_nom(self, obj):
        """Retourne le nom du technicien."""
        if obj.technicien:
            return f"{obj.technicien.first_name} {obj.technicien.last_name}"
        return None
    
    def get_cout_total(self, obj):
        """Calcule le coût total."""
        return float(obj.calculer_cout_total())

# SERIALIZER : MAINTENANCE (DÉTAIL)
class MaintenanceDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'une maintenance.
    """
    equipement_nom = serializers.CharField(source='equipement.nom', read_only=True)
    equipement_reference = serializers.CharField(source='equipement.reference', read_only=True)
    technicien_nom = serializers.SerializerMethodField()
    cout_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Maintenance
        fields = [
            'id',
            'equipement',
            'equipement_nom',
            'equipement_reference',
            'type_maintenance',
            'statut',
            'date_planifiee',
            'date_debut',
            'date_fin',
            'technicien',
            'technicien_nom',
            'description',
            'travaux_effectues',
            'pieces_remplacees',
            'cout_main_oeuvre',
            'cout_pieces',
            'cout_total',
            'observations',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_technicien_nom(self, obj):
        if obj.technicien:
            return f"{obj.technicien.first_name} {obj.technicien.last_name}"
        return None
    
    def get_cout_total(self, obj):
        return float(obj.calculer_cout_total())

# SERIALIZER : CRÉATION MAINTENANCE
class MaintenanceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une nouvelle maintenance.
    
    Valide que la date planifiée est cohérente.
    """
    
    class Meta:
        model = Maintenance
        fields = [
            'equipement',
            'type_maintenance',
            'date_planifiee',
            'technicien',
            'description',
            'cout_main_oeuvre',
            'cout_pieces',
        ]
    
    def validate_date_planifiee(self, value):
        """
        Valide que la date planifiée n'est pas trop loin dans le passé.
        
        Args:
            value (date): Date planifiée
        
        Raises:
            ValidationError: Si date incohérente
        
        Returns:
            date: Date validée
        """
        from datetime import timedelta
        
        # Autoriser jusqu'à 7 jours dans le passé (pour rétroactif)
        limite_passee = timezone.now().date() - timedelta(days=7)
        
        if value < limite_passee:
            raise serializers.ValidationError(
                "La date planifiée ne peut pas être antérieure à 7 jours."
            )
        
        return value

# SERIALIZER : TERMINAISON MAINTENANCE
class MaintenanceTerminaisonSerializer(serializers.Serializer):
    """
    Serializer pour terminer une maintenance.
    
    Format :
    {
        "travaux_effectues": "Remplacement disque dur",
        "pieces_remplacees": "Disque dur 1TB",
        "observations": "Équipement opérationnel"
    }
    """
    travaux_effectues = serializers.CharField(
        help_text="Description des travaux effectués"
    )
    pieces_remplacees = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Liste des pièces remplacées"
    )
    observations = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Observations"
    )

# SERIALIZER : RETOUR ÉQUIPEMENT
class RetourEquipementSerializer(serializers.Serializer):
    """
    Serializer pour marquer le retour d'un équipement réservé.
    
    Format :
    {
        "etat_retour": "Bon état, aucun dommage"
    }
    """
    etat_retour = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="État de l'équipement au retour"
    )

# SERIALIZER : DISPONIBILITÉ ÉQUIPEMENT
class DisponibiliteEquipementSerializer(serializers.Serializer):
    """
    Serializer pour vérifier la disponibilité d'un équipement.
    
    Format :
    {
        "equipement_id": 1,
        "date_debut": "2026-02-01T10:00:00Z",
        "date_fin": "2026-02-01T14:00:00Z",
        "quantite": 2
    }
    """
    equipement_id = serializers.IntegerField(
        help_text="ID de l'équipement"
    )
    date_debut = serializers.DateTimeField(
        help_text="Date de début de la période"
    )
    date_fin = serializers.DateTimeField(
        help_text="Date de fin de la période"
    )
    quantite = serializers.IntegerField(
        default=1,
        help_text="Quantité souhaitée"
    )
    
    def validate(self, data):
        """
        Validation globale.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si données incohérentes
        
        Returns:
            dict: Données validées
        """
        if data['date_fin'] <= data['date_debut']:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        
        if data['quantite'] <= 0:
            raise serializers.ValidationError(
                "La quantité doit être supérieure à 0."
            )
        
        # Vérifier que l'équipement existe
        try:
            Equipement.objects.get(id=data['equipement_id'])
        except Equipement.DoesNotExist:
            raise serializers.ValidationError(
                f"Équipement avec l'ID {data['equipement_id']} non trouvé."
            )
        
        return data
