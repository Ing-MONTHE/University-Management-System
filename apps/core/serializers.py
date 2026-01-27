# SERIALIZERS.PY - Conversion Models ↔ JSON

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, Role, Permission, AuditLog

# PERMISSION SERIALIZER
class PermissionSerializer(serializers.ModelSerializer):
    # Convertit Permission en JSON.
    # Utilisé pour lire/créer/modifier des permissions.
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'description', 'category', 'created_at']
        read_only_fields = ['id', 'created_at']

# ROLE SERIALIZER
class RoleSerializer(serializers.ModelSerializer):
    # Convertit Role en JSON.
    # Inclut les permissions et le nombre d'utilisateurs.
    
    # Inclure les détails des permissions
    permissions = PermissionSerializer(many=True, read_only=True)
    
    # IDs des permissions (pour créer/modifier)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions',
        required=False
    )
    
    # Nombre d'utilisateurs ayant ce rôle
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'permissions', 'permission_ids',
            'users_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'users_count']
    
    def get_users_count(self, obj):
        # Compter le nombre d'utilisateurs.
        return obj.users.count()
    
    def create(self, validated_data):
        # Créer un rôle avec ses permissions.
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        if permissions:
            role.permissions.set(permissions)
        return role
    
    def update(self, instance, validated_data):
        # Mettre à jour un rôle.
        permissions = validated_data.pop('permissions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if permissions is not None:
            instance.permissions.set(permissions)
        return instance

# USER SERIALIZER (Lecture)
class UserSerializer(serializers.ModelSerializer):
    # Pour LIRE les utilisateurs.
    # N'expose PAS le mot de passe.
    
    roles = RoleSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    all_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'uuid', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'is_staff', 'is_superuser',
            'roles', 'all_permissions', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_all_permissions(self, obj):
        # Obtenir toutes les permissions de l'utilisateur.
        permissions = set()
        for role in obj.roles.all():
            permissions.update(role.permissions.values_list('code', flat=True))
        return list(permissions)

# USER CREATE SERIALIZER
class UserCreateSerializer(serializers.ModelSerializer):
    # Pour CRÉER un utilisateur.
    # Valide le mot de passe et demande confirmation.
    
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        many=True,
        write_only=True,
        source='roles',
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'role_ids', 'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }
    
    def validate(self, attrs):
        # Valider que les mots de passe correspondent.
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': "Les mots de passe ne correspondent pas"
            })
        
        # Valider la force du mot de passe
        validate_password(attrs.get('password'))
        
        attrs.pop('password_confirm')
        return attrs
    
    def create(self, validated_data):
        # Créer l'utilisateur avec mot de passe hashé.
        roles = validated_data.pop('roles', [])
        user = User.objects.create_user(**validated_data)
        if roles:
            user.roles.set(roles)
        return user

# USER UPDATE SERIALIZER
class UserUpdateSerializer(serializers.ModelSerializer):
    # Pour MODIFIER un utilisateur.
    # Ne permet PAS de changer le mot de passe (utilisez ChangePasswordSerializer).
    
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        many=True,
        write_only=True,
        source='roles',
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role_ids', 'is_active']
    
    def update(self, instance, validated_data):
        # Mettre à jour l'utilisateur.
        roles = validated_data.pop('roles', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if roles is not None:
            instance.roles.set(roles)
        return instance

# CHANGE PASSWORD SERIALIZER
class ChangePasswordSerializer(serializers.Serializer):
    # Pour changer le mot de passe.
    # Demande l'ancien mot de passe pour sécurité.
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        # Vérifier que l'ancien mot de passe est correct.
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect")
        return value
    
    def validate(self, attrs):
        # Vérifier que les nouveaux mots de passe correspondent.
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "Les mots de passe ne correspondent pas"
            })
        validate_password(attrs['new_password'])
        return attrs
    
    def save(self):
        # Sauvegarder le nouveau mot de passe.
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# AUDIT LOG SERIALIZER
class AuditLogSerializer(serializers.ModelSerializer):
    # Pour lire les logs d'audit.
    # Tout est en lecture seule (on ne modifie jamais les logs).
    
    user_details = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_details', 'action', 'action_display',
            'table_name', 'object_id', 'details', 'ip_address',
            'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'user', 'action', 'table_name', 'object_id','details', 'ip_address', 'user_agent', 'timestamp']
    
    def get_user_details(self, obj):
        # Obtenir les détails de l'utilisateur.
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return None

# LOGIN SERIALIZER (JWT)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer JWT personnalisé qui retourne aussi les infos utilisateur
    """
    
    def validate(self, attrs):
        # Appeler la validation de base (génère les tokens)
        data = super().validate(attrs)
        
        # Ajouter les infos utilisateur avec UserSerializer
        user_data = UserSerializer(self.user).data
        
        # Retourner tokens + user
        data['user'] = user_data
        
        return data