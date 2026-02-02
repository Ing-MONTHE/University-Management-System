# Sérialisation des modèles étudiants/enseignants

import datetime
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

class EtudiantListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des étudiants (lecture seule)"""
    
    nom = serializers.CharField(source='user.last_name', read_only=True)
    prenom = serializers.CharField(source='user.first_name', read_only=True)
    email = serializers.EmailField(source='email_personnel', read_only=True)
    sexe_display = serializers.CharField(source='get_sexe_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Etudiant
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'sexe', 'sexe_display',
            'date_naissance', 'lieu_naissance', 'nationalite', 
            'telephone', 'email', 'email_personnel', 'adresse', 'ville', 'pays',
            'photo', 'photo_url', 'tuteur_nom', 'tuteur_telephone', 'tuteur_email',
            'statut', 'statut_display', 'created_at', 'updated_at'
        ]
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class EtudiantCreateSerializer(serializers.Serializer):
    """Serializer pour créer un étudiant depuis le frontend"""
    
    # Données personnelles
    nom = serializers.CharField(max_length=150)
    prenom = serializers.CharField(max_length=150)
    sexe = serializers.ChoiceField(choices=['M', 'F'])
    date_naissance = serializers.DateField()
    lieu_naissance = serializers.CharField(max_length=200)
    nationalite = serializers.CharField(max_length=100, default='Camerounaise')
    
    # Contact
    telephone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    adresse = serializers.CharField(required=False, allow_blank=True)
    ville = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pays = serializers.CharField(max_length=100, default='Cameroun')
    
    # Tuteur
    tuteur_nom = serializers.CharField(required=False, allow_blank=True)
    tuteur_telephone = serializers.CharField(required=False, allow_blank=True)
    tuteur_email = serializers.EmailField(required=False, allow_blank=True)
    
    # Statut
    statut = serializers.ChoiceField(
        choices=['ACTIF', 'SUSPENDU', 'DIPLOME', 'EXCLU', 'ABANDONNE'],
        default='ACTIF'
    )
    
    # Photo (optionnel)
    photo = serializers.ImageField(required=False, allow_null=True)
    
    def validate_email(self, value):
        """Vérifier que l'email est unique"""
        if Etudiant.objects.filter(email_personnel=value).exists():
            raise serializers.ValidationError("Un étudiant avec cet email existe déjà.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def create(self, validated_data):
        """Créer un étudiant avec son compte utilisateur"""
        
        # Extraire les données
        nom = validated_data['nom']
        prenom = validated_data['prenom']
        email = validated_data['email']
        photo = validated_data.pop('photo', None)
        
        # Générer username unique
        base_username = f"{prenom.lower()}.{nom.lower()}"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=prenom,
            last_name=nom,
            password='changeme123'  # Mot de passe par défaut
        )
        
        # Générer matricule unique
        annee = datetime.now().year
        matricule = Etudiant.generer_matricule(annee)

        # Créer l'étudiant
        etudiant = Etudiant.objects.create(
            user=user,
            matricule=matricule,
            date_naissance=validated_data['date_naissance'],
            lieu_naissance=validated_data['lieu_naissance'],
            sexe=validated_data['sexe'],
            nationalite=validated_data.get('nationalite', 'Camerounaise'),
            telephone=validated_data['telephone'],
            email_personnel=email,
            adresse=validated_data.get('adresse', ''),
            ville=validated_data.get('ville', ''),
            pays=validated_data.get('pays', 'Cameroun'),
            tuteur_nom=validated_data.get('tuteur_nom', ''),
            tuteur_telephone=validated_data.get('tuteur_telephone', ''),
            tuteur_email=validated_data.get('tuteur_email', ''),
            statut=validated_data.get('statut', 'ACTIF'),
            photo=photo
        )
        
        return etudiant


class EtudiantUpdateSerializer(serializers.Serializer):
    """Serializer pour mettre à jour un étudiant"""
    
    # Données modifiables
    date_naissance = serializers.DateField(required=False)
    lieu_naissance = serializers.CharField(max_length=200, required=False)
    sexe = serializers.ChoiceField(choices=['M', 'F'], required=False)
    nationalite = serializers.CharField(max_length=100, required=False)
    telephone = serializers.CharField(max_length=20, required=False)
    email_personnel = serializers.EmailField(required=False)
    adresse = serializers.CharField(required=False, allow_blank=True)
    ville = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pays = serializers.CharField(max_length=100, required=False)
    tuteur_nom = serializers.CharField(required=False, allow_blank=True)
    tuteur_telephone = serializers.CharField(required=False, allow_blank=True)
    tuteur_email = serializers.EmailField(required=False, allow_blank=True)
    statut = serializers.ChoiceField(
        choices=['ACTIF', 'SUSPENDU', 'DIPLOME', 'EXCLU', 'ABANDONNE'],
        required=False
    )
    
    def update(self, instance, validated_data):
        """Mettre à jour l'étudiant"""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class EtudiantDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un étudiant avec toutes les infos"""
    
    user = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    sexe_display = serializers.CharField(source='get_sexe_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    inscriptions = serializers.SerializerMethodField()
    
    class Meta:
        model = Etudiant
        fields = '__all__'
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def get_inscriptions(self, obj):
        from apps.students.serializers import InscriptionSerializer
        inscriptions = obj.inscriptions.all()[:5]  # Dernières 5 inscriptions
        return InscriptionSerializer(inscriptions, many=True, context=self.context).data
