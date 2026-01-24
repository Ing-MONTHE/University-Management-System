from rest_framework import serializers
from django.utils import timezone
from .models import Rapport, Dashboard, KPI

# SERIALIZER : RAPPORT (LISTE)
class RapportListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des rapports (vue simplifiée).
    """
    genere_par_nom = serializers.SerializerMethodField()
    fichier_url = serializers.SerializerMethodField()
    annee_academique_nom = serializers.CharField(
        source='annee_academique.nom',
        read_only=True,
        allow_null=True
    )
    filiere_nom = serializers.CharField(
        source='filiere.nom',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Rapport
        fields = [
            'id',
            'titre',
            'type_rapport',
            'format_export',
            'date_debut',
            'date_fin',
            'annee_academique',
            'annee_academique_nom',
            'filiere',
            'filiere_nom',
            'fichier',
            'fichier_url',
            'genere',
            'date_generation',
            'genere_par',
            'genere_par_nom',
            'planifie',
            'frequence',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_genere_par_nom(self, obj):
        if obj.genere_par:
            return f"{obj.genere_par.first_name} {obj.genere_par.last_name}"
        return None
    
    def get_fichier_url(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None

# SERIALIZER : RAPPORT (DÉTAIL)
class RapportDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un rapport.
    """
    genere_par_nom = serializers.SerializerMethodField()
    fichier_url = serializers.SerializerMethodField()
    annee_academique_nom = serializers.CharField(
        source='annee_academique.nom',
        read_only=True,
        allow_null=True
    )
    filiere_nom = serializers.CharField(
        source='filiere.nom',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Rapport
        fields = [
            'id',
            'titre',
            'description',
            'type_rapport',
            'format_export',
            'date_debut',
            'date_fin',
            'annee_academique',
            'annee_academique_nom',
            'filiere',
            'filiere_nom',
            'fichier',
            'fichier_url',
            'genere',
            'date_generation',
            'genere_par',
            'genere_par_nom',
            'planifie',
            'frequence',
            'prochaine_execution',
            'parametres',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_genere_par_nom(self, obj):
        if obj.genere_par:
            return f"{obj.genere_par.first_name} {obj.genere_par.last_name}"
        return None
    
    def get_fichier_url(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None

# SERIALIZER : CRÉATION RAPPORT
class RapportCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un nouveau rapport.
    """
    
    class Meta:
        model = Rapport
        fields = [
            'titre',
            'description',
            'type_rapport',
            'format_export',
            'date_debut',
            'date_fin',
            'annee_academique',
            'filiere',
            'planifie',
            'frequence',
            'parametres',
        ]
    
    def validate(self, data):
        """
        Validation globale.
        """
        if data['date_fin'] <= data['date_debut']:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        
        return data

# SERIALIZER : DASHBOARD (LISTE)
class DashboardListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des dashboards.
    """
    proprietaire_nom = serializers.SerializerMethodField()
    nombre_partages = serializers.SerializerMethodField()
    
    class Meta:
        model = Dashboard
        fields = [
            'id',
            'nom',
            'type_dashboard',
            'proprietaire',
            'proprietaire_nom',
            'partage',
            'nombre_partages',
            'par_defaut',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_proprietaire_nom(self, obj):
        return f"{obj.proprietaire.first_name} {obj.proprietaire.last_name}"
    
    def get_nombre_partages(self, obj):
        return obj.utilisateurs_partages.count()

# SERIALIZER : DASHBOARD (DÉTAIL)
class DashboardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un dashboard.
    """
    proprietaire_nom = serializers.SerializerMethodField()
    utilisateurs_partages_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Dashboard
        fields = [
            'id',
            'nom',
            'description',
            'type_dashboard',
            'proprietaire',
            'proprietaire_nom',
            'partage',
            'utilisateurs_partages',
            'utilisateurs_partages_details',
            'configuration',
            'par_defaut',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_proprietaire_nom(self, obj):
        return f"{obj.proprietaire.first_name} {obj.proprietaire.last_name}"
    
    def get_utilisateurs_partages_details(self, obj):
        return [
            {
                'id': user.id,
                'nom': f"{user.first_name} {user.last_name}",
                'email': user.email
            }
            for user in obj.utilisateurs_partages.all()
        ]

# SERIALIZER : CRÉATION DASHBOARD
class DashboardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un dashboard.
    """
    
    class Meta:
        model = Dashboard
        fields = [
            'nom',
            'description',
            'type_dashboard',
            'partage',
            'utilisateurs_partages',
            'configuration',
            'par_defaut',
        ]
    
    def create(self, validated_data):
        """
        Crée le dashboard avec le propriétaire automatiquement défini.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['proprietaire'] = request.user
        
        return Dashboard.objects.create(**validated_data)

# SERIALIZER : KPI (LISTE)
class KPIListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des KPIs.
    """
    taux_atteinte = serializers.SerializerMethodField()
    objectif_atteint = serializers.SerializerMethodField()
    
    class Meta:
        model = KPI
        fields = [
            'id',
            'nom',
            'code',
            'categorie',
            'type_valeur',
            'valeur',
            'objectif',
            'taux_atteinte',
            'objectif_atteint',
            'date_calcul',
            'actif',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_taux_atteinte(self, obj):
        taux = obj.calculer_taux_atteinte()
        return float(taux) if taux is not None else None
    
    def get_objectif_atteint(self, obj):
        return obj.est_objectif_atteint()

# SERIALIZER : KPI (DÉTAIL)
class KPIDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un KPI.
    """
    taux_atteinte = serializers.SerializerMethodField()
    objectif_atteint = serializers.SerializerMethodField()
    annee_academique_nom = serializers.CharField(
        source='annee_academique.nom',
        read_only=True,
        allow_null=True
    )
    filiere_nom = serializers.CharField(
        source='filiere.nom',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = KPI
        fields = [
            'id',
            'nom',
            'description',
            'code',
            'categorie',
            'type_valeur',
            'valeur',
            'objectif',
            'taux_atteinte',
            'objectif_atteint',
            'date_calcul',
            'annee_academique',
            'annee_academique_nom',
            'filiere',
            'filiere_nom',
            'actif',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_taux_atteinte(self, obj):
        taux = obj.calculer_taux_atteinte()
        return float(taux) if taux is not None else None
    
    def get_objectif_atteint(self, obj):
        return obj.est_objectif_atteint()

# SERIALIZER : CRÉATION KPI
class KPICreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un KPI.
    """
    
    class Meta:
        model = KPI
        fields = [
            'nom',
            'description',
            'code',
            'categorie',
            'type_valeur',
            'valeur',
            'objectif',
            'date_calcul',
            'annee_academique',
            'filiere',
            'actif',
        ]
