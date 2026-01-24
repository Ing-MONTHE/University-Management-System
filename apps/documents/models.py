from django.db import models
from apps.core.models import BaseModel, User
from apps.students.models import Etudiant, Inscription
from apps.evaluations.models import Resultat
from apps.finance.models import Paiement

# MODÈLE : DOCUMENT
class Document(BaseModel):
    """
    Représente un document administratif généré pour un étudiant.
    
    Types de documents :
    - ATTESTATION_SCOLARITE : Attestation de scolarité
    - ATTESTATION_INSCRIPTION : Attestation d'inscription
    - ATTESTATION_REUSSITE : Attestation de réussite
    - CERTIFICAT_SCOLARITE : Certificat de scolarité
    - RELEVE_NOTES : Relevé de notes officiel
    - BULLETIN_NOTES : Bulletin de notes
    - BORDEREAU_INSCRIPTION : Bordereau d'inscription
    - RECU_PAIEMENT : Reçu de paiement
    - CARTE_ETUDIANT : Carte d'étudiant
    
    Statuts :
    - BROUILLON : Document en cours de génération
    - GENERE : Document généré et prêt
    - DELIVRE : Document délivré à l'étudiant
    - ANNULE : Document annulé
    
    Relations :
    - Liée à un étudiant
    - Générée par un utilisateur
    - Peut être liée à une inscription, résultat, ou paiement
    """
    
    # Choix de types de documents
    class TypeDocument(models.TextChoices):
        """
        Types de documents administratifs.
        """
        ATTESTATION_SCOLARITE = 'ATTESTATION_SCOLARITE', 'Attestation de scolarité'
        ATTESTATION_INSCRIPTION = 'ATTESTATION_INSCRIPTION', 'Attestation d\'inscription'
        ATTESTATION_REUSSITE = 'ATTESTATION_REUSSITE', 'Attestation de réussite'
        CERTIFICAT_SCOLARITE = 'CERTIFICAT_SCOLARITE', 'Certificat de scolarité'
        RELEVE_NOTES = 'RELEVE_NOTES', 'Relevé de notes'
        BULLETIN_NOTES = 'BULLETIN_NOTES', 'Bulletin de notes'
        BORDEREAU_INSCRIPTION = 'BORDEREAU_INSCRIPTION', 'Bordereau d\'inscription'
        RECU_PAIEMENT = 'RECU_PAIEMENT', 'Reçu de paiement'
        CARTE_ETUDIANT = 'CARTE_ETUDIANT', 'Carte d\'étudiant'
    
    # Choix de statuts
    class StatutDocument(models.TextChoices):
        """
        Statuts du document.
        """
        BROUILLON = 'BROUILLON', 'Brouillon'
        GENERE = 'GENERE', 'Généré'
        DELIVRE = 'DELIVRE', 'Délivré'
        ANNULE = 'ANNULE', 'Annulé'
    
    # Étudiant concerné
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Étudiant concerné par le document"
    )
    
    # Type de document
    type_document = models.CharField(
        max_length=50,
        choices=TypeDocument.choices,
        help_text="Type de document"
    )
    
    # Numérotation unique
    numero_document = models.CharField(
        max_length=100,
        unique=True,
        help_text="Numéro unique du document (généré automatiquement)"
    )
    
    # Relations optionnelles (selon le type de document)
    inscription = models.ForeignKey(
        Inscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Inscription concernée (si applicable)"
    )
    resultat = models.ForeignKey(
        Resultat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Résultat concerné (pour relevés de notes)"
    )
    paiement = models.ForeignKey(
        Paiement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Paiement concerné (pour reçus)"
    )
    
    # Fichier généré
    fichier = models.FileField(
        upload_to='documents/%Y/%m/',
        null=True,
        blank=True,
        help_text="Fichier PDF du document"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=StatutDocument.choices,
        default=StatutDocument.BROUILLON,
        help_text="Statut actuel du document"
    )
    
    # Génération
    genere_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_generes',
        help_text="Utilisateur qui a généré le document"
    )
    date_generation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de génération"
    )
    
    # Délivrance
    delivre_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_delivres',
        help_text="Utilisateur qui a délivré le document"
    )
    date_delivrance = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de délivrance à l'étudiant"
    )
    
    # QR Code de vérification
    qr_code = models.CharField(
        max_length=200,
        blank=True,
        help_text="Code QR pour vérification d'authenticité"
    )
    
    # Observations
    motif_demande = models.TextField(
        blank=True,
        help_text="Motif de la demande du document"
    )
    observations = models.TextField(
        blank=True,
        help_text="Observations diverses"
    )
    
    class Meta:
        db_table = 'documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-date_generation', '-created_at']
        indexes = [
            models.Index(fields=['numero_document']),
            models.Index(fields=['etudiant', 'type_document']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"{self.get_type_document_display()} - {self.etudiant} ({self.numero_document})"
    
    def save(self, *args, **kwargs):
        """
        Génère automatiquement un numéro de document unique avant sauvegarde.
        
        Format : TYPE-YYYY-XXXXXX
        Exemple : ATT-SCO-2026-000123
        """
        if not self.numero_document:
            from django.utils import timezone
            annee = timezone.now().year
            
            # Préfixe selon le type
            prefixes = {
                'ATTESTATION_SCOLARITE': 'ATT-SCO',
                'ATTESTATION_INSCRIPTION': 'ATT-INS',
                'ATTESTATION_REUSSITE': 'ATT-REU',
                'CERTIFICAT_SCOLARITE': 'CERT-SCO',
                'RELEVE_NOTES': 'REL-NOT',
                'BULLETIN_NOTES': 'BUL-NOT',
                'BORDEREAU_INSCRIPTION': 'BOR-INS',
                'RECU_PAIEMENT': 'REC-PAI',
                'CARTE_ETUDIANT': 'CARTE',
            }
            
            prefix = prefixes.get(self.type_document, 'DOC')
            
            # Récupérer le dernier numéro de ce type pour cette année
            dernier_doc = Document.objects.filter(
                type_document=self.type_document,
                numero_document__startswith=f'{prefix}-{annee}-'
            ).order_by('-numero_document').first()
            
            if dernier_doc:
                dernier_numero = int(dernier_doc.numero_document.split('-')[-1])
                nouveau_numero = dernier_numero + 1
            else:
                nouveau_numero = 1
            
            self.numero_document = f'{prefix}-{annee}-{nouveau_numero:06d}'
        
        super().save(*args, **kwargs)
    
    def generer(self, user):
        """
        Marque le document comme généré.
        
        Args:
            user (User): Utilisateur qui génère le document
        """
        from django.utils import timezone
        
        self.statut = self.StatutDocument.GENERE
        self.genere_par = user
        self.date_generation = timezone.now()
        self.save()
    
    def delivrer(self, user):
        """
        Marque le document comme délivré à l'étudiant.
        
        Args:
            user (User): Utilisateur qui délivre le document
        """
        from django.utils import timezone
        
        if self.statut != 'GENERE':
            raise ValueError("Seuls les documents générés peuvent être délivrés.")
        
        self.statut = self.StatutDocument.DELIVRE
        self.delivre_par = user
        self.date_delivrance = timezone.now()
        self.save()
    
    def annuler(self):
        """
        Annule le document.
        """
        self.statut = self.StatutDocument.ANNULE
        self.save()
    
    def generer_qr_code(self):
        """
        Génère un code QR unique pour vérification.
        
        Returns:
            str: Code QR généré
        """
        import hashlib
        from django.utils import timezone
        
        # Créer un hash unique basé sur les données du document
        data = f"{self.numero_document}-{self.etudiant.matricule}-{timezone.now().isoformat()}"
        qr_hash = hashlib.sha256(data.encode()).hexdigest()[:32]
        
        self.qr_code = qr_hash
        self.save()
        
        return qr_hash

# MODÈLE : TEMPLATE DOCUMENT
class TemplateDocument(BaseModel):
    """
    Représente un template personnalisable pour un type de document.
    
    Permet de définir des modèles réutilisables avec :
    - En-tête personnalisé (logo, coordonnées)
    - Corps du document (texte avec variables)
    - Pied de page (signatures, cachets)
    - Styles (polices, couleurs)
    
    Variables disponibles :
    - {{nom_etudiant}}, {{prenom_etudiant}}, {{matricule}}
    - {{filiere}}, {{niveau}}, {{annee_academique}}
    - {{date_naissance}}, {{lieu_naissance}}
    - {{date_generation}}, {{numero_document}}
    - etc.
    
    Relations :
    - Liée à un type de document
    """
    
    # Type de document concerné
    type_document = models.CharField(
        max_length=50,
        choices=Document.TypeDocument.choices,
        unique=True,
        help_text="Type de document concerné par ce template"
    )
    
    # Nom du template
    nom = models.CharField(
        max_length=200,
        help_text="Nom descriptif du template"
    )
    description = models.TextField(
        blank=True,
        help_text="Description du template"
    )
    
    # Contenu du template
    contenu_html = models.TextField(
        help_text="Contenu HTML du template avec variables"
    )
    
    # Styles CSS
    styles_css = models.TextField(
        blank=True,
        help_text="Styles CSS personnalisés"
    )
    
    # En-tête et pied de page
    entete_html = models.TextField(
        blank=True,
        help_text="En-tête HTML (logo, coordonnées université)"
    )
    pied_page_html = models.TextField(
        blank=True,
        help_text="Pied de page HTML (signatures, cachets)"
    )
    
    # Logo
    logo = models.ImageField(
        upload_to='templates/logos/',
        null=True,
        blank=True,
        help_text="Logo de l'université"
    )
    
    # Watermark
    watermark_texte = models.CharField(
        max_length=200,
        blank=True,
        help_text="Texte du watermark (ex: CONFIDENTIEL, COPIE)"
    )
    
    # Actif
    actif = models.BooleanField(
        default=True,
        help_text="True si ce template est actif"
    )
    
    class Meta:
        db_table = 'templates_documents'
        verbose_name = 'Template de document'
        verbose_name_plural = 'Templates de documents'
        ordering = ['type_document']
    
    def __str__(self):
        return f"Template {self.get_type_document_display()}"
    
    def rendre(self, contexte):
        """
        Rend le template avec les données du contexte.
        
        Args:
            contexte (dict): Données à injecter dans le template
        
        Returns:
            str: HTML rendu
        """
        from django.template import Template, Context
        
        # Créer le template complet
        html_complet = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{self.styles_css}</style>
        </head>
        <body>
            <div class="entete">{self.entete_html}</div>
            <div class="contenu">{self.contenu_html}</div>
            <div class="pied-page">{self.pied_page_html}</div>
        </body>
        </html>
        """
        
        # Rendre avec le contexte
        template = Template(html_complet)
        context = Context(contexte)
        
        return template.render(context)
