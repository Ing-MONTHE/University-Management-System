# 🎓 University Management System - Backend API

> Système complet de gestion universitaire développé avec Django REST Framework

## 📖 Description

**University Management System (UMS)** est une API REST complète et professionnelle pour la gestion intégrale d'établissements universitaires. Conçue spécifiquement pour le contexte africain francophone, elle automatise l'ensemble des processus académiques, administratifs et financiers d'une université.

**Version actuelle :** 1.0.0 - Production Ready ✅

---

## ✨ Caractéristiques Principales

### 🔐 Sécurité & Authentification
- Authentification **JWT** (Access + Refresh tokens)
- Système **RBAC** complet (Role-Based Access Control)
- Permissions granulaires par fonctionnalité
- Audit logging de toutes les actions (IP, User Agent, timestamp)
- Protection contre les injections SQL (Django ORM)
- Variables d'environnement sécurisées

### 🏗️ Architecture Technique
- **12 modules Django** indépendants et réutilisables
- **48 modèles** de données soigneusement conçus
- **~526 endpoints API** REST documentés
- Architecture modulaire et scalable
- Code propre et maintenable
- Documentation automatique Swagger/ReDoc

### ⚡ Fonctionnalités Business
- Automatisation intelligente des processus
- Validation métier complète
- Génération automatique de documents (PDF)
- Calculs automatiques (moyennes, pénalités, crédits ECTS)
- Détection de conflits en temps réel
- Statistiques et rapports exportables

---

## 📦 Modules Implémentés

| Module | Description | Modèles | Points Forts |
|--------|-------------|---------|--------------|
| **Core** | Infrastructure, Auth, RBAC | 4 | JWT, Permissions, Audit logging |
| **Academic** | Structure académique | 5 | Hiérarchie Faculté→Filière→Matière |
| **Students** | Étudiants & Enseignants | 4 | Matricules auto, Inscriptions |
| **Evaluations** | Notes & Délibérations | 7 | Calcul auto moyennes, Jury complet |
| **Schedule** | Emplois du temps | 5 | Détection conflits temps réel |
| **Library** | Bibliothèque | 3 | Pénalités auto, Limite emprunts |
| **Attendance** | Présences & Absences | 3 | Taux présence, Justificatifs |
| **Finance** | Gestion financière | 4 | Paiements, Bourses, Factures PDF |
| **Communications** | Notifications | 4 | Multi-canaux, Préférences |
| **Resources** | Équipements | 4 | Réservations, Maintenance |
| **Documents** | Documents officiels | 2 | Attestations, Relevés PDF |
| **Analytics** | Rapports & Stats | 3 | Dashboards, KPI, Exports |

**Total : 48 modèles • ~526 endpoints • 100% fonctionnel**

---

## 🚀 Installation

### Prérequis

- **Python** 3.11 ou supérieur
- **PostgreSQL** 15 ou supérieur
- **pip** et **virtualenv**

### 1. Cloner le projet

```bash
git clone https://github.com/votre-username/University-Management-System.git
cd University-Management-System
```

### 2. Créer l'environnement virtuel

```bash
# Créer l'environnement
python -m venv venv

# Activer (Windows)
venv\Scripts\activate

# Activer (Linux/Mac)
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Créer un fichier `config.env` à la racine du projet :

```env
# Django Configuration
SECRET_KEY=votre-cle-secrete-unique-et-complexe
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=university_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Internationalization
LANGUAGE_CODE=fr-fr
TIME_ZONE=Africa/Douala

# Pagination
PAGE_SIZE=20

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=60      # minutes
JWT_REFRESH_TOKEN_LIFETIME=7      # jours

# Media Files
MEDIA_URL=/media/
MEDIA_ROOT=media
```

**⚠️ Important :** Ne jamais committer le fichier `config.env` ! Ajoutez-le au `.gitignore`.

### 5. Créer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données
CREATE DATABASE university_db;

# Créer un utilisateur (optionnel)
CREATE USER university_user WITH PASSWORD 'votre_password';
GRANT ALL PRIVILEGES ON DATABASE university_db TO university_user;

# Quitter
\q
```

### 6. Appliquer les migrations

```bash
python manage.py migrate
```

### 7. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer votre compte administrateur.

### 8. Lancer le serveur de développement

```bash
python manage.py runserver
```

L'API sera accessible sur : **http://localhost:8000/**

---

## 📚 Documentation API

### Accéder à la documentation

Une fois le serveur lancé, accédez à :

- **Swagger UI (interactif)** : http://localhost:8000/api/docs/
- **ReDoc (lecture)** : http://localhost:8000/api/redoc/
- **Schéma OpenAPI (JSON)** : http://localhost:8000/api/schema/

### Interface d'administration

Django Admin : http://localhost:8000/admin/

---

## 🔑 Authentification

### 1. Obtenir un token JWT

```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "votre_username",
  "password": "votre_password"
}
```

**Réponse :**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@university.cm",
    "full_name": "Administrateur",
    "roles": ["Administrateur"],
    "permissions": ["all"]
  }
}
```

### 2. Utiliser le token

Incluez le token dans l'en-tête de chaque requête :

```http
GET /api/facultes/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Rafraîchir le token

```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 📋 Exemples d'Endpoints

### Gestion Académique

```bash
# Liste des facultés
GET /api/facultes/

# Créer une faculté
POST /api/facultes/
{
  "nom": "Faculté des Sciences",
  "code": "FS",
  "description": "Sciences exactes et appliquées"
}

# Statistiques d'une faculté
GET /api/facultes/{id}/statistiques/

# Liste des filières
GET /api/filieres/

# Matières d'une filière
GET /api/filieres/{id}/matieres/
```

### Gestion des Étudiants

```bash
# Liste des étudiants
GET /api/etudiants/

# Créer un étudiant (matricule auto-généré)
POST /api/etudiants/
{
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@student.cm",
  "date_naissance": "2002-05-15",
  "sexe": "M",
  "filiere": 1
}

# Bulletins d'un étudiant
GET /api/etudiants/{id}/bulletins/

# Notes d'un étudiant
GET /api/etudiants/{id}/notes/

# Statistiques étudiants
GET /api/etudiants/statistiques/
```

### Notes & Évaluations

```bash
# Créer une évaluation
POST /api/evaluations/
{
  "matiere": 1,
  "type_evaluation": 1,
  "titre": "Devoir 1",
  "bareme": 20,
  "coefficient": 1,
  "date_evaluation": "2024-03-15"
}

# Saisir les notes en lot
POST /api/notes/saisie-lot/
{
  "evaluation": 1,
  "notes": [
    {"etudiant": 1, "note": 15.5},
    {"etudiant": 2, "note": 18.0},
    {"etudiant": 3, "absent": true}
  ]
}

# Générer un bulletin
GET /api/resultats/{id}/bulletin/
```

### Emploi du Temps

```bash
# Programmer un cours
POST /api/cours/
{
  "matiere": 1,
  "enseignant": 1,
  "salle": 1,
  "creneau": 1,
  "type_cours": "CM",
  "filiere": 1,
  "semestre": 1
}

# Emploi du temps d'une filière
GET /api/cours/emploi-du-temps/?filiere=1&semestre=1

# Emploi du temps d'un enseignant
GET /api/cours/enseignant/?enseignant_id=1

# Vérifier les conflits
GET /api/conflits/
GET /api/conflits/statistiques/
```

### Bibliothèque

```bash
# Catalogue de livres
GET /api/livres/

# Livres disponibles
GET /api/livres/disponibles/

# Créer un emprunt
POST /api/emprunts/
{
  "livre": 1,
  "etudiant": 1,
  "date_retour_prevue": "2024-04-15"
}

# Retourner un livre
POST /api/emprunts/{id}/retour/

# Emprunts en retard
GET /api/emprunts/en-retard/
```

### Présences

```bash
# Créer une feuille de présence
POST /api/feuilles-presence/
{
  "cours": 1,
  "date": "2024-03-15"
}

# Marquer les présences en masse
POST /api/feuilles-presence/{id}/marquer-presences/
{
  "presences": [
    {"etudiant": 1, "statut": "PRESENT"},
    {"etudiant": 2, "statut": "ABSENT"},
    {"etudiant": 3, "statut": "RETARD", "minutes_retard": 15}
  ]
}

# Alertes d'absence
GET /api/presences/alertes/
```

### Finance

```bash
# Enregistrer un paiement
POST /api/paiements/
{
  "etudiant": 1,
  "montant": 150000,
  "mode_paiement": "MOBILE_MONEY",
  "description": "Frais de scolarité - Tranche 1"
}

# Générer un reçu PDF
GET /api/paiements/{id}/recu/

# Factures impayées
GET /api/factures/impayes/

# Statistiques financières
GET /api/paiements/statistiques/
```

### Communications

```bash
# Créer une annonce
POST /api/annonces/
{
  "titre": "Rentrée académique 2024-2025",
  "contenu": "La rentrée est fixée au 1er septembre",
  "cible_roles": ["ETUDIANT"],
  "date_publication": "2024-08-15"
}

# Publier une annonce
POST /api/annonces/{id}/publier/

# Notifications non lues
GET /api/notifications/non-lues/

# Envoyer un message
POST /api/messages/
{
  "destinataire": 2,
  "sujet": "Question sur le cours",
  "contenu": "Bonjour, j'ai une question..."
}
```

### Documents & Analytics

```bash
# Générer une attestation de scolarité
GET /api/documents/attestation-scolarite/?etudiant=1

# Générer un relevé de notes
GET /api/documents/releve-notes/?etudiant=1&semestre=1

# Rapports disponibles
GET /api/rapports/

# Générer un rapport
POST /api/rapports/generer/

# KPI académiques
GET /api/kpis/academiques/

# Statistiques de réussite
GET /api/statistiques/taux-reussite/
```

---

## 🛠️ Technologies Utilisées

### Framework & Base de données
- **Django 6.0.1** - Framework web Python
- **Django REST Framework 3.16.1** - API REST
- **PostgreSQL 15+** - Base de données relationnelle
- **Simple JWT 5.5.1** - Authentification JWT

### Packages Principaux
- **django-filter 25.2** - Filtrage avancé des données
- **django-cors-headers 4.9.0** - Gestion CORS pour frontend
- **drf-spectacular 0.29.0** - Documentation OpenAPI/Swagger
- **psycopg2-binary 2.9.11** - Connecteur PostgreSQL
- **python-decouple 3.8** - Variables d'environnement
- **phonenumber-field 8.4.0** - Validation numéros de téléphone

### Génération de Documents
- **reportlab 4.4.9** - Génération de PDF
- **python-docx 1.2.0** - Génération de documents Word
- **openpyxl 3.1.5** - Export Excel
- **xlsxwriter 3.2.9** - Création de fichiers Excel

### Autres
- **pillow 12.1.0** - Traitement d'images
- **PyYAML 6.0.3** - Configuration YAML

---

## 📊 Fonctionnalités Détaillées

### 🎓 Module Academic - Structure Académique

**Modèles :** AnneeAcademique, Faculte, Departement, Filiere, Matiere

**Fonctionnalités :**
- Hiérarchie complète : Université → Faculté → Département → Filière → Matière
- Activation d'année académique (une seule active à la fois)
- Statistiques par faculté (départements, filières, étudiants)
- Gestion des coefficients et crédits ECTS
- Types de cours (CM, TD, TP)

### 👥 Module Students - Gestion des Acteurs

**Modèles :** Etudiant, Enseignant, Inscription, Attribution

**Fonctionnalités :**
- Génération automatique de matricules (ETUYYYY### / ENSYYYY###)
- Profils complets avec photos
- Inscriptions avec suivi des paiements
- Attributions enseignants aux matières
- Calcul automatique de charge horaire
- Statistiques détaillées (sexe, nationalité, grade)

### 📝 Module Evaluations - Notes & Jury

**Modèles :** TypeEvaluation, Evaluation, Note, Resultat, SessionDeliberation, MembreJury, DecisionJury

**Fonctionnalités :**
- Types d'évaluations multiples (Devoir, Examen, TP, Projet)
- Saisie individuelle ou en lot
- Calcul automatique des moyennes pondérées
- Génération de mentions (Excellent → Passable)
- Détermination automatique du statut (ADMIS/AJOURNÉ/RATTRAPAGE)
- Système de délibération complet avec composition de jury
- Génération de bulletins et procès-verbaux PDF
- Attribution automatique des crédits ECTS

### 📅 Module Schedule - Emplois du Temps

**Modèles :** Batiment, Salle, Creneau, Cours, ConflitSalle

**Fonctionnalités :**
- Gestion de bâtiments, salles (types : COURS, TD, TP, AMPHI)
- Créneaux horaires avec calcul automatique de durée
- Programmation de cours avec validation
- **Détection automatique de conflits :**
  - Conflit de salle (2 cours simultanés, même salle)
  - Conflit d'enseignant (1 prof, 2 cours en même temps)
  - Capacité dépassée (effectif > capacité salle)
- Génération d'emploi du temps par filière
- Consultation par enseignant
- Taux d'occupation en temps réel

### 📚 Module Library - Bibliothèque

**Modèles :** CategoriesLivre, Livre, Emprunt

**Fonctionnalités :**
- Catalogage complet (ISBN, auteur, éditeur, catégorie)
- Gestion des exemplaires (stock total/disponible)
- **Système d'emprunt intelligent :**
  - Limite de 5 emprunts simultanés par étudiant
  - Blocage si pénalités impayées
  - Calcul automatique des pénalités (100 FCFA/jour de retard)
  - Mise à jour automatique du stock
- Détection automatique des retards
- Historique complet des emprunts
- Statistiques de la bibliothèque

### ✅ Module Attendance - Assiduité

**Modèles :** FeuillePresence, Presence, JustificatifAbsence

**Fonctionnalités :**
- Feuilles de présence par cours
- Génération automatique des enregistrements
- Marquage individuel ou en masse (PRESENT, ABSENT, RETARD)
- Calcul automatique des taux de présence
- Upload de justificatifs (PDF, images)
- Workflow d'approbation/rejet des justificatifs
- Alertes automatiques si seuil dépassé
- Historique complet par étudiant

### 💰 Module Finance - Gestion Financière

**Modèles :** FraisScolarite, Paiement, Bourse, Facture

**Fonctionnalités :**
- Définition des frais par filière/niveau/année
- Gestion des tranches de paiement
- Modes multiples (Espèces, Virement, Mobile Money)
- Enregistrement des paiements avec validation
- Génération automatique de factures et reçus PDF
- Système de bourses et exonérations
- Suivi des impayés
- Statistiques financières détaillées

### 📢 Module Communications

**Modèles :** Annonce, Notification, Message, PreferenceNotification

**Fonctionnalités :**
- Système d'annonces avec ciblage (rôles, filières)
- Notifications push en temps réel
- Messagerie interne complète
- Préférences par canal (Email, SMS, Push, In-App)
- Historique complet
- Statuts de lecture

### 🔧 Module Resources - Ressources

**Modèles :** Equipement, Reservation, ReservationEquipement, Maintenance

**Fonctionnalités :**
- Gestion d'équipements (projecteurs, ordinateurs, labos)
- Système de réservation de salles et équipements
- Calendrier de disponibilité
- Maintenance préventive et corrective
- Suivi de l'état des équipements
- Historique des interventions

### 📄 Module Documents

**Modèles :** Document, TemplateDocument

**Fonctionnalités :**
- Génération automatique d'attestations de scolarité
- Relevés de notes officiels
- Certificats personnalisables
- Templates modifiables (HTML/CSS)
- Export PDF automatique
- Archivage sécurisé

### 📈 Module Analytics

**Modèles :** Rapport, Dashboard, KPI

**Fonctionnalités :**
- Tableaux de bord interactifs personnalisables
- KPI en temps réel (taux de réussite, effectifs, finances)
- Rapports automatiques planifiables
- Exports multiformats (PDF, Excel, CSV)
- Statistiques académiques avancées
- Évolution des effectifs

---

## 🧪 Tests

### Exécuter les tests

```bash
# Tous les tests
python manage.py test

# Tests d'un module spécifique
python manage.py test apps.core
python manage.py test apps.academic
python manage.py test apps.students

# Tests avec verbosité
python manage.py test --verbosity=2

# Tests avec couverture de code
pip install coverage
coverage run --source='apps' manage.py test
coverage report
coverage html  # Génère un rapport HTML
```

### Tests de performance

```bash
# Installer django-silk pour profiling
pip install django-silk

# Voir la documentation de Silk pour l'activation
```

---

## 📈 Métriques du Projet

| Métrique | Valeur |
|----------|--------|
| **Modules** | 12 |
| **Modèles Django** | 48 |
| **Endpoints API** | ~526 |
| **Lignes de code** | ~22,500 |
| **Migrations** | 13 |
| **Serializers** | 90+ |
| **ViewSets** | 45+ |
| **Admin Interfaces** | 48 |

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -m 'Ajout fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

### Standards de code

- Suivre les conventions PEP 8
- Ajouter des docstrings aux fonctions
- Écrire des tests pour les nouvelles fonctionnalités
- Mettre à jour la documentation

---

## 🐛 Signaler un Bug

Utilisez les [Issues GitHub](https://github.com/Ing-MONTHE/University-Management-System/issues) pour :
- Signaler des bugs
- Proposer des améliorations
- Demander des nouvelles fonctionnalités

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## 👨‍💻 Auteur

**MONTHE** - Développeur Full Stack

---

## 🙏 Remerciements

- **Django** et **Django REST Framework** pour les frameworks excellents
- **PostgreSQL** pour la base de données robuste
- La communauté open source pour les nombreux packages utilisés

---

## 📞 Support

Pour toute question ou assistance :

- **Email :** monthejunior45@gmail.com
- **Documentation API :** http://localhost:8000/api/docs/
- **GitHub Issues :** [Signaler un problème](https://github.com/Ing-MONTHE/University-Management-System/issues)

---

## 📅 Historique des Versions

### Version 1.0.0 (Janvier 2026) - Production Ready ✅

**Fonctionnalités :**
- ✅ 12 modules complets et fonctionnels
- ✅ 48 modèles de données
- ✅ ~526 endpoints API REST
- ✅ Authentification JWT complète
- ✅ Système RBAC avec permissions granulaires
- ✅ Audit logging complet
- ✅ Documentation Swagger/ReDoc
- ✅ Génération automatique de documents PDF
- ✅ Calculs automatiques (moyennes, pénalités, etc.)
- ✅ Détection de conflits en temps réel
- ✅ Statistiques et rapports exportables

**Modules implémentés :**
1. Core - Infrastructure & Authentification
2. Academic - Structure académique
3. Students - Étudiants & Enseignants
4. Evaluations - Notes & Délibérations
5. Schedule - Emplois du temps
6. Library - Bibliothèque
7. Attendance - Présences & Absences
8. Finance - Gestion financière
9. Communications - Notifications
10. Resources - Équipements
11. Documents - Documents officiels
12. Analytics - Rapports & Statistiques

---

**Développé pour une gestion universitaire moderne et efficace**
