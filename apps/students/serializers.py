# Sérialisation des modèles étudiants/enseignants

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Etudiant, Enseignant, Inscription, Attribution
from apps.core.serializers import UserSerializer
from apps.academic.serializers import (
    FiliereSerializer, 
    MatiereSimpleSerializer,
    DepartementSerializer,
    AnneeAcademiqueSerializer
)

User = get_user_model()

# ETUDIANT SERIALIZER
class EtudiantSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour Étudiant.
    Inclut les infos du user.
    """
    
    # Détails de l'utilisateur (lecture)
    user_details = UserSerializer(source='user', read_only=True)
    
    # Données user pour création
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    
    # Champs calculés
    filiere_actuelle = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    sexe_display = serializers.CharField(source='get_sexe_display', read_only=True)
    
    # Photo URL
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Etudiant
        fields = [
            'id', 'user', 'user_details', 'username', 'email', 'password',
            'first_name', 'last_name', 'matricule', 'date_naissance',
            'lieu_naissance', 'sexe', 'sexe_display', 'nationalite',
            'telephone', 'email_personnel', 'adresse', 'ville', 'pays',
            'photo', 'photo_url', 'tuteur_nom', 'tuteur_telephone',
            'tuteur_email', 'statut', 'statut_display', 'filiere_actuelle',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'matricule', 'created_at', 'updated_at']
    
    def get_filiere_actuelle(self, obj):
        # Filière actuelle de l'étudiant.
        filiere = obj.get_filiere_actuelle()
        if filiere:
            return {
                'id': filiere.id,
                'code': filiere.code,
                'nom': filiere.nom
            }
        return None
    
    def get_photo_url(self, obj):
        # URL de la photo.
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def create(self, validated_data):
        # Créer un étudiant avec son compte utilisateur.
        # Extraire les données user
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Générer le matricule
        from datetime import datetime
        annee = datetime.now().year
        matricule = Etudiant.generer_matricule(annee)
        
        # Créer l'étudiant
        etudiant = Etudiant.objects.create(
            user=user,
            matricule=matricule,
            **validated_data
        )
        
        return etudiant

# ENSEIGNANT SERIALIZER
class EnseignantSerializer(serializers.ModelSerializer):
    # Serializer complet pour Enseignant.
    
    # Détails de l'utilisateur
    user_details = UserSerializer(source='user', read_only=True)
    
    # Données user pour création
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    
    # Détails département
    departement_details = DepartementSerializer(source='departement', read_only=True)
    
    # ID département (pour création)
    departement_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['Departement']).Departement.objects.all(),
        source='departement',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Champs calculés
    grade_display = serializers.CharField(source='get_grade_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    sexe_display = serializers.CharField(source='get_sexe_display', read_only=True)
    matieres_enseignees = serializers.SerializerMethodField()
    
    # URLs fichiers
    photo_url = serializers.SerializerMethodField()
    cv_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Enseignant
        fields = [
            'id', 'user', 'user_details', 'username', 'email', 'password',
            'first_name', 'last_name', 'matricule', 'departement',
            'departement_id', 'departement_details', 'specialite', 'grade',
            'grade_display', 'date_naissance', 'sexe', 'sexe_display',
            'telephone', 'email_personnel', 'adresse', 'photo', 'photo_url',
            'cv', 'cv_url', 'date_embauche', 'statut', 'statut_display',
            'matieres_enseignees', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'matricule', 'created_at', 'updated_at']
    
    def get_matieres_enseignees(self, obj):
        # Liste des matières enseignées.
        return list(obj.get_matieres_enseignees())
    
    def get_photo_url(self, obj):
        # URL de la photo.
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def get_cv_url(self, obj):
        # URL du CV.
        if obj.cv:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cv.url)
            return obj.cv.url
        return None
    
    def create(self, validated_data):
        # Créer un enseignant avec son compte utilisateur.
        # Extraire les données user
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Générer le matricule
        from datetime import datetime
        annee = datetime.now().year
        matricule = Enseignant.generer_matricule(annee)
        
        # Créer l'enseignant
        enseignant = Enseignant.objects.create(
            user=user,
            matricule=matricule,
            **validated_data
        )
        
        return enseignant

# INSCRIPTION SERIALIZER
class InscriptionSerializer(serializers.ModelSerializer):
    # Serializer pour Inscription.
    
    # Détails
    etudiant_details = EtudiantSerializer(source='etudiant', read_only=True)
    filiere_details = FiliereSerializer(source='filiere', read_only=True)
    annee_academique_details = AnneeAcademiqueSerializer(source='annee_academique', read_only=True)
    
    # IDs pour création
    etudiant_id = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(),
        source='etudiant',
        write_only=True
    )
    
    filiere_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['Filiere']).Filiere.objects.all(),
        source='filiere',
        write_only=True
    )
    
    annee_academique_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['AnneeAcademique']).AnneeAcademique.objects.all(),
        source='annee_academique',
        write_only=True
    )
    
    # Champs calculés
    statut_paiement_display = serializers.CharField(source='get_statut_paiement_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    reste_a_payer = serializers.SerializerMethodField()
    est_solde = serializers.SerializerMethodField()
    
    class Meta:
        model = Inscription
        fields = [
            'id', 'etudiant', 'etudiant_id', 'etudiant_details',
            'filiere', 'filiere_id', 'filiere_details',
            'annee_academique', 'annee_academique_id', 'annee_academique_details',
            'niveau', 'date_inscription', 'montant_inscription',
            'montant_paye', 'reste_a_payer', 'est_solde',
            'statut_paiement', 'statut_paiement_display',
            'statut', 'statut_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_inscription', 'created_at', 'updated_at']
    
    def get_reste_a_payer(self, obj):
        # Montant restant.
        return obj.get_reste_a_payer()
    
    def get_est_solde(self, obj):
        # Inscription soldée ?
        return obj.est_solde()

# ATTRIBUTION SERIALIZER
class AttributionSerializer(serializers.ModelSerializer):
    # Serializer pour Attribution.
    
    # Détails
    enseignant_details = EnseignantSerializer(source='enseignant', read_only=True)
    matiere_details = MatiereSimpleSerializer(source='matiere', read_only=True)
    annee_academique_details = AnneeAcademiqueSerializer(source='annee_academique', read_only=True)
    
    # IDs pour création
    enseignant_id = serializers.PrimaryKeyRelatedField(
        queryset=Enseignant.objects.all(),
        source='enseignant',
        write_only=True
    )
    
    matiere_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['Matiere']).Matiere.objects.all(),
        source='matiere',
        write_only=True
    )
    
    annee_academique_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['AnneeAcademique']).AnneeAcademique.objects.all(),
        source='annee_academique',
        write_only=True
    )
    
    # Champs calculés
    type_enseignement_display = serializers.CharField(source='get_type_enseignement_display', read_only=True)
    
    class Meta:
        model = Attribution
        fields = [
            'id', 'enseignant', 'enseignant_id', 'enseignant_details',
            'matiere', 'matiere_id', 'matiere_details',
            'annee_academique', 'annee_academique_id', 'annee_academique_details',
            'type_enseignement', 'type_enseignement_display',
            'volume_horaire_assigne', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
