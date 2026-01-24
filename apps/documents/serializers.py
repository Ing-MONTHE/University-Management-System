from rest_framework import serializers
from .models import Document, TemplateDocument

# SERIALIZER : DOCUMENT (LISTE)
class DocumentListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des documents (vue simplifiée).
    
    Affiche les informations essentielles pour les listes.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='etudiant.matricule', read_only=True)
    genere_par_nom = serializers.SerializerMethodField()
    fichier_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'etudiant',
            'etudiant_nom',
            'etudiant_matricule',
            'type_document',
            'numero_document',
            'statut',
            'fichier',
            'fichier_url',
            'genere_par',
            'genere_par_nom',
            'date_generation',
            'date_delivrance',
            'created_at',
        ]
        read_only_fields = ['id', 'numero_document', 'created_at']
    
    def get_etudiant_nom(self, obj):
        """Retourne le nom complet de l'étudiant."""
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_genere_par_nom(self, obj):
        """Retourne le nom de la personne qui a généré le document."""
        if obj.genere_par:
            return f"{obj.genere_par.first_name} {obj.genere_par.last_name}"
        return None
    
    def get_fichier_url(self, obj):
        """Retourne l'URL du fichier PDF."""
        if obj.fichier:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None

# SERIALIZER : DOCUMENT (DÉTAIL)
class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un document.
    
    Inclut toutes les informations + relations.
    """
    etudiant_nom = serializers.SerializerMethodField()
    etudiant_matricule = serializers.CharField(source='etudiant.matricule', read_only=True)
    genere_par_nom = serializers.SerializerMethodField()
    delivre_par_nom = serializers.SerializerMethodField()
    fichier_url = serializers.SerializerMethodField()
    inscription_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'etudiant',
            'etudiant_nom',
            'etudiant_matricule',
            'type_document',
            'numero_document',
            'inscription',
            'inscription_details',
            'resultat',
            'paiement',
            'fichier',
            'fichier_url',
            'statut',
            'genere_par',
            'genere_par_nom',
            'date_generation',
            'delivre_par',
            'delivre_par_nom',
            'date_delivrance',
            'qr_code',
            'motif_demande',
            'observations',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'numero_document', 'created_at', 'updated_at']
    
    def get_etudiant_nom(self, obj):
        return f"{obj.etudiant.user.first_name} {obj.etudiant.user.last_name}"
    
    def get_genere_par_nom(self, obj):
        if obj.genere_par:
            return f"{obj.genere_par.first_name} {obj.genere_par.last_name}"
        return None
    
    def get_delivre_par_nom(self, obj):
        if obj.delivre_par:
            return f"{obj.delivre_par.first_name} {obj.delivre_par.last_name}"
        return None
    
    def get_fichier_url(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None
    
    def get_inscription_details(self, obj):
        """Retourne les détails de l'inscription si présente."""
        if obj.inscription:
            return {
                'filiere': obj.inscription.filiere.nom,
                'niveau': obj.inscription.niveau,
                'annee_academique': obj.inscription.annee_academique.nom,
            }
        return None

# SERIALIZER : CRÉATION DOCUMENT
class DocumentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un nouveau document.
    
    Valide que les relations requises sont présentes selon le type.
    """
    
    class Meta:
        model = Document
        fields = [
            'etudiant',
            'type_document',
            'inscription',
            'resultat',
            'paiement',
            'motif_demande',
            'observations',
        ]
    
    def validate(self, data):
        """
        Validation selon le type de document.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si données manquantes
        
        Returns:
            dict: Données validées
        """
        type_document = data.get('type_document')
        
        # Documents nécessitant une inscription
        types_avec_inscription = [
            'ATTESTATION_INSCRIPTION',
            'CERTIFICAT_SCOLARITE',
            'BORDEREAU_INSCRIPTION',
            'CARTE_ETUDIANT',
        ]
        
        if type_document in types_avec_inscription and not data.get('inscription'):
            raise serializers.ValidationError(
                f"Une inscription est requise pour ce type de document ({type_document})."
            )
        
        # Documents nécessitant un résultat
        types_avec_resultat = [
            'RELEVE_NOTES',
            'BULLETIN_NOTES',
            'ATTESTATION_REUSSITE',
        ]
        
        if type_document in types_avec_resultat and not data.get('resultat'):
            raise serializers.ValidationError(
                f"Un résultat est requis pour ce type de document ({type_document})."
            )
        
        # Documents nécessitant un paiement
        if type_document == 'RECU_PAIEMENT' and not data.get('paiement'):
            raise serializers.ValidationError(
                "Un paiement est requis pour générer un reçu."
            )
        
        return data
    
    def create(self, validated_data):
        """
        Crée le document.
        
        Args:
            validated_data (dict): Données validées
        
        Returns:
            Document: Instance créée
        """
        # Le numéro sera généré automatiquement par le modèle
        return Document.objects.create(**validated_data)

# SERIALIZER : GÉNÉRATION DOCUMENT
class DocumentGenerationSerializer(serializers.Serializer):
    """
    Serializer pour générer le PDF d'un document.
    
    Format :
    {
        "document_id": 1
    }
    """
    document_id = serializers.IntegerField(
        help_text="ID du document à générer"
    )
    
    def validate_document_id(self, value):
        """
        Valide que le document existe.
        
        Args:
            value (int): ID du document
        
        Raises:
            ValidationError: Si document inexistant
        
        Returns:
            int: ID validé
        """
        try:
            Document.objects.get(id=value)
        except Document.DoesNotExist:
            raise serializers.ValidationError(
                f"Document avec l'ID {value} non trouvé."
            )
        
        return value

# SERIALIZER : TEMPLATE DOCUMENT (LISTE)
class TemplateDocumentListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des templates (vue simplifiée).
    """
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateDocument
        fields = [
            'id',
            'type_document',
            'nom',
            'description',
            'logo',
            'logo_url',
            'watermark_texte',
            'actif',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_logo_url(self, obj):
        """Retourne l'URL du logo."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

# SERIALIZER : TEMPLATE DOCUMENT (DÉTAIL)
class TemplateDocumentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détails complets d'un template.
    """
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateDocument
        fields = [
            'id',
            'type_document',
            'nom',
            'description',
            'contenu_html',
            'styles_css',
            'entete_html',
            'pied_page_html',
            'logo',
            'logo_url',
            'watermark_texte',
            'actif',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

# SERIALIZER : CRÉATION TEMPLATE
class TemplateDocumentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer/modifier un template.
    
    Valide que le contenu HTML contient les balises de base.
    """
    
    class Meta:
        model = TemplateDocument
        fields = [
            'type_document',
            'nom',
            'description',
            'contenu_html',
            'styles_css',
            'entete_html',
            'pied_page_html',
            'logo',
            'watermark_texte',
            'actif',
        ]
    
    def validate_contenu_html(self, value):
        """
        Valide que le contenu HTML n'est pas vide.
        
        Args:
            value (str): Contenu HTML
        
        Raises:
            ValidationError: Si vide
        
        Returns:
            str: Contenu validé
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Le contenu HTML ne peut pas être vide."
            )
        
        return value

# SERIALIZER : DEMANDE DOCUMENT
class DemandeDocumentSerializer(serializers.Serializer):
    """
    Serializer pour qu'un étudiant demande un document.
    
    Format :
    {
        "type_document": "ATTESTATION_SCOLARITE",
        "motif_demande": "Pour candidature master",
        "inscription_id": 1  (optionnel, selon le type)
    }
    """
    type_document = serializers.ChoiceField(
        choices=Document.TypeDocument.choices,
        help_text="Type de document demandé"
    )
    motif_demande = serializers.CharField(
        help_text="Motif de la demande"
    )
    inscription_id = serializers.IntegerField(
        required=False,
        help_text="ID de l'inscription (si applicable)"
    )
    resultat_id = serializers.IntegerField(
        required=False,
        help_text="ID du résultat (si applicable)"
    )
    
    def validate(self, data):
        """
        Validation selon le type de document demandé.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si données manquantes
        
        Returns:
            dict: Données validées
        """
        type_document = data['type_document']
        
        # Vérifier si inscription requise
        types_avec_inscription = [
            'ATTESTATION_INSCRIPTION',
            'CERTIFICAT_SCOLARITE',
            'BORDEREAU_INSCRIPTION',
            'CARTE_ETUDIANT',
        ]
        
        if type_document in types_avec_inscription and not data.get('inscription_id'):
            raise serializers.ValidationError(
                "L'ID de l'inscription est requis pour ce type de document."
            )
        
        # Vérifier si résultat requis
        types_avec_resultat = [
            'RELEVE_NOTES',
            'BULLETIN_NOTES',
            'ATTESTATION_REUSSITE',
        ]
        
        if type_document in types_avec_resultat and not data.get('resultat_id'):
            raise serializers.ValidationError(
                "L'ID du résultat est requis pour ce type de document."
            )
        
        return data

# SERIALIZER : VÉRIFICATION DOCUMENT
class VerificationDocumentSerializer(serializers.Serializer):
    """
    Serializer pour vérifier l'authenticité d'un document via QR code.
    
    Format :
    {
        "qr_code": "abc123xyz...",
        "numero_document": "ATT-SCO-2026-000123"
    }
    """
    qr_code = serializers.CharField(
        help_text="Code QR du document"
    )
    numero_document = serializers.CharField(
        help_text="Numéro du document"
    )
    
    def validate(self, data):
        """
        Valide que le document existe et que le QR code correspond.
        
        Args:
            data (dict): Données à valider
        
        Raises:
            ValidationError: Si document invalide
        
        Returns:
            dict: Données validées
        """
        try:
            document = Document.objects.get(numero_document=data['numero_document'])
        except Document.DoesNotExist:
            raise serializers.ValidationError(
                "Document non trouvé avec ce numéro."
            )
        
        # Vérifier le QR code
        if document.qr_code != data['qr_code']:
            raise serializers.ValidationError(
                "Le code QR ne correspond pas à ce document. Document potentiellement falsifié."
            )
        
        # Vérifier que le document n'est pas annulé
        if document.statut == 'ANNULE':
            raise serializers.ValidationError(
                "Ce document a été annulé et n'est plus valide."
            )
        
        # Ajouter le document validé au contexte
        data['document'] = document
        
        return data
