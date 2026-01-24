from rest_framework import serializers
from django.utils import timezone
from .models import FeuillePresence, Presence, JustificatifAbsence
from apps.students.models import Etudiant

# SERIALIZER : FEUILLE DE PRÉSENCE (LISTE)
class FeuillePresenceListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des feuilles de présence (vue simplifiée).
    
    Affiche les informations essentielles pour les listes.
    Inclut les noms lisibles du cours, de la matière, de l'enseignant.
    """
    # Champs calculés pour affichage lisible
    cours_nom = serializers.CharField(source='cours.matiere.nom', read_only=True)
    enseignant_nom = serializers.SerializerMethodField()
    filiere_nom = serializers.CharField(source='cours.filiere.nom', read_only=True)
    taux_presence = serializers.SerializerMethodField()
    
    class Meta:
        model = FeuillePresence
        fields = [
            'id',
            'cours',
            'cours_nom',
            'enseignant_nom',
            'filiere_nom',
            'date_cours',
            'heure_debut',
            'heure_fin',
            'statut',
            'nombre_presents',
            'nombre_absents',
            'nombre_retards',
            'taux_presence',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_enseignant_nom(self, obj):
        """
        Retourne le nom complet de l'enseignant du cours.
        
        Returns:
            str: Nom complet (Prénom Nom)
        """
        return f"{obj.cours.enseignant.user.first_name} {obj.cours.enseignant.user.last_name}"
    
    def get_taux_presence(self, obj):
        """
        Calcule le taux de présence en pourcentage.
        
        Returns:
            float: Taux de présence (0-100)
        """
        return obj.calculer_taux_presence()

# SERIALIZER : FEUILLE DE PRÉSENCE (DÉTAIL)
class FeuillePresenceDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'une feuille de présence.
    
    Inclut toutes les informations + liste des présences des étudiants.
    """
    cours_nom = serializers.CharField(source='cours.matiere.nom', read_only=True)
    enseignant_nom = serializers.SerializerMethodField()
    filiere_nom = serializers.CharField(source='cours.filiere.nom', read_only=True)
    taux_presence = serializers.SerializerMethodField()
    # Liste des présences sera ajoutée dans les vues
    
    class Meta:
        model = FeuillePresence
        fields = [
            'id',
            'cours',
            'cours_nom',
            'enseignant_nom',
            'filiere_nom',
            'date_cours',
            'heure_debut',
            'heure_fin',
            'statut',
            'nombre_presents',
            'nombre_absents',
            'nombre_retards',
            'taux_presence',
            'observations',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_enseignant_nom(self, obj):
        return f"{obj.cours.enseignant.user.first_name} {obj.cours.enseignant.user.last_name}"
    
    def get_taux_presence(self, obj):
        return obj.calculer_taux_presence()

# SERIALIZER : CRÉATION FEUILLE DE PRÉSENCE
class FeuillePresenceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une nouvelle feuille de présence.
    
    Valide que :
    1. Le cours existe
    2. Pas de doublon (cours + date)
    3. La date n'est pas dans le futur lointain
    """
    
    class Meta:
        model = FeuillePresence
        fields = [
            'cours',
            'date_cours',
            'heure_debut',
            'heure_fin',
            'observations',
        ]
    
    def validate_date_cours(self, value):
        """
        Valide que la date du cours est cohérente.
        
        Args:
            value (date): Date du cours
        
        Raises:
            ValidationError: Si la date est trop loin dans le futur
        
        Returns:
            date: Date validée
        """
        from datetime import timedelta
        
        # Ne pas autoriser les dates trop loin dans le futur (> 1 mois)
        date_max = timezone.now().date() + timedelta(days=30)
        if value > date_max:
            raise serializers.ValidationError(
                "La date du cours ne peut pas être plus d'un mois dans le futur."
            )
        
        return value
    
    def validate(self, data):
        """
        Validation globale : vérifier les doublons et la cohérence des heures.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si doublon ou heures incohérentes
        
        Returns:
            dict: Données validées
        """
        # Vérifier les doublons
        if FeuillePresence.objects.filter(
            cours=data['cours'],
            date_cours=data['date_cours']
        ).exists():
            raise serializers.ValidationError(
                "Une feuille de présence existe déjà pour ce cours à cette date."
            )
        
        # Vérifier que heure_fin > heure_debut
        if data['heure_fin'] <= data['heure_debut']:
            raise serializers.ValidationError(
                "L'heure de fin doit être postérieure à l'heure de début."
            )
        
        return data
    
    def create(self, validated_data):
        """
        Crée la feuille de présence et génère automatiquement
        les enregistrements de présence pour tous les étudiants inscrits.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            FeuillePresence: Instance créée
        """
        # Créer la feuille
        feuille = FeuillePresence.objects.create(**validated_data)
        
        # Récupérer tous les étudiants inscrits dans cette filière
        cours = validated_data['cours']
        etudiants = Etudiant.objects.filter(
            inscriptions__filiere=cours.filiere,
            inscriptions__annee_academique__est_active=True
        ).distinct()
        
        # Créer un enregistrement de présence pour chaque étudiant
        # (par défaut : ABSENT)
        presences = [
            Presence(
                feuille_presence=feuille,
                etudiant=etudiant,
                statut='ABSENT'
            )
            for etudiant in etudiants
        ]
        
        # Insertion en masse (plus performant)
        Presence.objects.bulk_create(presences)
        
        # Mettre à jour le nombre d'absents
        feuille.nombre_absents = len(presences)
        feuille.save()
        
        return feuille

# SERIALIZER : PRÉSENCE ÉTUDIANT
class PresenceSerializer(serializers.ModelSerializer):
    """
    Serializer pour les enregistrements de présence individuelle.
    
    Affiche les informations de présence d'un étudiant à un cours.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='etudiant.matricule', read_only=True)
    minutes_retard = serializers.SerializerMethodField()
    
    class Meta:
        model = Presence
        fields = [
            'id',
            'feuille_presence',
            'etudiant',
            'etudiant_nom',
            'etudiant_matricule',
            'statut',
            'heure_arrivee',
            'absence_justifiee',
            'remarque',
            'minutes_retard',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_etudiant_nom(self, obj):
        """Retourne le nom complet de l'étudiant."""
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_minutes_retard(self, obj):
        """Calcule les minutes de retard."""
        return obj.calculer_minutes_retard()

# SERIALIZER : MARQUER PRÉSENCES EN MASSE
class MarquerPresencesSerializer(serializers.Serializer):
    """
    Serializer pour marquer les présences de plusieurs étudiants en une fois.
    
    Permet à l'enseignant de marquer rapidement toute la classe.
    
    Format attendu :
    {
        "presences": [
            {"etudiant_id": 1, "statut": "PRESENT"},
            {"etudiant_id": 2, "statut": "ABSENT"},
            {"etudiant_id": 3, "statut": "RETARD", "heure_arrivee": "09:15"}
        ]
    }
    """
    presences = serializers.ListField(
        child=serializers.DictField(),
        help_text="Liste des présences à marquer"
    )
    
    def validate_presences(self, value):
        """
        Valide le format de la liste des présences.
        
        Args:
            value (list): Liste des présences
        
        Raises:
            ValidationError: Si format invalide
        
        Returns:
            list: Données validées
        """
        statuts_valides = ['PRESENT', 'ABSENT', 'RETARD']
        
        for item in value:
            # Vérifier les champs requis
            if 'etudiant_id' not in item or 'statut' not in item:
                raise serializers.ValidationError(
                    "Chaque présence doit contenir 'etudiant_id' et 'statut'."
                )
            
            # Vérifier le statut
            if item['statut'] not in statuts_valides:
                raise serializers.ValidationError(
                    f"Statut invalide : {item['statut']}. "
                    f"Valeurs autorisées : {', '.join(statuts_valides)}"
                )
            
            # Si RETARD, vérifier l'heure d'arrivée
            if item['statut'] == 'RETARD' and 'heure_arrivee' not in item:
                raise serializers.ValidationError(
                    "L'heure d'arrivée est requise pour un statut RETARD."
                )
        
        return value

# SERIALIZER : JUSTIFICATIF D'ABSENCE (LISTE)
class JustificatifAbsenceListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des justificatifs (vue simplifiée).
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='etudiant.matricule', read_only=True)
    duree_jours = serializers.SerializerMethodField()
    
    class Meta:
        model = JustificatifAbsence
        fields = [
            'id',
            'etudiant',
            'etudiant_nom',
            'etudiant_matricule',
            'date_debut',
            'date_fin',
            'duree_jours',
            'type_justificatif',
            'statut',
            'date_soumission',
            'date_traitement',
        ]
        read_only_fields = ['id', 'date_soumission', 'date_traitement']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_duree_jours(self, obj):
        """Retourne la durée en jours."""
        return obj.calculer_duree()

# SERIALIZER : JUSTIFICATIF D'ABSENCE (DÉTAIL)
class JustificatifAbsenceDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un justificatif.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='etudiant.matricule', read_only=True)
    duree_jours = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = JustificatifAbsence
        fields = [
            'id',
            'etudiant',
            'etudiant_nom',
            'etudiant_matricule',
            'date_debut',
            'date_fin',
            'duree_jours',
            'type_justificatif',
            'statut',
            'document',
            'document_url',
            'motif',
            'commentaire_validation',
            'date_soumission',
            'date_traitement',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'date_soumission', 'date_traitement', 'created_at', 'updated_at']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_duree_jours(self, obj):
        return obj.calculer_duree()
    
    def get_document_url(self, obj):
        """
        Retourne l'URL complète du document.
        
        Returns:
            str: URL du document ou None
        """
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None

# SERIALIZER : CRÉATION JUSTIFICATIF
class JustificatifAbsenceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer/uploader un nouveau justificatif.
    """
    
    class Meta:
        model = JustificatifAbsence
        fields = [
            'etudiant',
            'date_debut',
            'date_fin',
            'type_justificatif',
            'document',
            'motif',
        ]
    
    def validate(self, data):
        """
        Validation globale des dates.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si dates incohérentes
        
        Returns:
            dict: Données validées
        """
        # Vérifier que date_fin >= date_debut
        if data['date_fin'] < data['date_debut']:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure ou égale à la date de début."
            )
        
        # Vérifier que les dates ne sont pas trop loin dans le passé (> 6 mois)
        from datetime import timedelta
        date_limite = timezone.now().date() - timedelta(days=180)
        if data['date_debut'] < date_limite:
            raise serializers.ValidationError(
                "La date de début ne peut pas être plus de 6 mois dans le passé."
            )
        
        return data

# SERIALIZER : VALIDATION/REJET JUSTIFICATIF
class JustificatifValidationSerializer(serializers.Serializer):
    """
    Serializer pour valider ou rejeter un justificatif.
    
    Format :
    {
        "action": "VALIDER" ou "REJETER",
        "commentaire": "Raison du rejet ou remarque"
    }
    """
    action = serializers.ChoiceField(
        choices=['VALIDER', 'REJETER'],
        help_text="Action à effectuer : VALIDER ou REJETER"
    )
    commentaire = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Commentaire de validation/rejet"
    )
    
    def validate_commentaire(self, value):
        """
        Le commentaire est obligatoire en cas de rejet.
        
        Args:
            value (str): Commentaire
        
        Returns:
            str: Commentaire validé
        """
        action = self.initial_data.get('action')
        if action == 'REJETER' and not value:
            raise serializers.ValidationError(
                "Un commentaire est obligatoire lors du rejet d'un justificatif."
            )
        return value
