from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse

from .models import Document, TemplateDocument
from .serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentCreateSerializer,
    DocumentGenerationSerializer,
    TemplateDocumentListSerializer,
    TemplateDocumentDetailSerializer,
    TemplateDocumentCreateSerializer,
    DemandeDocumentSerializer,
    VerificationDocumentSerializer,
)

# VIEWSET : DOCUMENTS
class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les documents administratifs.
    
    Endpoints générés automatiquement :
    - GET /documents/ : Liste tous les documents
    - POST /documents/ : Crée un nouveau document
    - GET /documents/{id}/ : Détails d'un document
    - PUT /documents/{id}/ : Mise à jour complète
    - PATCH /documents/{id}/ : Mise à jour partielle
    - DELETE /documents/{id}/ : Suppression
    
    Actions personnalisées :
    - POST /documents/{id}/generer/ : Générer le PDF du document
    - POST /documents/{id}/delivrer/ : Marquer comme délivré
    - POST /documents/{id}/annuler/ : Annuler le document
    - POST /documents/demander/ : Demander un document (étudiant)
    - POST /documents/verifier/ : Vérifier l'authenticité d'un document
    - GET /documents/mes-documents/ : Documents de l'utilisateur connecté
    - GET /documents/par-etudiant/ : Documents d'un étudiant
    - GET /documents/par-type/ : Filtrer par type
    - GET /documents/en-attente/ : Documents en attente de génération
    - GET /documents/statistiques/ : Stats globales
    
    Filtres :
    - ?etudiant={id} : Par étudiant
    - ?type_document=ATTESTATION_SCOLARITE : Par type
    - ?statut=GENERE : Par statut
    
    Permissions : Authentification requise
    """
    queryset = Document.objects.select_related(
        'etudiant__user',
        'inscription__filiere',
        'inscription__annee_academique',
        'genere_par',
        'delivre_par'
    ).all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer approprié selon l'action.
        
        Returns:
            Serializer: Classe de serializer à utiliser
        """
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentListSerializer
    
    def get_queryset(self):
        """
        Applique les filtres de recherche.
        
        Returns:
            QuerySet: Documents filtrés
        """
        queryset = super().get_queryset()
        
        # Filtre par étudiant
        etudiant_id = self.request.query_params.get('etudiant')
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        
        # Filtre par type
        type_document = self.request.query_params.get('type_document')
        if type_document:
            queryset = queryset.filter(type_document=type_document)
        
        # Filtre par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def generer(self, request, pk=None):
        """
        Action personnalisée : Génère le PDF du document.
        
        URL: POST /documents/{id}/generer/
        
        Processus :
        1. Récupère le template correspondant au type
        2. Prépare les données (contexte)
        3. Rend le HTML avec le template
        4. Génère le PDF
        5. Sauvegarde le fichier
        6. Génère le QR code
        7. Marque comme GENERE
        
        Returns:
            Response: Document généré avec URL du PDF
        """
        document = self.get_object()
        
        # Vérifier que le document n'est pas déjà généré
        if document.statut == 'GENERE':
            return Response(
                {'error': 'Ce document a déjà été généré.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le template
        try:
            template = TemplateDocument.objects.get(
                type_document=document.type_document,
                actif=True
            )
        except TemplateDocument.DoesNotExist:
            return Response(
                {'error': f'Aucun template actif trouvé pour {document.get_type_document_display()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Préparer le contexte avec les données
        contexte = {
            'numero_document': document.numero_document,
            'date_generation': timezone.now().strftime('%d/%m/%Y'),
            'etudiant': {
                'nom': document.etudiant.user.last_name.upper(),
                'prenom': document.etudiant.user.first_name,
                'matricule': document.etudiant.matricule,
                'date_naissance': document.etudiant.date_naissance.strftime('%d/%m/%Y') if document.etudiant.date_naissance else 'N/A',
                'lieu_naissance': document.etudiant.lieu_naissance or 'N/A',
                'email': document.etudiant.user.email,
            }
        }
        
        # Ajouter les données d'inscription si présente
        if document.inscription:
            contexte['inscription'] = {
                'filiere': document.inscription.filiere.nom,
                'niveau': document.inscription.niveau,
                'annee_academique': document.inscription.annee_academique.nom,
            }
        
        # Ajouter les données de résultat si présent
        if document.resultat:
            contexte['resultat'] = {
                'moyenne_generale': document.resultat.moyenne_generale,
                'mention': document.resultat.mention,
                'rang': document.resultat.rang,
            }
        
        # Ajouter les données de paiement si présent
        if document.paiement:
            contexte['paiement'] = {
                'montant': document.paiement.montant,
                'mode': document.paiement.get_mode_paiement_display(),
                'date': document.paiement.date_paiement.strftime('%d/%m/%Y'),
            }
        
        # Rendre le HTML avec le template
        html_content = template.rendre(contexte)
        
        # TODO: Générer le PDF avec une bibliothèque (WeasyPrint, ReportLab, etc.)
        # Pour l'instant, on simule la génération
        # En production, vous devrez installer et utiliser une bibliothèque PDF
        
        # Exemple avec WeasyPrint (à installer: pip install weasyprint)
        # from weasyprint import HTML
        # pdf_file = HTML(string=html_content).write_pdf()
        
        # Pour cette démo, on sauvegarde juste le HTML
        from django.core.files.base import ContentFile
        import os
        
        filename = f"{document.numero_document}.html"
        document.fichier.save(filename, ContentFile(html_content.encode('utf-8')))
        
        # Générer le QR code
        document.generer_qr_code()
        
        # Marquer comme généré (méthode du modèle)
        document.generer(request.user)
        
        serializer = DocumentDetailSerializer(document, context={'request': request})
        
        return Response({
            'message': 'Document généré avec succès.',
            'document': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def delivrer(self, request, pk=None):
        """
        Action personnalisée : Marque le document comme délivré à l'étudiant.
        
        URL: POST /documents/{id}/delivrer/
        
        Returns:
            Response: Document marqué comme délivré
        """
        document = self.get_object()
        
        try:
            # Délivrer (méthode du modèle)
            document.delivrer(request.user)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DocumentDetailSerializer(document, context={'request': request})
        
        return Response({
            'message': 'Document délivré avec succès.',
            'document': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """
        Action personnalisée : Annule un document.
        
        URL: POST /documents/{id}/annuler/
        
        Returns:
            Response: Document annulé
        """
        document = self.get_object()
        
        # Vérifier que le document n'est pas déjà délivré
        if document.statut == 'DELIVRE':
            return Response(
                {'error': 'Impossible d\'annuler un document déjà délivré.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Annuler (méthode du modèle)
        document.annuler()
        
        serializer = DocumentDetailSerializer(document, context={'request': request})
        
        return Response({
            'message': 'Document annulé avec succès.',
            'document': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def demander(self, request):
        """
        Action personnalisée : Un étudiant demande un document.
        
        URL: POST /documents/demander/
        Body: {
            "type_document": "ATTESTATION_SCOLARITE",
            "motif_demande": "Pour candidature master",
            "inscription_id": 1
        }
        
        Processus :
        1. Valide la demande
        2. Récupère l'étudiant connecté
        3. Crée le document en statut BROUILLON
        
        Returns:
            Response: Document créé
        """
        serializer = DemandeDocumentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Récupérer l'étudiant connecté
        try:
            from apps.students.models import Etudiant
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response(
                {'error': 'Vous devez être un étudiant pour demander un document.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Créer le document
        document_data = {
            'etudiant': etudiant,
            'type_document': data['type_document'],
            'motif_demande': data['motif_demande'],
        }
        
        # Ajouter l'inscription si fournie
        if data.get('inscription_id'):
            from apps.students.models import Inscription
            try:
                inscription = Inscription.objects.get(
                    id=data['inscription_id'],
                    etudiant=etudiant
                )
                document_data['inscription'] = inscription
            except Inscription.DoesNotExist:
                return Response(
                    {'error': 'Inscription non trouvée ou ne vous appartient pas.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Ajouter le résultat si fourni
        if data.get('resultat_id'):
            from apps.evaluations.models import Resultat
            try:
                resultat = Resultat.objects.get(
                    id=data['resultat_id'],
                    inscription__etudiant=etudiant
                )
                document_data['resultat'] = resultat
            except Resultat.DoesNotExist:
                return Response(
                    {'error': 'Résultat non trouvé ou ne vous appartient pas.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        document = Document.objects.create(**document_data)
        
        serializer_result = DocumentDetailSerializer(document, context={'request': request})
        
        return Response({
            'message': 'Demande de document enregistrée avec succès.',
            'document': serializer_result.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def verifier(self, request):
        """
        Action personnalisée : Vérifie l'authenticité d'un document.
        
        URL: POST /documents/verifier/
        Body: {
            "qr_code": "abc123xyz...",
            "numero_document": "ATT-SCO-2026-000123"
        }
        
        Returns:
            Response: Résultat de la vérification
        """
        serializer = VerificationDocumentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        document = serializer.validated_data['document']
        
        # Document vérifié avec succès
        return Response({
            'valide': True,
            'message': 'Document authentique et valide.',
            'document': {
                'numero': document.numero_document,
                'type': document.get_type_document_display(),
                'etudiant': f"{document.etudiant.user.first_name} {document.etudiant.user.last_name}",
                'matricule': document.etudiant.matricule,
                'date_generation': document.date_generation,
                'statut': document.get_statut_display(),
            }
        })
    
    @action(detail=False, methods=['get'])
    def mes_documents(self, request):
        """
        Action personnalisée : Documents de l'utilisateur connecté.
        
        URL: GET /documents/mes-documents/
        
        Returns:
            Response: Documents de l'étudiant connecté
        """
        try:
            from apps.students.models import Etudiant
            etudiant = Etudiant.objects.get(user=request.user)
        except Etudiant.DoesNotExist:
            return Response(
                {'error': 'Vous devez être un étudiant.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        documents = self.get_queryset().filter(etudiant=etudiant)
        serializer = self.get_serializer(documents, many=True)
        
        return Response({
            'total': documents.count(),
            'documents': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def par_etudiant(self, request):
        """
        Action personnalisée : Documents d'un étudiant spécifique.
        
        URL: GET /documents/par-etudiant/?etudiant_id={id}
        
        Returns:
            Response: Documents de l'étudiant
        """
        etudiant_id = request.query_params.get('etudiant_id')
        
        if not etudiant_id:
            return Response(
                {'error': 'Le paramètre etudiant_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        documents = self.get_queryset().filter(etudiant_id=etudiant_id)
        serializer = self.get_serializer(documents, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """
        Action personnalisée : Filtrer par type de document.
        
        URL: GET /documents/par-type/?type={type}
        
        Returns:
            Response: Documents du type spécifié
        """
        type_document = request.query_params.get('type')
        
        if not type_document:
            return Response(
                {'error': 'Le paramètre type est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        documents = self.get_queryset().filter(type_document=type_document)
        serializer = self.get_serializer(documents, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """
        Action personnalisée : Documents en attente de génération.
        
        URL: GET /documents/en-attente/
        
        Returns:
            Response: Documents en statut BROUILLON
        """
        documents = self.get_queryset().filter(statut='BROUILLON')
        serializer = self.get_serializer(documents, many=True)
        
        return Response({
            'count': documents.count(),
            'documents': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Action personnalisée : Statistiques globales des documents.
        
        URL: GET /documents/statistiques/
        
        Returns:
            Response: Stats complètes
        """
        total = Document.objects.count()
        brouillons = Document.objects.filter(statut='BROUILLON').count()
        generes = Document.objects.filter(statut='GENERE').count()
        delivres = Document.objects.filter(statut='DELIVRE').count()
        annules = Document.objects.filter(statut='ANNULE').count()
        
        # Répartition par type
        par_type = Document.objects.values('type_document').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Documents générés ce mois
        date_actuelle = timezone.now()
        premier_jour = date_actuelle.replace(day=1)
        
        ce_mois = Document.objects.filter(
            date_generation__gte=premier_jour,
            statut__in=['GENERE', 'DELIVRE']
        ).count()
        
        return Response({
            'total_documents': total,
            'brouillons': brouillons,
            'generes': generes,
            'delivres': delivres,
            'annules': annules,
            'generes_ce_mois': ce_mois,
            'repartition_par_type': list(par_type),
        })

# VIEWSET : TEMPLATES
class TemplateDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les templates de documents.
    
    Endpoints :
    - GET /templates/ : Liste tous les templates
    - POST /templates/ : Crée un nouveau template
    - GET /templates/{id}/ : Détails d'un template
    - PUT/PATCH /templates/{id}/ : Modifier un template
    - DELETE /templates/{id}/ : Supprimer un template
    
    Actions personnalisées :
    - GET /templates/actifs/ : Templates actifs uniquement
    - GET /templates/{id}/previsualiser/ : Prévisualiser le rendu
    - POST /templates/{id}/dupliquer/ : Dupliquer un template
    
    Permissions : Authentification requise
    """
    queryset = TemplateDocument.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Sélectionne le serializer selon l'action.
        
        Returns:
            Serializer: Classe appropriée
        """
        if self.action in ['create', 'update', 'partial_update']:
            return TemplateDocumentCreateSerializer
        elif self.action == 'retrieve':
            return TemplateDocumentDetailSerializer
        return TemplateDocumentListSerializer
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """
        Action personnalisée : Templates actifs uniquement.
        
        URL: GET /templates/actifs/
        
        Returns:
            Response: Templates actifs
        """
        templates = self.get_queryset().filter(actif=True)
        serializer = self.get_serializer(templates, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def previsualiser(self, request, pk=None):
        """
        Action personnalisée : Prévisualise le rendu d'un template.
        
        URL: GET /templates/{id}/previsualiser/
        
        Returns:
            Response: HTML rendu avec données de test
        """
        template = self.get_object()
        
        # Données de test pour prévisualisation
        contexte_test = {
            'numero_document': 'TEST-2026-000001',
            'date_generation': timezone.now().strftime('%d/%m/%Y'),
            'etudiant': {
                'nom': 'DUPONT',
                'prenom': 'Jean',
                'matricule': 'ETU2026001',
                'date_naissance': '01/01/2000',
                'lieu_naissance': 'Paris',
                'email': 'jean.dupont@example.com',
            },
            'inscription': {
                'filiere': 'Licence Informatique',
                'niveau': 'L3',
                'annee_academique': '2025-2026',
            },
            'resultat': {
                'moyenne_generale': 14.5,
                'mention': 'Bien',
                'rang': 5,
            },
        }
        
        # Rendre le template
        html_rendu = template.rendre(contexte_test)
        
        # Retourner le HTML directement pour prévisualisation
        return HttpResponse(html_rendu, content_type='text/html')
    
    @action(detail=True, methods=['post'])
    def dupliquer(self, request, pk=None):
        """
        Action personnalisée : Duplique un template.
        
        URL: POST /templates/{id}/dupliquer/
        
        Returns:
            Response: Nouveau template créé
        """
        template = self.get_object()
        
        # Créer une copie
        nouveau_template = TemplateDocument.objects.create(
            type_document=template.type_document,
            nom=f"{template.nom} (Copie)",
            description=template.description,
            contenu_html=template.contenu_html,
            styles_css=template.styles_css,
            entete_html=template.entete_html,
            pied_page_html=template.pied_page_html,
            watermark_texte=template.watermark_texte,
            actif=False  # Désactivé par défaut
        )
        
        # Note: Le logo n'est pas copié automatiquement
        
        serializer = TemplateDocumentDetailSerializer(nouveau_template, context={'request': request})
        
        return Response({
            'message': 'Template dupliqué avec succès.',
            'template': serializer.data
        }, status=status.HTTP_201_CREATED)
