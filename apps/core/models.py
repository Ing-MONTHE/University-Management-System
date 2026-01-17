# Modèles du module CORE
# Contient : User, Role, Permission, AuditLog

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import EmailValidator
from django.utils import timezone
import uuid


# MANAGER PERSONNALISÉ POUR USER
class UserManager(BaseUserManager):
    # Manager pour créer des utilisateurs.
    # Django a besoin de savoir comment créer users et superusers.
    def create_user(self, username, email, password=None, **extra_fields):
        # Créer un utilisateur normal.
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire")
        
        if not email:
            raise ValueError("L'email est obligatoire")
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        # Créer un superutilisateur (admin).
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


# MODÈLE USER
class User(AbstractBaseUser, PermissionsMixin):
    # Modèle utilisateur personnalisé.
    # Chaque personne (étudiant, enseignant, admin) a UN compte User.
    # UUID unique
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID"
    )
    
    # Login
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nom d'utilisateur"
    )
    
    # Email
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name="Email"
    )
    
    # Informations personnelles
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Nom")
    
    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    # Relation avec Role (sera créée plus bas)
    roles = models.ManyToManyField('Role', related_name='users', blank=True)
    
    # Configuration
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'core_users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def get_full_name(self):
        # Retourner le nom complet.
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission_code):
        # Vérifier si l'utilisateur a une permission.
        if self.is_superuser:
            return True
        for role in self.roles.all():
            if role.permissions.filter(code=permission_code).exists():
                return True
        return False

# MODÈLE PERMISSION
class Permission(models.Model):
    # Une permission = une action autorisée.
    # Exemples: create_student, view_grades, manage_payments
    
    name = models.CharField(max_length=100, verbose_name="Nom")
    code = models.CharField(max_length=100, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    category = models.CharField(max_length=50, blank=True, verbose_name="Catégorie")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# MODÈLE ROLE
class Role(models.Model):
    # Un rôle = groupe de permissions.
    # Exemples: Enseignant, Étudiant, Admin Académique
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_roles'
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def add_permission(self, permission):
        # Ajouter une permission à ce rôle.
        self.permissions.add(permission)
    
    def remove_permission(self, permission):
        # Retirer une permission de ce rôle.
        self.permissions.remove(permission)

# MODÈLE AUDITLOG
class AuditLog(models.Model):
    # Journal d'audit - Enregistre toutes les actions.
    # Qui a fait quoi et quand.
    
    class ActionChoices(models.TextChoices):
        CREATE = 'CREATE', 'Création'
        UPDATE = 'UPDATE', 'Modification'
        DELETE = 'DELETE', 'Suppression'
        LOGIN = 'LOGIN', 'Connexion'
        LOGOUT = 'LOGOUT', 'Déconnexion'
        VIEW = 'VIEW', 'Consultation'
        EXPORT = 'EXPORT', 'Export'
        IMPORT = 'IMPORT', 'Import'
        OTHER = 'OTHER', 'Autre'
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="Utilisateur"
    )
    action = models.CharField(max_length=20, choices=ActionChoices.choices, verbose_name="Action")
    table_name = models.CharField(max_length=100, verbose_name="Table")
    object_id = models.CharField(max_length=100, blank=True, verbose_name="ID objet")
    details = models.JSONField(default=dict, blank=True, verbose_name="Détails")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.CharField(max_length=255, blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date/Heure", db_index=True)
    
    class Meta:
        db_table = 'core_audit_logs'
        verbose_name = 'Log d\'audit'
        verbose_name_plural = 'Logs d\'audit'
        ordering = ['-timestamp']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Système'
        return f"{user_str} - {self.action} - {self.table_name}"
    
    @classmethod
    def log_action(cls, user, action, table_name, object_id=None, details=None, 
                   ip_address=None, user_agent=None):
        # Créer un log d'audit.
        return cls.objects.create(
            user=user,
            action=action,
            table_name=table_name,
            object_id=object_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )