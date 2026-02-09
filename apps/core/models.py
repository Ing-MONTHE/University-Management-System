from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
import re


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATORS PERSONNALISÉS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_username(value):
    """
    Valide le format du nom d'utilisateur.
    - 3 à 150 caractères
    - Lettres, chiffres, tirets, underscores uniquement
    """
    if len(value) < 3:
        raise ValidationError(
            "Le nom d'utilisateur doit contenir au moins 3 caractères.",
            code='username_too_short'
        )
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValidationError(
            "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores.",
            code='username_invalid_chars'
        )


def validate_permission_code(value):
    """
    Valide le format du code de permission.
    Format: module.action (ex: students.create, evaluations.view)
    """
    if not re.match(r'^[a-z_]+\.[a-z_]+$', value):
        raise ValidationError(
            "Le code de permission doit être au format 'module.action' (ex: students.create).",
            code='permission_code_invalid'
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE DE BASE ABSTRAIT
# ═══════════════════════════════════════════════════════════════════════════════

class BaseModel(models.Model):
    """
    Modèle abstrait de base pour tous les modèles de l'application.
    
    Ajoute automatiquement :
    - created_at : Date de création
    - updated_at : Date de dernière modification
    - Index sur created_at et updated_at
    
    Méthodes utilitaires :
    - is_recent() : Vérifie si créé dans les dernières 24h
    - age_in_days() : Nombre de jours depuis création
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
        help_text="Date et heure de création de l'enregistrement",
        db_index=True  # Index pour tri et filtrage
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification",
        help_text="Date et heure de la dernière modification",
        db_index=True  # Index pour tri et filtrage
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='%(app_label)s_%(class)s_created_idx'),
            models.Index(fields=['-updated_at'], name='%(app_label)s_%(class)s_updated_idx'),
        ]
    
    @property
    def is_recent(self):
        """Vérifie si l'objet a été créé dans les dernières 24 heures."""
        return (timezone.now() - self.created_at).days == 0
    
    @property
    def age_in_days(self):
        """Retourne l'âge de l'objet en jours."""
        return (timezone.now() - self.created_at).days
    
    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.pk} created={self.created_at}>"


# ═══════════════════════════════════════════════════════════════════════════════
# MANAGER PERSONNALISÉ POUR USER
# ═══════════════════════════════════════════════════════════════════════════════

class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User.
    
    Méthodes :
    - create_user() : Créer un utilisateur normal
    - create_superuser() : Créer un superutilisateur
    - get_active() : Récupérer tous les utilisateurs actifs
    - get_staff() : Récupérer tous les staff
    - search() : Rechercher par nom, email, username
    """
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Créer et sauvegarder un utilisateur normal."""
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
        """Créer et sauvegarder un superutilisateur."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)
    
    def get_active(self):
        """Récupérer tous les utilisateurs actifs."""
        return self.filter(is_active=True)
    
    def get_staff(self):
        """Récupérer tous les membres du staff."""
        return self.filter(is_staff=True, is_active=True)
    
    def search(self, query):
        """
        Rechercher des utilisateurs par nom, email ou username.
        
        Args:
            query (str): Terme de recherche
            
        Returns:
            QuerySet: Utilisateurs correspondants
        """
        return self.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE USER
# ═══════════════════════════════════════════════════════════════════════════════

class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé.
    
    Chaque personne (étudiant, enseignant, admin) a UN compte User.
    
    Optimisations :
    - Index sur username, email, uuid
    - Index composite (is_active, is_staff)
    - Validators personnalisés
    - Méthodes utilitaires (get_full_name, has_permission, etc.)
    """
    
    # UUID unique
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID",
        db_index=True  # Index pour recherches par UUID
    )
    
    # Login
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nom d'utilisateur",
        validators=[validate_username],
        db_index=True  # Index pour authentification
    )
    
    # Email
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Format d'email invalide")],
        verbose_name="Email",
        db_index=True  # Index pour recherches
    )
    
    # Informations personnelles
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Prénom",
        db_index=True  # Index pour recherches et tri
    )
    
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nom",
        db_index=True  # Index pour recherches et tri
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        db_index=True  # Index pour filtrage
    )
    
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff",
        db_index=True  # Index pour filtrage
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le",
        db_index=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    # Dernière connexion (tracking)
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP dernière connexion"
    )
    
    # Relation avec Role
    roles = models.ManyToManyField(
        'Role',
        related_name='users',
        blank=True,
        verbose_name="Rôles"
    )
    
    # Configuration
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'core_users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']
        indexes = [
            # Index composites pour requêtes fréquentes
            models.Index(fields=['is_active', 'is_staff'], name='core_user_active_staff_idx'),
            models.Index(fields=['last_name', 'first_name'], name='core_user_name_idx'),
            models.Index(fields=['-created_at'], name='core_user_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def __repr__(self):
        return f"<User {self.username} id={self.pk} active={self.is_active}>"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def initials(self):
        """Retourne les initiales de l'utilisateur."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[0].upper()
    
    @property
    def has_profile(self):
        """Vérifie si l'utilisateur a un profil étudiant ou enseignant."""
        return hasattr(self, 'etudiant') or hasattr(self, 'enseignant')
    
    @property
    def profile_type(self):
        """Retourne le type de profil (étudiant, enseignant, admin)."""
        if hasattr(self, 'etudiant'):
            return 'ETUDIANT'
        elif hasattr(self, 'enseignant'):
            return 'ENSEIGNANT'
        elif self.is_staff:
            return 'ADMIN'
        return 'UTILISATEUR'
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTHODES
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_full_name(self):
        """Retourne le nom complet (méthode Django standard)."""
        return self.full_name
    
    def get_short_name(self):
        """Retourne le prénom ou username."""
        return self.first_name or self.username
    
    def has_permission(self, permission_code):
        """
        Vérifie si l'utilisateur a une permission spécifique.
        
        Args:
            permission_code (str): Code de la permission (ex: 'students.create')
            
        Returns:
            bool: True si l'utilisateur a la permission
        """
        # Superuser a toutes les permissions
        if self.is_superuser:
            return True
        
        # Vérifier dans les rôles
        return self.roles.filter(
            is_active=True,
            permissions__code=permission_code
        ).exists()
    
    def has_any_permission(self, *permission_codes):
        """
        Vérifie si l'utilisateur a au moins une des permissions.
        
        Args:
            *permission_codes: Codes de permissions
            
        Returns:
            bool: True si au moins une permission
        """
        if self.is_superuser:
            return True
        
        return self.roles.filter(
            is_active=True,
            permissions__code__in=permission_codes
        ).exists()
    
    def get_all_permissions(self):
        """
        Retourne toutes les permissions de l'utilisateur.
        
        Returns:
            QuerySet: Permissions de l'utilisateur
        """
        if self.is_superuser:
            return Permission.objects.all()
        
        from django.db.models import Prefetch
        return Permission.objects.filter(
            roles__in=self.roles.filter(is_active=True)
        ).distinct()
    
    def add_role(self, role):
        """Ajouter un rôle à l'utilisateur."""
        self.roles.add(role)
    
    def remove_role(self, role):
        """Retirer un rôle de l'utilisateur."""
        self.roles.remove(role)
    
    def activate(self):
        """Activer le compte utilisateur."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
    
    def deactivate(self):
        """Désactiver le compte utilisateur."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE PERMISSION
# ═══════════════════════════════════════════════════════════════════════════════

class Permission(models.Model):
    """
    Modèle de permission.
    
    Une permission = une action autorisée.
    Exemples: students.create, evaluations.view, finance.manage_payments
    
    Optimisations :
    - Index sur code (unique)
    - Index composite (category, name)
    - Validator pour format du code
    - Méthodes de requête par catégorie
    """
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nom",
        help_text="Nom descriptif de la permission",
        db_index=True
    )
    
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Code",
        help_text="Code unique (format: module.action)",
        validators=[validate_permission_code],
        db_index=True  # Index pour recherches rapides
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description détaillée de la permission"
    )
    
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Catégorie",
        help_text="Catégorie de la permission (ex: academic, finance)",
        db_index=True  # Index pour filtrage par catégorie
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    class Meta:
        db_table = 'core_permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'name'], name='core_perm_cat_name_idx'),
            models.Index(fields=['code'], name='core_perm_code_idx'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def __repr__(self):
        return f"<Permission {self.code} category={self.category}>"
    
    @property
    def module(self):
        """Retourne le module de la permission (partie avant le point)."""
        return self.code.split('.')[0] if '.' in self.code else ''
    
    @property
    def action(self):
        """Retourne l'action de la permission (partie après le point)."""
        return self.code.split('.')[1] if '.' in self.code else self.code
    
    @classmethod
    def get_by_category(cls, category):
        """Récupérer toutes les permissions d'une catégorie."""
        return cls.objects.filter(category=category)
    
    @classmethod
    def get_by_module(cls, module):
        """Récupérer toutes les permissions d'un module."""
        return cls.objects.filter(code__startswith=f"{module}.")


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE ROLE
# ═══════════════════════════════════════════════════════════════════════════════

class Role(models.Model):
    """
    Modèle de rôle.
    
    Un rôle = groupe de permissions.
    Exemples: Enseignant, Étudiant, Admin Académique, Comptable
    
    Optimisations :
    - Index sur name (unique)
    - Index sur is_active
    - Méthodes de gestion des permissions
    - Comptage des utilisateurs
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom",
        db_index=True
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True,
        verbose_name="Permissions"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        db_index=True  # Index pour filtrage
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    class Meta:
        db_table = 'core_roles'
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name'], name='core_role_active_name_idx'),
        ]
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"<Role {self.name} active={self.is_active} perms={self.permissions.count()}>"
    
    @property
    def users_count(self):
        """Nombre d'utilisateurs ayant ce rôle."""
        return self.users.count()
    
    @property
    def permissions_count(self):
        """Nombre de permissions dans ce rôle."""
        return self.permissions.count()
    
    def add_permission(self, permission):
        """Ajouter une permission à ce rôle."""
        self.permissions.add(permission)
    
    def remove_permission(self, permission):
        """Retirer une permission de ce rôle."""
        self.permissions.remove(permission)
    
    def has_permission(self, permission_code):
        """Vérifie si le rôle a une permission spécifique."""
        return self.permissions.filter(code=permission_code).exists()
    
    def get_permissions_by_category(self, category):
        """Récupérer les permissions d'une catégorie."""
        return self.permissions.filter(category=category)
    
    @classmethod
    def get_active(cls):
        """Récupérer tous les rôles actifs."""
        return cls.objects.filter(is_active=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE AUDITLOG
# ═══════════════════════════════════════════════════════════════════════════════

class AuditLog(models.Model):
    """
    Journal d'audit - Enregistre toutes les actions.
    
    Optimisations :
    - Index sur timestamp (pour recherches chronologiques)
    - Index composite (user, action, timestamp)
    - Index composite (table_name, action)
    - Méthode de création simplifiée
    - Méthodes de requête par période
    """
    
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
        verbose_name="Utilisateur",
        db_index=True  # Index pour filtrage par utilisateur
    )
    
    action = models.CharField(
        max_length=20,
        choices=ActionChoices.choices,
        verbose_name="Action",
        db_index=True  # Index pour filtrage par action
    )
    
    table_name = models.CharField(
        max_length=100,
        verbose_name="Table",
        db_index=True  # Index pour filtrage par table
    )
    
    object_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID objet",
        db_index=True  # Index pour retrouver les actions sur un objet
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Détails"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP",
        db_index=True  # Index pour recherches par IP
    )
    
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="User Agent"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date/Heure",
        db_index=True  # Index crucial pour recherches chronologiques
    )
    
    class Meta:
        db_table = 'core_audit_logs'
        verbose_name = 'Log d\'audit'
        verbose_name_plural = 'Logs d\'audit'
        ordering = ['-timestamp']
        indexes = [
            # Index composites pour requêtes fréquentes
            models.Index(fields=['user', 'action', '-timestamp'], name='core_audit_user_action_idx'),
            models.Index(fields=['table_name', 'action'], name='core_audit_table_action_idx'),
            models.Index(fields=['table_name', 'object_id'], name='core_audit_table_obj_idx'),
            models.Index(fields=['-timestamp'], name='core_audit_timestamp_idx'),
            models.Index(fields=['ip_address', '-timestamp'], name='core_audit_ip_time_idx'),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Système'
        return f"{user_str} - {self.action} - {self.table_name}"
    
    def __repr__(self):
        return f"<AuditLog {self.action} table={self.table_name} user={self.user_id} time={self.timestamp}>"
    
    @classmethod
    def log_action(cls, user, action, table_name, object_id=None, details=None, 
                   ip_address=None, user_agent=None):
        """
        Créer un log d'audit (méthode simplifiée).
        
        Args:
            user: Utilisateur effectuant l'action
            action: Type d'action (CREATE, UPDATE, etc.)
            table_name: Nom de la table concernée
            object_id: ID de l'objet concerné
            details: Détails supplémentaires (dict)
            ip_address: Adresse IP
            user_agent: User agent du navigateur
            
        Returns:
            AuditLog: Log créé
        """
        return cls.objects.create(
            user=user,
            action=action,
            table_name=table_name,
            object_id=object_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def get_by_user(cls, user):
        """Récupérer tous les logs d'un utilisateur."""
        return cls.objects.filter(user=user)
    
    @classmethod
    def get_by_table(cls, table_name):
        """Récupérer tous les logs d'une table."""
        return cls.objects.filter(table_name=table_name)
    
    @classmethod
    def get_by_period(cls, start_date, end_date):
        """Récupérer les logs d'une période."""
        return cls.objects.filter(timestamp__range=[start_date, end_date])
    
    @classmethod
    def get_recent(cls, days=7):
        """Récupérer les logs des derniers jours."""
        from datetime import timedelta
        since = timezone.now() - timedelta(days=days)
        return cls.objects.filter(timestamp__gte=since)
