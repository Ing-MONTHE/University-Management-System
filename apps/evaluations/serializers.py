# Sérialisation des modèles d'évaluations

from rest_framework import serializers
from .models import TypeEvaluation, Evaluation, Note, Resultat, SessionDeliberation, MembreJury, DecisionJury
from apps.academic.serializers import MatiereSimpleSerializer, AnneeAcademiqueSerializer
from apps.students.models import Etudiant

# TYPE EVALUATION SERIALIZER
class TypeEvaluationSerializer(serializers.ModelSerializer):
    """
    Serializer pour Type d'évaluation.
    """
    
    code_display = serializers.CharField(source='get_code_display', read_only=True)
    
    class Meta:
        model = TypeEvaluation
        fields = [
            'id', 'code', 'code_display', 'nom',
            'coefficient_min', 'coefficient_max',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# EVALUATION SERIALIZER
class EvaluationSerializer(serializers.ModelSerializer):
    """
    Serializer pour Évaluation.
    """
    
    # Détails
    matiere_details = MatiereSimpleSerializer(source='matiere', read_only=True)
    type_evaluation_details = TypeEvaluationSerializer(source='type_evaluation', read_only=True)
    annee_academique_details = AnneeAcademiqueSerializer(source='annee_academique', read_only=True)
    
    # IDs pour création
    matiere_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['Matiere']).Matiere.objects.all(),
        source='matiere',
        write_only=True
    )
    
    type_evaluation_id = serializers.PrimaryKeyRelatedField(
        queryset=TypeEvaluation.objects.all(),
        source='type_evaluation',
        write_only=True
    )
    
    annee_academique_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['AnneeAcademique']).AnneeAcademique.objects.all(),
        source='annee_academique',
        write_only=True
    )
    
    # Statistiques
    moyenne_classe = serializers.SerializerMethodField()
    nombre_presents = serializers.SerializerMethodField()
    nombre_absents = serializers.SerializerMethodField()
    
    class Meta:
        model = Evaluation
        fields = [
            'id', 'matiere', 'matiere_id', 'matiere_details',
            'type_evaluation', 'type_evaluation_id', 'type_evaluation_details',
            'annee_academique', 'annee_academique_id', 'annee_academique_details',
            'titre', 'date', 'coefficient', 'note_totale', 'duree',
            'description', 'moyenne_classe', 'nombre_presents',
            'nombre_absents', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    validators = [
            serializers.UniqueTogetherValidator(
                queryset=Evaluation.objects.all(),
                fields=['matiere_id', 'titre', 'annee_academique_id'],
                message="Une évaluation avec ce titre existe déjà pour cette matière et année académique."
            )
        ]
    
    def get_moyenne_classe(self, obj):
        # Moyenne de la classe.
        return round(obj.get_moyenne_classe(), 2)
    
    def get_nombre_presents(self, obj):
        # Nombre de présents.
        return obj.get_nombre_presents()
    
    def get_nombre_absents(self, obj):
        # Nombre d'absents.
        return obj.get_nombre_absents()
    
    def validate(self, attrs):
        # Validation des données.
        # Vérifier que le coefficient est dans la plage autorisée
        type_eval = attrs.get('type_evaluation')
        coefficient = attrs.get('coefficient')
        
        if type_eval and coefficient:
            if coefficient < type_eval.coefficient_min or coefficient > type_eval.coefficient_max:
                raise serializers.ValidationError({
                    'coefficient': f'Le coefficient doit être entre {type_eval.coefficient_min} et {type_eval.coefficient_max} pour ce type d\'évaluation'
                })
        
        return attrs

# NOTE SERIALIZER (Simple)
class NoteSimpleSerializer(serializers.ModelSerializer):
    """
    Version simple du serializer Note.
    """
    
    note_sur_20 = serializers.SerializerMethodField()
    appreciation_auto = serializers.SerializerMethodField()
    
    class Meta:
        model = Note
        fields = [
            'id', 'note_obtenue', 'note_sur', 'note_sur_20',
            'appreciations', 'appreciation_auto', 'absence',
            'date_saisie'
        ]
        read_only_fields = ['id', 'date_saisie']
    
    def get_note_sur_20(self, obj):
        """Note convertie sur 20."""
        return round(obj.get_note_sur_20(), 2)
    
    def get_appreciation_auto(self, obj):
        """Appréciation automatique."""
        return obj.get_appreciation_auto()

# NOTE SERIALIZER (Complet)
class NoteSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour Note.
    """
    
    # Détails
    evaluation_details = EvaluationSerializer(source='evaluation', read_only=True)
    
    # Infos étudiant
    etudiant_info = serializers.SerializerMethodField()
    
    # IDs pour création
    evaluation_id = serializers.PrimaryKeyRelatedField(
        queryset=Evaluation.objects.all(),
        source='evaluation',
        write_only=True
    )
    
    etudiant_id = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(),
        source='etudiant',
        write_only=True
    )
    
    # Calculs
    note_sur_20 = serializers.SerializerMethodField()
    appreciation_auto = serializers.SerializerMethodField()
    
    class Meta:
        model = Note
        fields = [
            'id', 'evaluation', 'evaluation_id', 'evaluation_details',
            'etudiant', 'etudiant_id', 'etudiant_info',
            'note_obtenue', 'note_sur', 'note_sur_20',
            'appreciations', 'appreciation_auto', 'absence',
            'date_saisie', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_saisie', 'created_at', 'updated_at']
    
    def get_etudiant_info(self, obj):
        """Informations de l'étudiant."""
        return {
            'id': obj.etudiant.id,
            'matricule': obj.etudiant.matricule,
            'nom_complet': obj.etudiant.user.get_full_name()
        }
    
    def get_note_sur_20(self, obj):
        """Note convertie sur 20."""
        return round(obj.get_note_sur_20(), 2)
    
    def get_appreciation_auto(self, obj):
        """Appréciation automatique."""
        return obj.get_appreciation_auto()
    
    def validate(self, attrs):
        """Validation des données."""
        note_obtenue = attrs.get('note_obtenue')
        note_sur = attrs.get('note_sur')
        absence = attrs.get('absence', False)
        
        # Si absent, pas de note
        if absence and note_obtenue is not None:
            raise serializers.ValidationError({
                'note_obtenue': 'Un étudiant absent ne peut pas avoir de note'
            })
        
        # Si présent, note obligatoire
        if not absence and note_obtenue is None:
            raise serializers.ValidationError({
                'note_obtenue': 'La note est obligatoire si l\'étudiant n\'est pas absent'
            })
        
        # Note ne doit pas dépasser le barème
        if note_obtenue is not None and note_sur is not None:
            if note_obtenue > note_sur:
                raise serializers.ValidationError({
                    'note_obtenue': f'La note ne peut pas dépasser {note_sur}'
                })
            if note_obtenue < 0:
                raise serializers.ValidationError({
                    'note_obtenue': 'La note ne peut pas être négative'
                })
        
        return attrs

# RESULTAT SERIALIZER
class ResultatSerializer(serializers.ModelSerializer):
    """
    Serializer pour Résultat.
    """
    
    # Infos étudiant
    etudiant_info = serializers.SerializerMethodField()
    
    # Détails
    matiere_details = MatiereSimpleSerializer(source='matiere', read_only=True)
    annee_academique_details = AnneeAcademiqueSerializer(source='annee_academique', read_only=True)
    
    # IDs pour création
    etudiant_id = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(),
        source='etudiant',
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
    
    # Display
    mention_display = serializers.CharField(source='get_mention_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Resultat
        fields = [
            'id', 'etudiant', 'etudiant_id', 'etudiant_info',
            'matiere', 'matiere_id', 'matiere_details',
            'annee_academique', 'annee_academique_id', 'annee_academique_details',
            'moyenne_generale', 'mention', 'mention_display',
            'statut', 'statut_display', 'credits_obtenus', 'rang',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'mention', 'statut', 'credits_obtenus', 'created_at', 'updated_at']
    
    def get_etudiant_info(self, obj):
        """Informations de l'étudiant."""
        return {
            'id': obj.etudiant.id,
            'matricule': obj.etudiant.matricule,
            'nom_complet': obj.etudiant.user.get_full_name()
        }

# SAISIE MULTIPLE DE NOTES
class SaisieMultipleNotesSerializer(serializers.Serializer):
    """
    Serializer pour saisir plusieurs notes en une fois.
    """
    
    evaluation_id = serializers.IntegerField()
    notes = serializers.ListField(
        child=serializers.DictField(),
        help_text="Liste des notes : [{etudiant_id, note_obtenue, absence, appreciations}]"
    )
    
    def validate_notes(self, value):
        """Valider le format des notes."""
        for note in value:
            if 'etudiant_id' not in note:
                raise serializers.ValidationError("Chaque note doit avoir un etudiant_id")
            
            absence = note.get('absence', False)
            note_obtenue = note.get('note_obtenue')
            
            if not absence and note_obtenue is None:
                raise serializers.ValidationError(
                    f"La note est obligatoire pour l'étudiant {note['etudiant_id']} s'il n'est pas absent"
                )
        
        return value

# SESSION DELIBERATION SERIALIZER
class SessionDeliberationSerializer(serializers.ModelSerializer):
    """
    Serializer pour Session de délibération.
    """
    
    # Détails
    annee_academique_details = AnneeAcademiqueSerializer(source='annee_academique', read_only=True)
    filiere_details = serializers.SerializerMethodField()
    
    # IDs pour création
    annee_academique_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['AnneeAcademique']).AnneeAcademique.objects.all(),
        source='annee_academique',
        write_only=True
    )
    
    filiere_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.academic.models', fromlist=['Filiere']).Filiere.objects.all(),
        source='filiere',
        write_only=True
    )
    
    # Display
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    # Statistiques
    nombre_etudiants = serializers.SerializerMethodField()
    taux_reussite = serializers.SerializerMethodField()
    nombre_membres_jury = serializers.SerializerMethodField()
    
    class Meta:
        model = SessionDeliberation
        fields = [
            'id', 'annee_academique', 'annee_academique_id', 'annee_academique_details',
            'filiere', 'filiere_id', 'filiere_details',
            'niveau', 'semestre', 'semestre_display', 'date_deliberation',
            'lieu', 'president_jury', 'statut', 'statut_display',
            'proces_verbal', 'nombre_etudiants', 'taux_reussite',
            'nombre_membres_jury', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    validators = [
            serializers.UniqueTogetherValidator(
                queryset=SessionDeliberation.objects.all(),
                fields=['annee_academique_id', 'filiere_id', 'niveau', 'semestre'],
                message="Une session existe déjà pour cette filière, niveau et semestre."
            )
        ]
    
    def get_filiere_details(self, obj):
        """Détails de la filière."""
        return {
            'id': obj.filiere.id,
            'code': obj.filiere.code,
            'nom': obj.filiere.nom
        }
    
    def get_nombre_etudiants(self, obj):
        """Nombre d'étudiants."""
        return obj.get_nombre_etudiants()
    
    def get_taux_reussite(self, obj):
        """Taux de réussite."""
        return obj.get_taux_reussite()
    
    def get_nombre_membres_jury(self, obj):
        """Nombre de membres du jury."""
        return obj.membres_jury.count()

# MEMBRE JURY SERIALIZER
class MembreJurySerializer(serializers.ModelSerializer):
    """
    Serializer pour Membre du jury.
    """
    
    # Détails session
    session_details = SessionDeliberationSerializer(source='session', read_only=True)
    
    # Infos enseignant
    enseignant_info = serializers.SerializerMethodField()
    
    # IDs pour création
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=SessionDeliberation.objects.all(),
        source='session',
        write_only=True
    )
    
    enseignant_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.students.models', fromlist=['Enseignant']).Enseignant.objects.all(),
        source='enseignant',
        write_only=True
    )
    
    # Display
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = MembreJury
        fields = [
            'id', 'session', 'session_id', 'session_details',
            'enseignant', 'enseignant_id', 'enseignant_info',
            'role', 'role_display', 'present',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_enseignant_info(self, obj):
        """Informations de l'enseignant."""
        return {
            'id': obj.enseignant.id,
            'matricule': obj.enseignant.matricule,
            'nom_complet': obj.enseignant.user.get_full_name(),
            'grade': obj.enseignant.get_grade_display()
        }

# DECISION JURY SERIALIZER
class DecisionJurySerializer(serializers.ModelSerializer):
    """
    Serializer pour Décision du jury.
    """
    
    # Détails session
    session_details = SessionDeliberationSerializer(source='session', read_only=True)
    
    # Infos étudiant
    etudiant_info = serializers.SerializerMethodField()
    
    # IDs pour création
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=SessionDeliberation.objects.all(),
        source='session',
        write_only=True
    )
    
    etudiant_id = serializers.PrimaryKeyRelatedField(
        queryset=Etudiant.objects.all(),
        source='etudiant',
        write_only=True
    )
    
    # Display
    decision_display = serializers.CharField(source='get_decision_display', read_only=True)
    mention_display = serializers.CharField(source='get_mention_display', read_only=True)
    
    # Calculs
    taux_credits = serializers.SerializerMethodField()
    
    class Meta:
        model = DecisionJury
        fields = [
            'id', 'session', 'session_id', 'session_details',
            'etudiant', 'etudiant_id', 'etudiant_info',
            'moyenne_generale', 'total_credits_obtenus',
            'total_credits_requis', 'taux_credits',
            'decision', 'decision_display', 'mention', 'mention_display',
            'rang_classe', 'observations',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'mention', 'created_at', 'updated_at']
    
    def get_etudiant_info(self, obj):
        """Informations de l'étudiant."""
        return {
            'id': obj.etudiant.id,
            'matricule': obj.etudiant.matricule,
            'nom_complet': obj.etudiant.user.get_full_name()
        }
    
    def get_taux_credits(self, obj):
        """Taux de crédits obtenus."""
        return obj.get_taux_credits()

# GENERATION DECISIONS SERIALIZER
class GenerationDecisionsSerializer(serializers.Serializer):
    """
    Serializer pour générer automatiquement les décisions.
    """
    
    session_id = serializers.IntegerField()
    seuil_admission = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
        help_text="Seuil de moyenne pour être admis (défaut: 10)"
    )
    seuil_rattrapage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=7.0,
        help_text="Seuil de moyenne pour le rattrapage (défaut: 7)"
    )