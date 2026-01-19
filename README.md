# 🎓 University Management System

Système complet de gestion universitaire développé avec Django REST Framework.

## 📋 Table des matières

- [À propos](#à-propos)
- [Fonctionnalités](#fonctionnalités)
- [Technologies utilisées](#technologies-utilisées)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API Documentation](#api-documentation)
- [Sprints du projet](#sprints-du-projet)
- [Contributeurs](#contributeurs)

---

## 📖 À propos

University Management System (UMS) est une application web complète pour la gestion d'une université. Elle permet de gérer les étudiants, les enseignants, les inscriptions, les notes, les évaluations, les délibérations, les emplois du temps et bien plus encore.

**Statut du projet :** 🚧 En développement (5/10 sprints terminés - 50%)

---

## ✨ Fonctionnalités

### ✅ Fonctionnalités implémentées (Sprints 1-5)

#### 🔐 Sprint 1 : Infrastructure de base
- Authentification JWT (Access + Refresh tokens)
- Gestion des utilisateurs (User, Role, Permission)
- Système de permissions granulaires
- Système d'audit (logs des actions)
- Interface d'administration Django
- **API Endpoints :** ~15

#### 🏛️ Sprint 2 : Structure académique
- Gestion des années académiques (avec activation)
- Gestion des facultés (avec statistiques)
- Gestion des départements (rattachés aux facultés)
- Gestion des filières (Licence, Master, Doctorat, DUT, BTS)
- Gestion des matières (avec CM, TD, TP)
- Relations hiérarchiques complètes
- **API Endpoints :** ~35

#### 👥 Sprint 3 : Étudiants et Enseignants
- Gestion des étudiants (profils complets)
- Génération automatique de matricules (format : STU-YYYY-###)
- Gestion des enseignants (profils, grades, CV)
- Génération automatique de matricules enseignants (format : TCH-YYYY-###)
- Inscriptions des étudiants avec gestion des paiements
- Attributions des enseignants aux matières (CM, TD, TP)
- Calcul de charge horaire des enseignants
- Statistiques détaillées par sexe, nationalité, grade
- **API Endpoints :** ~35

#### 📊 Sprint 4 : Notes, Évaluations et Délibérations
**Évaluations :**
- Types d'évaluations (Devoir, Examen, Rattrapage, TD, TP, Projet)
- Création d'évaluations avec coefficient et barème
- Duplication d'évaluations
- Statistiques par évaluation (moyenne, min, max, répartition)

**Notes :**
- Saisie individuelle ou multiple des notes
- Gestion des absences
- Conversion automatique des notes sur 20
- Appréciations automatiques (Excellent, Très bien, Bien, etc.)
- Validation des notes (note <= barème)

**Résultats :**
- Calcul automatique des moyennes pondérées
- Génération des mentions (Passable à Excellent)
- Calcul du statut (ADMIS, AJOURNÉ, RATTRAPAGE)
- Attribution automatique des crédits
- Bulletins complets par étudiant

**Délibérations :**
- Sessions de délibération par filière/niveau/semestre
- Composition du jury (Président, Membres, Secrétaire)
- Génération automatique des décisions du jury
- Calcul automatique des rangs/classements
- Statuts de session (PREVUE, EN_COURS, TERMINEE, VALIDEE)
- Procès-verbaux de délibération
- Taux de réussite automatique
- **API Endpoints :** ~50

#### 📅 Sprint 5 : Emploi du temps et Gestion des Salles
**Bâtiments et Salles :**
- Gestion des bâtiments (code, nom, nombre d'étages)
- Gestion des salles (types : COURS, TD, TP, AMPHI, CONFERENCE)
- Capacités et équipements
- Taux d'occupation automatique
- Vérification de disponibilité en temps réel

**Créneaux horaires :**
- Gestion des créneaux (jour, heure début, heure fin)
- Durée automatique en minutes
- Validation : heure fin > heure début
- Organisation par jour de la semaine

**Cours et Programmation :**
- Programmation des cours (matière, enseignant, filière, salle, créneau)
- Types de cours (CM, TD, TP)
- Effectif prévu et validation capacité
- **Validation automatique en temps réel** :
  - Conflit de salle (2 cours, même salle, même créneau)
  - Conflit d'enseignant (1 prof, 2 cours simultanés)
  - Capacité dépassée (effectif > capacité salle)
- Génération d'emploi du temps par filière et semestre
- Consultation par enseignant
- Duplication de cours

**Détection et Gestion des Conflits :**
- Détection automatique de 3 types de conflits :
  - Conflit de salle
  - Conflit d'enseignant
  - Capacité dépassée
- Statuts : DETECTE, EN_COURS, RESOLU, IGNORE
- Tracking de la résolution avec date et solution appliquée
- Statistiques des conflits
- **API Endpoints :** ~45

**Total API Endpoints : ~180**

### ⏳ Fonctionnalités à venir (Sprints 6-10)

- **Sprint 6 :** Finance et gestion complète des paiements
- **Sprint 7 :** Inscriptions en ligne (portail étudiant)
- **Sprint 8 :** Bibliothèque et gestion des emprunts
- **Sprint 9 :** Notifications (Email, SMS, Push)
- **Sprint 10 :** Reporting avancé et tableaux de bord

---

## 🛠️ Technologies utilisées

### Backend
- **Python 3.13**
- **Django 6.0.1**
- **Django REST Framework 3.14+**
- **PostgreSQL 17** (Base de données)
- **JWT** (Authentification)

### Packages principaux
```
django==6.0.1
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1
psycopg2-binary==2.9.9
python-decouple==3.8
django-cors-headers==4.3.1
django-filter==23.5
drf-spectacular==0.27.0
pillow==10.1.0
openpyxl==3.1.2
```

### Frontend (À venir)
- React.js + Tailwind CSS (Sprint 11+)

---

## 🏗️ Architecture
```
University_Management/
│
├── config/                      # Configuration Django
│   ├── settings.py             # Paramètres du projet
│   ├── urls.py                 # URLs principales
│   └── wsgi.py                 # WSGI config
│
├── apps/                        # Applications Django
│   ├── core/                   # Sprint 1 - Auth & Permissions
│   │   ├── models.py          # User, Role, Permission, AuditLog
│   │   ├── serializers.py     # 8 serializers
│   │   ├── views.py           # 5 viewsets
│   │   ├── urls.py            # ~15 endpoints
│   │   └── admin.py           # Config admin
│   │
│   ├── academic/               # Sprint 2 - Structure académique
│   │   ├── models.py          # AnneeAcademique, Faculte, Departement, Filiere, Matiere
│   │   ├── serializers.py     # 6 serializers
│   │   ├── views.py           # 5 viewsets
│   │   ├── urls.py            # ~35 endpoints
│   │   └── admin.py           # Config admin
│   │
│   ├── students/               # Sprint 3 - Étudiants & Enseignants
│   │   ├── models.py          # Etudiant, Enseignant, Inscription, Attribution
│   │   ├── serializers.py     # 6 serializers
│   │   ├── views.py           # 4 viewsets
│   │   ├── urls.py            # ~35 endpoints
│   │   └── admin.py           # Config admin
│   │
│   ├── evaluations/            # Sprint 4 - Notes & Évaluations
│   │   ├── models.py          # TypeEvaluation, Evaluation, Note, Resultat
│   │   │                      # SessionDeliberation, MembreJury, DecisionJury
│   │   ├── serializers.py     # 10 serializers
│   │   ├── views.py           # 7 viewsets
│   │   ├── urls.py            # ~50 endpoints
│   │   └── admin.py           # Config admin
│   │
│   └── schedule/               # Sprint 5 - Emploi du temps
│       ├── models.py          # Batiment, Salle, Creneau, Cours, ConflitSalle
│       ├── serializers.py     # 10 serializers
│       ├── views.py           # 5 viewsets
│       ├── urls.py            # ~45 endpoints
│       └── admin.py           # Config admin
│
├── media/                       # Fichiers uploadés (photos, CV)
├── staticfiles/                 # Fichiers statiques (CSS, JS)
├── .env/                        # Environnement virtuel Python
├── config.env                   # Variables d'environnement
├── requirements.txt             # Dépendances Python
├── manage.py                    # Script Django
└── README.md                    # Ce fichier
```

---

## 🚀 Installation

### Prérequis

- Python 3.13+
- PostgreSQL 16+
- Git

### Étapes d'installation

#### 1. Cloner le projet
```bash
git clone https://github.com/VOTRE-USERNAME/University-Management-System.git
cd University-Management-System
```

#### 2. Créer l'environnement virtuel
```bash
python -m venv .env
```

#### 3. Activer l'environnement virtuel

**Windows :**
```bash
.env\Scripts\activate
```

**Linux/Mac :**
```bash
source .env/bin/activate
```

#### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

#### 5. Créer la base de données PostgreSQL
```sql
CREATE DATABASE university_db;
```

#### 6. Configurer les variables d'environnement

Créez un fichier `config.env` à la racine :
```env
# DJANGO SETTINGS
SECRET_KEY=votre-cle-secrete-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# DATABASE SETTINGS
DB_ENGINE=django.db.backends.postgresql
DB_NAME=university_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# JWT SETTINGS
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=7

# CORS SETTINGS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# TIMEZONE & LANGUAGE
TIME_ZONE=Africa/Douala
LANGUAGE_CODE=fr-fr

# PAGINATION
PAGE_SIZE=20
```

#### 7. Appliquer les migrations
```bash
python manage.py migrate
```

#### 8. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

#### 9. Lancer le serveur
```bash
python manage.py runserver
```

Le serveur sera accessible sur : **http://localhost:8000 ou http://127.0.0.1:8000**

---

## ⚙️ Configuration

### Ports utilisés

- **Backend Django :** 8000
- **PostgreSQL :** 5432
- **Frontend (futur) :** 3000

---

## 📖 Utilisation

### Interface d'administration

Accédez à l'interface d'administration Django :
```
http://localhost:8000/admin/ ou http://127.0.0.1:8000/admin/
```

### Documentation API (Swagger)

Documentation interactive de l'API :
```
http://localhost:8000/api/docs/ ou http://127.0.0.1:8000/api/docs/
```

### Schéma OpenAPI
```
http://localhost:8000/api/schema/ ou http://127.0.0.1:8000/api/schema
```

---

## 🔌 API Documentation

### Authentification

Toutes les requêtes API (sauf `/api/core/auth/login/`) nécessitent un token JWT.

#### Obtenir un token
```bash
curl -X POST http://localhost:8000/api/core/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'
```

**Réponse :**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@university.cm"
  }
}
```

#### Utiliser le token
```bash
curl -X GET http://localhost:8000/api/facultes/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Endpoints principaux

#### **Authentification**
```
POST /api/auth/login/              # Connexion
POST /api/auth/refresh/            # Rafraîchir le token
```

#### **Utilisateurs (Sprint 1)**
```
GET  /api/users/                   # Liste des utilisateurs
POST /api/users/                   # Créer un utilisateur
GET  /api/users/me/                # Utilisateur connecté
POST /api/users/{id}/change-password/  # Changer mot de passe
GET  /api/roles/                   # Gestion des rôles
GET  /api/permissions/             # Gestion des permissions
```

#### **Structure académique (Sprint 2)**
```
GET  /api/annees-academiques/      # Années académiques
POST /api/annees-academiques/{id}/activate/  # Activer une année
GET  /api/facultes/                # Facultés
GET  /api/facultes/{id}/statistiques/  # Statistiques d'une faculté
GET  /api/departements/            # Départements
GET  /api/filieres/                # Filières
GET  /api/matieres/                # Matières
```

#### **Étudiants et Enseignants (Sprint 3)**
```
GET  /api/etudiants/               # Liste des étudiants
POST /api/etudiants/               # Créer un étudiant
GET  /api/etudiants/{id}/inscriptions/  # Inscriptions d'un étudiant
GET  /api/etudiants/statistiques/  # Statistiques étudiants

GET  /api/enseignants/             # Liste des enseignants
GET  /api/enseignants/{id}/charge-horaire/  # Charge horaire
GET  /api/enseignants/statistiques/  # Statistiques enseignants

GET  /api/inscriptions/            # Inscriptions
POST /api/inscriptions/{id}/payer/  # Enregistrer un paiement

GET  /api/attributions/            # Attributions enseignants
```

#### **Évaluations et Notes (Sprint 4)**
```
GET  /api/types-evaluations/       # Types d'évaluations
GET  /api/evaluations/             # Évaluations
POST /api/evaluations/{id}/dupliquer/  # Dupliquer une évaluation
GET  /api/evaluations/{id}/statistiques/  # Statistiques

GET  /api/notes/                   # Notes
POST /api/notes/saisie-multiple/   # Saisir plusieurs notes
GET  /api/notes/par-etudiant/{id}/ # Notes d'un étudiant

GET  /api/resultats/               # Résultats
POST /api/resultats/calculer-moyenne/  # Calculer moyenne
GET  /api/resultats/bulletin/{id}/ # Bulletin complet

GET  /api/sessions-deliberation/   # Sessions de délibération
POST /api/sessions-deliberation/{id}/generer-decisions/  # Générer décisions
POST /api/sessions-deliberation/{id}/cloturer/  # Clôturer session
GET  /api/decisions-jury/          # Décisions du jury
```

#### **Emploi du temps (Sprint 5)**
```
GET  /api/batiments/               # Bâtiments
GET  /api/batiments/{id}/salles/   # Salles d'un bâtiment
GET  /api/batiments/statistiques/  # Statistiques

GET  /api/salles/                  # Salles
GET  /api/salles/{id}/disponibilite/  # Vérifier disponibilité
GET  /api/salles/disponibles/      # Salles disponibles pour un créneau
GET  /api/salles/statistiques/     # Statistiques

GET  /api/creneaux/                # Créneaux horaires
GET  /api/creneaux/par-jour/       # Créneaux groupés par jour

GET  /api/cours/                   # Cours programmés
POST /api/cours/emploi-du-temps/   # Générer emploi du temps par filière
GET  /api/cours/par-enseignant/{id}/  # Cours d'un enseignant
GET  /api/cours/statistiques/      # Statistiques

POST /api/conflits/detecter/       # Détecter conflits automatiquement
POST /api/conflits/{id}/resoudre/  # Marquer conflit résolu
GET  /api/conflits/statistiques/   # Statistiques des conflits
```

### Format des réponses

Toutes les listes sont paginées :
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/etudiants/?page=2",
  "previous": null,
  "results": [...]
}
```

### Codes de statut HTTP

- **200 OK** : Requête réussie
- **201 Created** : Ressource créée
- **400 Bad Request** : Données invalides
- **401 Unauthorized** : Non authentifié
- **403 Forbidden** : Pas de permission
- **404 Not Found** : Ressource introuvable
- **500 Internal Server Error** : Erreur serveur

---

## 📅 Sprints du projet

| Sprint | Titre | Statut | Modules | Endpoints |
|--------|-------|--------|---------|-----------|
| 1 | Infrastructure de base | ✅ **Terminé** | User, Role, Permission, AuditLog | ~15 |
| 2 | Structure académique | ✅ **Terminé** | AnneeAcademique, Faculte, Departement, Filiere, Matiere | ~35 |
| 3 | Étudiants & Enseignants | ✅ **Terminé** | Etudiant, Enseignant, Inscription, Attribution | ~35 |
| 4 | Notes & Évaluations | ✅ **Terminé** | TypeEvaluation, Evaluation, Note, Resultat, SessionDeliberation, MembreJury, DecisionJury | ~50 |
| 5 | Emploi du temps | ✅ **Terminé** | Batiment, Salle, Creneau, Cours, ConflitSalle | ~45 |
| 6 | Finance avancée | ⏳ **À faire** | Gestion complète des paiements, reçus | - |
| 7 | Inscriptions en ligne | ⏳ À faire | Portail web pour étudiants | - |
| 8 | Bibliothèque | ⏳ À faire | Gestion des livres et emprunts | - |
| 9 | Notifications | ⏳ À faire | Email, SMS, notifications push | - |
| 10 | Reporting | ⏳ À faire | Statistiques avancées, exports | - |

**Progression globale : 50% (5/10 sprints) | ~180 endpoints créés**

---

### Variables d'environnement production
```env
DEBUG=False
ALLOWED_HOSTS=votredomaine.com,www.votredomaine.com
SECRET_KEY=une-cle-tres-secrete-et-longue
```
---

## 🤝 Contributeurs

- **Développeur principal :** MONTHE
- **Framework :** Django REST Framework
- **Assistance :** Claude AI (Anthropic)

---

## 📄 Licence

Ce projet est développé dans un cadre éducatif.

---

## 📞 Support

Pour toute question ou problème :
- **Email :** support@university.cm
- **Documentation :** http://localhost:8000/api/docs/

---

## 🔄 Historique des versions

### Version 0.5.0 (Actuelle - Janvier 2026)
- ✅ Sprint 1 : Infrastructure de base (~15 endpoints)
- ✅ Sprint 2 : Structure académique (~35 endpoints)
- ✅ Sprint 3 : Étudiants et Enseignants (~35 endpoints)
- ✅ Sprint 4 : Notes, Évaluations et Délibérations (~50 endpoints)
- ✅ Sprint 5 : Emploi du temps et Gestion des Conflits (~45 endpoints)
- **Total : ~180 endpoints fonctionnels**

### Prochaines versions
- **0.6.0** : Finance avancée
- **0.7.0** : Inscriptions en ligne
- **0.8.0** : Bibliothèque
- **1.0.0** : Version complète (tous les 10 sprints)

---

## 🎯 Métriques du projet

- **Lines of Code :** ~12,000+
- **Models :** 25
- **Serializers :** 45+
- **ViewSets :** 26
- **API Endpoints :** ~180
- **Admin Interfaces :** 25
- **Migrations :** 10

---

## 🌟 Points forts du système

### **Gestion intelligente des conflits**
Le système détecte automatiquement 3 types de conflits :
- Conflit de salle (2 cours au même créneau)
- Conflit d'enseignant (double programmation)
- Capacité dépassée (trop d'étudiants)

### **Validation en temps réel**
Impossible de créer un cours en conflit - le système bloque immédiatement.

### **Génération automatique**
- Matricules étudiants/enseignants
- Moyennes et mentions
- Emplois du temps
- Détection de conflits

### **Statistiques complètes**
Chaque module offre des statistiques détaillées pour le pilotage.

---

**Fait pour une gestion universitaire moderne**