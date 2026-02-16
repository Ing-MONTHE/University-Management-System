# Sérialisation des modèles d'emploi du temps

from rest_framework import serializers
from .models import Batiment, Salle, Creneau, Cours, ConflitSalle
from apps.academic.models import Matiere, AnneeAcademique
from apps.students.models import Enseignant, Filiere

# BATIMENT SERIALIZER
class BatimentSerializer(serializers.ModelSerializer):
    """
    Serializer pour Bâtiment.
    """
    
    nombre_salles = serializers.SerializerMethodField()
    
    class Meta:
        model = Batiment
        fields = [
            'id', 'code', 'nom', 'nombre_etages', 'adresse',
            'is_active', 'nombre_salles', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_nombre_salles(self, obj):
        """Nombre de salles dans le bâtiment."""
        return obj.get_nombre_salles()

# SALLE SERIALIZER
class SalleSerializer(serializers.ModelSerializer):
    """
    Serializer pour Salle.
    """
    
    # Détails batiment
    batiment_details = BatimentSerializer(source='batiment', read_only=True)
    
    # ID batiment pour création
    batiment_id = serializers.PrimaryKeyRelatedField(
        queryset=Batiment.objects.all(),
        source='batiment',
        write_only=True
    )
    
    # Display
    type_salle_display = serializers.CharField(source='get_type_salle_display', read_only=True)
    
    # Taux d'occupation
    taux_occupation = serializers.SerializerMethodField()
    
    class Meta:
        model = Salle
        fields = [
            'id', 'batiment', 'batiment_id', 'batiment_details',
            'code', 'nom', 'type_salle', 'type_salle_display',
            'capacite', 'etage', 'equipements', 'is_disponible',
            'taux_occupation', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_taux_occupation(self, obj):
        """Taux d'occupation de la salle."""
        # Obtenir l'année académique active
        try:
            annee_active = AnneeAcademique.objects.get(is_active=True)
            return obj.get_taux_occupation(annee_active)
        except AnneeAcademique.DoesNotExist:
            return 0

# CRENEAU SERIALIZER
class CreneauSerializer(serializers.ModelSerializer):
    """
    Serializer pour Créneau horaire.
    """
    
    jour_display = serializers.CharField(source='get_jour_display', read_only=True)
    duree_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Creneau
        fields = [
            'id', 'jour', 'jour_display', 'heure_debut', 'heure_fin',
            'code', 'duree_minutes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']
    
    def get_duree_minutes(self, obj):
        """Durée du créneau en minutes."""
        return obj.get_duree_minutes()
    
    def validate(self, attrs):
        """Validation personnalisée."""
        heure_debut = attrs.get('heure_debut')
        heure_fin = attrs.get('heure_fin')
        
        if heure_debut and heure_fin:
            if heure_fin <= heure_debut:
                raise serializers.ValidationError({
                    'heure_fin': 'L\'heure de fin doit être après l\'heure de début'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Créer un créneau avec génération automatique du code."""
        from datetime import datetime
        
        # Convertir les heures au format time si nécessaire
        heure_debut = validated_data.get('heure_debut')
        heure_fin = validated_data.get('heure_fin')
        
        # Si les heures sont des strings, les convertir
        if isinstance(heure_debut, str):
            heure_debut = datetime.strptime(heure_debut, '%H:%M').time()
            validated_data['heure_debut'] = heure_debut
        
        if isinstance(heure_fin, str):
            heure_fin = datetime.strptime(heure_fin, '%H:%M').time()
            validated_data['heure_fin'] = heure_fin
        
        # Générer le code automatiquement si non fourni
        if 'code' not in validated_data or not validated_data['code']:
            jour = validated_data['jour']
            validated_data['code'] = f"{jour}-{heure_debut.strftime('%H%M')}-{heure_fin.strftime('%H%M')}"
        
        return super().create(validated_data)

# COURS SERIALIZER
class CoursSerializer(serializers.ModelSerializer):
    """
    Serializer pour Cours.
    """
    
    # Détails des relations
    annee_academique_details = serializers.SerializerMethodField()
    matiere_details = serializers.SerializerMethodField()
    enseignant_details = serializers.SerializerMethodField()
    filiere_details = serializers.SerializerMethodField()
    salle_details = SalleSerializer(source='salle', read_only=True)
    creneau_details = CreneauSerializer(source='creneau', read_only=True)
    
    # IDs pour création
    annee_academique_id = serializers.PrimaryKeyRelatedField(
        queryset=AnneeAcademique.objects.all(),
        source='annee_academique',
        write_only=True
    )
    
    matiere_id = serializers.PrimaryKeyRelatedField(
        queryset=Matiere.objects.all(),
        source='matiere',
        write_only=True
    )
    
    enseignant_id = serializers.PrimaryKeyRelatedField(
        queryset=Enseignant.objects.all(),
        source='enseignant',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    filiere_id = serializers.PrimaryKeyRelatedField(
        queryset=Filiere.objects.all(),
        source='filiere',
        write_only=True
    )
    
    salle_id = serializers.PrimaryKeyRelatedField(
        queryset=Salle.objects.all(),
        source='salle',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    creneau_id = serializers.PrimaryKeyRelatedField(
        queryset=Creneau.objects.all(),
        source='creneau',
        write_only=True
    )
    
    # Display
    type_cours_display = serializers.CharField(source='get_type_cours_display', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = Cours
        fields = [
            'id', 'annee_academique', 'annee_academique_id', 'annee_academique_details',
            'matiere', 'matiere_id', 'matiere_details',
            'enseignant', 'enseignant_id', 'enseignant_details',
            'filiere', 'filiere_id', 'filiere_details',
            'salle', 'salle_id', 'salle_details',
            'creneau', 'creneau_id', 'creneau_details',
            'type_cours', 'type_cours_display', 'effectif_prevu',
            'semestre', 'semestre_display', 'date_debut', 'date_fin',
            'is_actif', 'remarques', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_annee_academique_details(self, obj):
        """Détails année académique."""
        return {
            'id': obj.annee_academique.id,
            'code': obj.annee_academique.code
        }
    
    def get_matiere_details(self, obj):
        """Détails matière."""
        return {
            'id': obj.matiere.id,
            'code': obj.matiere.code,
            'nom': obj.matiere.nom
        }
    
    def get_enseignant_details(self, obj):
        """Détails enseignant."""
        if obj.enseignant:
            return {
                'id': obj.enseignant.id,
                'matricule': obj.enseignant.matricule,
                'nom_complet': obj.enseignant.user.get_full_name(),
                'grade': obj.enseignant.get_grade_display()
            }
        return None
    
    def get_filiere_details(self, obj):
        """Détails filière."""
        return {
            'id': obj.filiere.id,
            'code': obj.filiere.code,
            'nom': obj.filiere.nom
        }
    
    def validate(self, attrs):
        """Validation des conflits."""
        # Récupérer les valeurs
        salle = attrs.get('salle')
        creneau = attrs.get('creneau')
        annee_academique = attrs.get('annee_academique')
        enseignant = attrs.get('enseignant')
        effectif_prevu = attrs.get('effectif_prevu')
        
        # Si c'est une mise à jour, exclure le cours actuel
        instance = self.instance
        
        # 1. Vérifier conflit de salle
        if salle and creneau and annee_academique:
            conflit_salle = Cours.objects.filter(
                salle=salle,
                creneau=creneau,
                annee_academique=annee_academique,
                is_actif=True
            )
            
            if instance:
                conflit_salle = conflit_salle.exclude(pk=instance.pk)
            
            if conflit_salle.exists():
                cours_existant = conflit_salle.first()
                raise serializers.ValidationError({
                    'salle': f'Cette salle est déjà occupée à ce créneau par : {cours_existant.matiere.nom} ({cours_existant.filiere.code})'
                })
        
        # 2. Vérifier conflit enseignant
        if enseignant and creneau and annee_academique:
            conflit_enseignant = Cours.objects.filter(
                enseignant=enseignant,
                creneau=creneau,
                annee_academique=annee_academique,
                is_actif=True
            )
            
            if instance:
                conflit_enseignant = conflit_enseignant.exclude(pk=instance.pk)
            
            if conflit_enseignant.exists():
                cours_existant = conflit_enseignant.first()
                raise serializers.ValidationError({
                    'enseignant': f'Cet enseignant a déjà un cours à ce créneau : {cours_existant.matiere.nom} ({cours_existant.filiere.code})'
                })
        
        # 3. Vérifier capacité de la salle
        if salle and effectif_prevu:
            if effectif_prevu > salle.capacite:
                raise serializers.ValidationError({
                    'effectif_prevu': f'L\'effectif ({effectif_prevu}) dépasse la capacité de la salle ({salle.capacite})'
                })
        
        return attrs

# CONFLIT SALLE SERIALIZER
class ConflitSalleSerializer(serializers.ModelSerializer):
    """
    Serializer pour Conflit de salle.
    """
    
    # Détails des cours
    cours1_details = CoursSerializer(source='cours1', read_only=True)
    cours2_details = CoursSerializer(source='cours2', read_only=True)
    
    # IDs pour création
    cours1_id = serializers.PrimaryKeyRelatedField(
        queryset=Cours.objects.all(),
        source='cours1',
        write_only=True
    )
    
    cours2_id = serializers.PrimaryKeyRelatedField(
        queryset=Cours.objects.all(),
        source='cours2',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Display
    type_conflit_display = serializers.CharField(source='get_type_conflit_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = ConflitSalle
        fields = [
            'id', 'cours1', 'cours1_id', 'cours1_details',
            'cours2', 'cours2_id', 'cours2_details',
            'type_conflit', 'type_conflit_display',
            'description', 'statut', 'statut_display',
            'date_detection', 'date_resolution', 'solution_appliquee',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_detection', 'created_at', 'updated_at']

# DETECTION CONFLITS SERIALIZER
class DetectionConflitsSerializer(serializers.Serializer):
    """
    Serializer pour déclencher la détection de conflits.
    """
    
    annee_academique_id = serializers.IntegerField(
        help_text="ID de l'année académique à analyser"
    )

# RESOLUTION CONFLIT SERIALIZER
class ResolutionConflitSerializer(serializers.Serializer):
    """
    Serializer pour résoudre un conflit.
    """
    
    solution = serializers.CharField(
        help_text="Description de la solution appliquée"
    )

# EMPLOI DU TEMPS PAR FILIERE SERIALIZER
class EmploiDuTempsSerializer(serializers.Serializer):
    """
    Serializer pour générer un emploi du temps.
    """
    
    filiere_id = serializers.IntegerField()
    semestre = serializers.IntegerField(min_value=1, max_value=2)
    annee_academique_id = serializers.IntegerField(required=False)

# STATISTIQUES EMPLOI DU TEMPS
class StatistiquesEmploiDuTempsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques d'emploi du temps.
    """
    
    annee_academique_id = serializers.IntegerField(required=False)