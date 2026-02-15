# Sérialisation des modèles académiques

from rest_framework import serializers
from .models import AnneeAcademique, Faculte, Departement, Filiere, Matiere

# ANNEE ACADEMIQUE SERIALIZER
class AnneeAcademiqueSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AnneeAcademique
        fields = [
            'id', 'code', 'date_debut', 'date_fin', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        # Vérifier que date_fin > date_debut.
        if attrs.get('date_fin') and attrs.get('date_debut'):
            if attrs['date_fin'] <= attrs['date_debut']:
                raise serializers.ValidationError({
                    'date_fin': 'La date de fin doit être après la date de début'
                })
        return attrs

# FACULTE SERIALIZER
class FaculteSerializer(serializers.ModelSerializer):
    # Champs calculés
    departements_count = serializers.SerializerMethodField()
    etudiants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Faculte
        fields = [
            'id', 'code', 'nom', 'description', 'doyen',
            'email', 'telephone', 'departements_count', 
            'etudiants_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_departements_count(self, obj):
        # Nombre de départements.
        return obj.get_departements_count()
    
    def get_etudiants_count(self, obj):
        # Nombre d'étudiants (sera implémenté au Sprint 3).
        return obj.get_etudiants_count()

# DEPARTEMENT SERIALIZER
class DepartementSerializer(serializers.ModelSerializer):
    
    # Inclure les détails de la faculté
    faculte_details = FaculteSerializer(source='faculte', read_only=True)
    
    # ID de la faculté pour lecture
    faculte = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # ID de la faculté (pour créer/modifier)
    faculte_id = serializers.PrimaryKeyRelatedField(
        queryset=Faculte.objects.all(),
        source='faculte',
        write_only=True
    )
    
    # Nombre de filières
    filieres_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Departement
        fields = [
            'id', 'code', 'nom', 'description', 'chef_departement',
            'faculte', 'faculte_id', 'faculte_details', 'filieres_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'faculte', 'faculte_details']
    
    def get_filieres_count(self, obj):
        # Nombre de filières.
        return obj.get_filieres_count()

# FILIERE SERIALIZER
class FiliereSerializer(serializers.ModelSerializer):
    
    # Détails du département
    departement_details = DepartementSerializer(source='departement', read_only=True)
    
    # ID du département (pour créer/modifier)
    departement_id = serializers.PrimaryKeyRelatedField(
        queryset=Departement.objects.all(),
        source='departement',
        write_only=True
    )
    
    # Affichage du cycle
    cycle_display = serializers.CharField(source='get_cycle_display', read_only=True)
    
    # Nombre de matières
    matieres_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Filiere
        fields = [
            'id', 'code', 'nom', 'cycle', 'cycle_display', 
            'duree_annees', 'frais_inscription', 'description',
            'departement_id', 'departement_details',
            'matieres_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'departement_details']
    
    def get_matieres_count(self, obj):
        # Nombre de matières.
        return obj.get_matieres_count()

# MATIERE SERIALIZER (Simple)
class MatiereSimpleSerializer(serializers.ModelSerializer):
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    volume_horaire_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Matiere
        fields = [
            'id', 'code', 'nom', 'coefficient', 'credits',
            'volume_horaire_cm', 'volume_horaire_td', 'volume_horaire_tp',
            'volume_horaire_total', 'semestre', 'semestre_display',
            'is_optionnelle', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_volume_horaire_total(self, obj):
        """Volume horaire total."""
        return obj.get_volume_horaire_total()

# MATIERE SERIALIZER (Complet)
class MatiereSerializer(serializers.ModelSerializer):
    # Détails des filières (lecture)
    filieres_details = FiliereSerializer(source='filieres', many=True, read_only=True)
    
    # IDs des filières (écriture)
    filiere_ids = serializers.PrimaryKeyRelatedField(
        queryset=Filiere.objects.all(),
        many=True,
        source='filieres',
        write_only=True,
        required=False
    )
    
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    volume_horaire_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Matiere
        fields = [
            'id', 'code', 'nom', 'coefficient', 'credits',
            'volume_horaire_cm', 'volume_horaire_td', 'volume_horaire_tp',
            'volume_horaire_total', 'semestre', 'semestre_display',
            'is_optionnelle', 'description', 'filiere_ids',
            'filieres_details', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'filieres_details']
    
    def get_volume_horaire_total(self, obj):
        # Volume horaire total.
        return obj.get_volume_horaire_total()
    
    def create(self, validated_data):
        # Créer une matière avec ses filières.
        filieres = validated_data.pop('filieres', [])
        matiere = Matiere.objects.create(**validated_data)
        if filieres:
            matiere.filieres.set(filieres)
        return matiere
    
    def update(self, instance, validated_data):
        # Mettre à jour une matière.
        filieres = validated_data.pop('filieres', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if filieres is not None:
            instance.filieres.set(filieres)
        
        return instance