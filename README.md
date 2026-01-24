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
- [Roadmap](#roadmap)
- [Contributeurs](#contributeurs)

---

## 📖 À propos

University Management System (UMS) est une application web complète pour la gestion d'une université. Elle permet de gérer les étudiants, les enseignants, les inscriptions, les notes, les évaluations, les délibérations, les emplois du temps, la bibliothèque et bien plus encore.

**Statut du projet :** 🚧 En développement actif (6/12 sprints terminés - 50%)

---

## ✨ Fonctionnalités

### ✅ Fonctionnalités implémentées (Sprints 1-7)

#### 🔐 Sprint 1 : Infrastructure de base
**Authentification et gestion des utilisateurs**

- Authentification JWT (Access + Refresh tokens)
- Gestion des utilisateurs (User, Role, Permission)
- Système de permissions granulaires
- Système d'audit (logs des actions)
- Interface d'administration Django
- **API Endpoints :** ~25

**Modèles :**
- User (utilisateur personnalisé)
- Role (rôles utilisateurs)
- Permission (permissions granulaires)
- AuditLog (traçabilité des actions)

---

#### 🏛️ Sprint 2 : Structure académique
**Organisation hiérarchique de l'université**

- Gestion des années académiques (avec activation)
- Gestion des facultés (avec statistiques)
- Gestion des départements (rattachés aux facultés)
- Gestion des filières (Licence, Master, Doctorat, DUT, BTS)
- Gestion des matières (avec CM, TD, TP)
- Relations hiérarchiques : Université → Faculté → Département → Filière → Matière
- **API Endpoints :** ~40

**Modèles :**
- AnneeAcademique
- Faculte
- Departement
- Filiere
- Matiere

**Fonctionnalités clés :**
- Activation/désactivation des années académiques
- Statistiques par faculté (nb départements, filières, étudiants)
- Chef de département assignable
- Coefficients et crédits ECTS par matière

---

#### 👥 Sprint 3 : Étudiants et Enseignants
**Gestion complète des acteurs universitaires**

- Gestion des étudiants (profils complets avec photos)
- Génération automatique de matricules (format : ETUYYYY###)
- Gestion des enseignants (profils, grades, CV)
- Génération automatique de matricules enseignants (format : ENSYYYY###)
- Inscriptions des étudiants avec gestion des paiements
- Attributions des enseignants aux matières (CM, TD, TP)
- Calcul automatique de charge horaire
- Statistiques détaillées (sexe, nationalité, grade)
- **API Endpoints :** ~35

**Modèles :**
- Etudiant
- Enseignant
- Inscription
- Attribution

**Fonctionnalités clés :**
- Matricules auto-générés uniques
- Suivi des paiements des inscriptions
- Charge horaire calculée automatiquement
- Validation : 1 enseignant par type de cours (CM/TD/TP)

---

#### 📊 Sprint 4 : Notes, Évaluations et Délibérations
**Système complet de gestion académique**

**Évaluations :**
- Types d'évaluations (Devoir, Examen, Rattrapage, TD, TP, Projet)
- Création avec coefficient et barème personnalisables
- Duplication d'évaluations pour réutilisation
- Statistiques automatiques (moyenne, min, max, répartition)

**Notes :**
- Saisie individuelle ou en lot
- Gestion des absences aux évaluations
- Conversion automatique sur base 20
- Appréciations automatiques (Excellent, Très bien, Bien, Passable, Insuffisant)
- Validation : note ≤ barème

**Résultats :**
- Calcul automatique des moyennes pondérées
- Génération des mentions (Passable à Excellent)
- Détermination du statut (ADMIS, AJOURNÉ, RATTRAPAGE)
- Attribution automatique des crédits ECTS
- Bulletins complets par étudiant

**Délibérations :**
- Sessions de délibération (filière, niveau, semestre)
- Composition du jury (Président, Membres, Secrétaire)
- Génération automatique des décisions
- Calcul des rangs et classements
- Statuts : PREVUE, EN_COURS, TERMINEE, VALIDEE
- Procès-verbaux officiels
- Taux de réussite automatique
- **API Endpoints :** ~40

**Modèles :**
- TypeEvaluation
- Evaluation
- Note
- Resultat
- SessionDeliberation
- MembreJury
- DecisionJury

---

#### 📅 Sprint 5 : Emploi du temps et Gestion des Conflits
**Planification intelligente des cours**

**Bâtiments et Salles :**
- Gestion des bâtiments (code, nom, étages)
- Gestion des salles (types : COURS, TD, TP, AMPHI, CONFERENCE)
- Capacités et équipements
- Taux d'occupation en temps réel
- Vérification de disponibilité

**Créneaux horaires :**
- Gestion des créneaux (jour, heure début/fin)
- Calcul automatique de la durée
- Validation : heure fin > heure début
- Organisation par jour de semaine

**Cours et Programmation :**
- Programmation des cours (matière, enseignant, filière, salle, créneau)
- Types : CM, TD, TP
- Validation de capacité
- **Validation en temps réel :**
  - Détection conflit de salle
  - Détection conflit d'enseignant
  - Vérification capacité vs effectif
- Génération d'emploi du temps par filière/semestre
- Consultation par enseignant
- Duplication de cours

**Détection et Gestion des Conflits :**
- Détection automatique de 3 types :
  - Conflit de salle (2 cours simultanés, même salle)
  - Conflit d'enseignant (1 prof, 2 cours en même temps)
  - Capacité dépassée (effectif > capacité salle)
- Statuts : DETECTE, EN_COURS, RESOLU, IGNORE
- Tracking de résolution (date, solution appliquée)
- Statistiques des conflits
- **API Endpoints :** ~45

**Modèles :**
- Batiment
- Salle
- Creneau
- Cours
- ConflitSalle

---

#### 📚 Sprint 6 : Bibliothèque Universitaire ✨ NOUVEAU
**Gestion complète de la bibliothèque**

**Catalogage des livres :**
- Catégorisation (Sciences, Littérature, Informatique, etc.)
- Informations bibliographiques complètes (ISBN, titre, auteur, éditeur, année)
- Gestion des exemplaires (stock total/disponible)
- Localisation physique dans la bibliothèque
- Résumé et description
- Recherche avancée (titre, auteur, ISBN, catégorie)

**Gestion des emprunts :**
- Création d'emprunt avec validations :
  - Vérification disponibilité du livre
  - Limite de 5 emprunts simultanés par étudiant
  - Blocage si pénalités impayées
- Enregistrement des retours
- Calcul automatique des pénalités (100 FCFA/jour de retard)
- Mise à jour automatique des statuts :
  - EN_COURS : Emprunt actif
  - EN_RETARD : Dépassement de la date de retour
  - RETOURNE : Livre rendu
  - ANNULE : Emprunt annulé
- Gestion intelligente du stock :
  - Décrémentation automatique à l'emprunt
  - Incrémentation automatique au retour

**Actions personnalisées :**
- `/categories/{id}/livres/` : Livres d'une catégorie
- `/livres/disponibles/` : Livres en stock
- `/livres/{id}/historique/` : Historique des emprunts
- `/livres/statistiques/` : Stats bibliothèque
- `/emprunts/{id}/retour/` : Enregistrer un retour
- `/emprunts/en_cours/` : Emprunts actifs
- `/emprunts/en_retard/` : Emprunts en retard (mise à jour auto)
- `/emprunts/statistiques/` : Stats complètes

**Statistiques et rapports :**
- Nombre total de livres et exemplaires
- Taux de disponibilité
- Répartition par catégorie
- Emprunts en cours/retard/retournés
- Total des pénalités
- Livre le plus emprunté
- **API Endpoints :** ~30

**Modèles :**
- CategoriesLivre
- Livre
- Emprunt

**Fonctionnalités clés :**
- Système de pénalités automatique
- Validation métier complète
- Historique complet des transactions
- Détection automatique des retards
- Blocage intelligent des emprunts


### ✅ Sprint 7 : Absences & Présences ✨ NOUVEAU
**Gestion complète de l'assiduité des étudiants**

**Feuilles de présence :**
- Création automatique de feuilles par cours
- Génération automatique des enregistrements de présence pour tous les étudiants inscrits
- Marquage des présences (PRESENT, ABSENT, RETARD)
- Marquage en masse de plusieurs étudiants en une seule requête
- Fermeture/verrouillage des feuilles avec recalcul automatique des statistiques
- Calcul automatique du taux de présence par cours
- Observations de l'enseignant
- Statuts : OUVERTE (modifiable), FERMEE (verrouillée), ANNULEE

**Gestion des présences :**
- Enregistrement individuel de chaque étudiant (statut + heure d'arrivée)
- Calcul automatique des minutes de retard
- Marquage des absences justifiées/non justifiées
- Remarques par étudiant
- Historique complet des présences par étudiant

**Justificatifs d'absence :**
- Upload de documents justificatifs (PDF, images)
- Types : MEDICAL, ADMINISTRATIF, FAMILIAL, AUTRE
- Workflow de validation :
  - EN_ATTENTE : Justificatif soumis
  - VALIDE : Approuvé par l'administration
  - REJETE : Refusé avec commentaire
- Validation automatique des absences lors de l'approbation
- Calcul de la durée couverte (en jours)
- Tracking complet (date soumission, date traitement)
- Actions en masse dans l'admin Django

**Actions personnalisées :**

*Feuilles de présence :*
- `/feuilles-presence/{id}/fermer/` : Verrouiller une feuille
- `/feuilles-presence/{id}/marquer-presences/` : Marquer plusieurs présences
- `/feuilles-presence/{id}/liste-presences/` : Liste complète des présences
- `/feuilles-presence/par-cours/` : Feuilles d'un cours spécifique
- `/feuilles-presence/statistiques/` : Stats globales

*Présences :*
- `/presences/par-etudiant/` : Présences d'un étudiant avec stats
- `/presences/absents/` : Liste des absences (filtre justifié/non justifié)
- `/presences/retards/` : Liste des retards avec minutes calculées
- `/presences/taux-assiduite/` : Calcul détaillé du taux d'assiduité
  - Niveaux : EXCELLENT (≥90%), BON (≥75%), MOYEN (≥60%), FAIBLE (<60%)

*Justificatifs :*
- `/justificatifs/{id}/valider/` : Valider et marquer absences comme justifiées
- `/justificatifs/{id}/rejeter/` : Rejeter avec commentaire
- `/justificatifs/en-attente/` : Justificatifs à traiter
- `/justificatifs/par-etudiant/` : Justificatifs d'un étudiant
- `/justificatifs/statistiques/` : Stats complètes (taux validation, délai traitement)

**Statistiques et rapports :**
- Taux de présence par cours et global
- Taux d'assiduité par étudiant (avec niveau)
- Nombre de présents/absents/retards
- Absences justifiées vs non justifiées
- Délai moyen de traitement des justificatifs
- Répartition des justificatifs par type

**Fonctionnalités clés :**
- Génération automatique des présences à la création de feuille
- Recalcul automatique des statistiques
- Validation en masse des justificatifs
- Calcul intelligent des retards (en minutes)
- Workflow complet de justification d'absences
- Historique complet et traçabilité

**Endpoints générés : ~32**

**Modèles :**
- FeuillePresence
- Presence
- JustificatifAbsence

### ✅ Sprint 8 : Finance & Scolarité ✨ NOUVEAU
**Gestion complète des finances universitaires**

**Frais de scolarité :**
- Configuration des tarifs par filière, niveau et année académique
- Montants personnalisables selon les formations
- Système de tranches de paiement (1 à 12 tranches)
- Date limite de paiement configurable
- Activation/désactivation des tarifs
- Calcul automatique du montant par tranche
- Statistiques d'utilisation par filière

**Gestion des paiements :**
- Enregistrement des paiements étudiants
- Modes de paiement multiples :
  - Espèces
  - Virement bancaire
  - Mobile Money (Orange Money, MTN MoMo)
  - Chèque
  - Autre
- Génération automatique de numéros de reçu (format : REC-YYYY-XXXXXX)
- Workflow de validation :
  - EN_ATTENTE : Paiement soumis
  - VALIDE : Paiement confirmé par l'administration
  - REJETE : Paiement refusé
  - ANNULE : Paiement annulé
- Référence de transaction pour traçabilité
- Tracking complet (qui a validé, quand)
- Mise à jour automatique de la facture lors du paiement
- Validation : montant ≤ solde restant

**Bourses et exonérations :**
- Types de bourses :
  - TOTALE : 100% des frais pris en charge
  - PARTIELLE : Pourcentage des frais (0-100%)
  - MONTANT_FIXE : Montant fixe déduit
- Sources de financement :
  - Gouvernement
  - Université
  - Entreprise privée
  - ONG
  - Autre
- Statuts : EN_COURS, SUSPENDUE, TERMINEE, ANNULEE
- Période de validité (date début/fin)
- Calcul automatique du montant de réduction
- Vérification automatique si bourse active
- Conditions de maintien
- Référence de décision d'attribution
- Actions en masse : suspendre/réactiver

**Factures de scolarité :**
- Génération automatique de factures pour les inscriptions
- Numérotation unique auto (format : FACT-YYYY-XXXXXX)
- Calcul automatique :
  - Montant brut (frais de scolarité)
  - Montant réduction (bourses actives)
  - Montant net (brut - réductions)
  - Montant payé (somme des paiements validés)
  - Solde restant (net - payé)
- Statuts automatiques :
  - IMPAYEE : Aucun paiement
  - PARTIELLE : Paiements partiels
  - SOLDEE : Totalement payée
  - ANNULEE : Facture annulée
- Détection automatique des retards (échéance dépassée)
- Calcul du taux de paiement (%)
- Mise à jour automatique lors des paiements

**Actions personnalisées :**

*Frais de scolarité :*
- `/frais-scolarite/actifs/` : Frais actuellement actifs
- `/frais-scolarite/par-filiere/` : Frais d'une filière
- `/frais-scolarite/par-annee/` : Frais d'une année académique
- `/frais-scolarite/statistiques/` : Stats globales

*Paiements :*
- `/paiements/{id}/valider/` : Valider un paiement (enregistre qui et quand)
- `/paiements/en-attente/` : Paiements à valider
- `/paiements/par-etudiant/` : Historique des paiements d'un étudiant
- `/paiements/par-mode/` : Répartition par mode de paiement
- `/paiements/statistiques/` : Stats financières complètes
  - Total encaissé
  - Montant moyen
  - Paiements du mois
  - Paiements en attente

*Bourses :*
- `/bourses/actives/` : Bourses actuellement valides
- `/bourses/par-etudiant/` : Bourses d'un étudiant
- `/bourses/par-source/` : Répartition par source de financement
- `/bourses/{id}/suspendre/` : Suspendre une bourse
- `/bourses/{id}/reactiver/` : Réactiver une bourse suspendue
- `/bourses/statistiques/` : Stats par type et source

*Factures :*
- `/factures/generer/` : Générer automatiquement une facture
  - Récupère frais de scolarité
  - Calcule bourses actives
  - Calcule montant net
  - Crée la facture
- `/factures/impayees/` : Factures non payées avec total
- `/factures/en-retard/` : Factures avec échéance dépassée
- `/factures/soldees/` : Factures totalement payées
- `/factures/par-etudiant/` : Toutes les factures d'un étudiant
- `/factures/statistiques/` : Stats de recouvrement
  - Montant total à encaisser
  - Montant total encaissé
  - **Taux de recouvrement global (%)**
  - Factures en retard
  - Répartition par statut

**Statistiques et rapports :**
- Taux de recouvrement des paiements
- Répartition des paiements par mode
- Total encaissé par période
- Montant moyen des paiements
- Factures en retard avec montants
- Répartition des bourses par type et source
- Nombre d'étudiants par tarif
- Suivi des impayés

**Fonctionnalités clés :**
- Génération automatique des numéros (reçus, factures)
- Workflow complet de validation des paiements
- Calcul automatique des réductions (bourses)
- Mise à jour automatique des factures
- Détection automatique des retards
- Calcul automatique des soldes et statuts
- Actions en masse dans l'admin (validation, suspension)
- Traçabilité complète (qui, quand, combien)
- Validation métier (montant ≤ solde, bourses selon type)

**Endpoints générés : ~45**

**Modèles :**
- FraisScolarite
- Paiement
- Bourse
- Facture

### ✅ Sprint 9 : Communications & Notifications ✨ NOUVEAU
**Système complet de communication intégré**

**Annonces et actualités :**
- Création et gestion d'annonces officielles
- Types d'annonces :
  - GENERALE : Pour tout le monde
  - ETUDIANTS : Étudiants uniquement
  - ENSEIGNANTS : Enseignants uniquement
  - ADMINISTRATION : Personnel administratif
  - URGENTE : Annonces urgentes (priorité haute)
- Workflow de publication :
  - BROUILLON : Annonce en cours de rédaction
  - PUBLIEE : Annonce visible par le public cible
  - ARCHIVEE : Annonce archivée (non visible)
- Système de priorité (annonces mises en avant)
- Date d'expiration configurable
- Pièces jointes (PDF, images, documents)
- Publication et archivage en un clic
- Détection automatique des annonces expirées

**Système de notifications :**
- Création manuelle ou automatique de notifications
- Types de notifications :
  - INFO : Information générale
  - SUCCES : Confirmation d'action réussie
  - ALERTE : Alerte importante
  - ERREUR : Problème à corriger
- Canaux de diffusion :
  - APP : Notification dans l'application (push)
  - EMAIL : Notification par email
  - SMS : Notification par SMS
- Envoi en masse à plusieurs utilisateurs
- Marquage lu/non lu automatique
- Lien de redirection optionnel
- Tracking complet (envoyée, lue, date)
- Notifications personnalisées par utilisateur

**Messagerie interne :**
- Communication privée entre utilisateurs
- Envoi de messages avec pièces jointes
- Système de réponses (fils de discussion)
- Boîte de réception et messages envoyés
- Marquage lu/non lu
- Archivage des messages
- Conversation complète (vue récursive du fil)
- Validation : impossible de s'envoyer un message à soi-même
- Détection automatique des réponses

**Préférences de notification :**
- Personnalisation par utilisateur
- Préférences par type d'événement :
  - Nouvelles notes
  - Absences
  - Paiements
  - Bibliothèque (retours)
  - Emploi du temps
  - Annonces
  - Nouveaux messages
- Préférences par canal :
  - Activer/désactiver email
  - Activer/désactiver SMS
  - Activer/désactiver push (app)
- Fréquence d'envoi :
  - IMMEDIAT : Notification instantanée
  - QUOTIDIEN : Digest quotidien
  - HEBDOMADAIRE : Digest hebdomadaire
- Création automatique des préférences par défaut
- Mise à jour partielle des préférences

**Actions personnalisées :**

*Annonces :*
- `/annonces/{id}/publier/` : Publier une annonce (change statut + date)
- `/annonces/{id}/archiver/` : Archiver une annonce
- `/annonces/publiees/` : Annonces publiées et non expirées
- `/annonces/urgentes/` : Annonces urgentes uniquement
- `/annonces/par-type/` : Filtrer par type de public
- `/annonces/statistiques/` : Stats globales (total, publiées, par type)

*Notifications :*
- `/notifications/{id}/marquer-lue/` : Marquer comme lue
- `/notifications/marquer-toutes-lues/` : Marquer toutes comme lues
- `/notifications/envoyer-masse/` : Envoyer à plusieurs utilisateurs
- `/notifications/non-lues/` : Liste des non lues
- `/notifications/mes-notifications/` : Notifications de l'utilisateur connecté
- `/notifications/statistiques/` : Stats (total, par type, par canal)

*Messages :*
- `/messages/{id}/marquer-lu/` : Marquer comme lu
- `/messages/{id}/archiver/` : Archiver le message
- `/messages/{id}/desarchivier/` : Désarchiver le message
- `/messages/{id}/repondre/` : Répondre au message (crée réponse liée)
- `/messages/boite-reception/` : Messages reçus (avec compteur non lus)
- `/messages/messages-envoyes/` : Messages envoyés
- `/messages/non-lus/` : Messages non lus
- `/messages/archives/` : Messages archivés
- `/messages/conversation/` : Fil de discussion complet (récursif)
- `/messages/statistiques/` : Stats de l'utilisateur

*Préférences :*
- `/preferences/mes-preferences/` : Récupère préférences (crée si inexistantes)
- `/preferences/mettre-a-jour/` : Met à jour les préférences (partiel)

*Statistiques :*
- `/statistiques/utilisateur/` : Stats de l'utilisateur connecté
  - Notifications non lues
  - Messages non lus
  - Totaux
- `/statistiques/globales/` : Stats système complètes
  - Total annonces, notifications, messages
  - Utilisateurs avec préférences

**Statistiques et rapports :**
- Compteur de notifications non lues
- Compteur de messages non lus
- Répartition des notifications par type et canal
- Répartition des annonces par type
- Statistiques utilisateur personnalisées
- Statistiques globales du système

**Fonctionnalités clés :**
- Assignation automatique auteur/expéditeur depuis utilisateur connecté
- Création automatique des préférences par défaut
- Marquage automatique des dates (lecture, publication, envoi)
- Fil de discussion récursif (messages et réponses)
- Validation métier (expéditeur ≠ destinataire, dates expiration)
- Actions en masse dans l'admin (publier, archiver, marquer lu)
- Envoi de notifications en masse à plusieurs utilisateurs
- Détection automatique des annonces expirées
- Tracking complet de tous les événements

**Endpoints générés : ~50**

**Modèles :**
- Annonce
- Notification
- Message
- PreferenceNotification

---

**Endpoints totaux backend : ~342**

---


### ⏳ Fonctionnalités à venir (Sprints 8-12)

Les 6 prochains sprints couvriront :

- **Sprint 8 :** Finance et scolarité
- **Sprint 9 :** Communications et notifications
- **Sprint 10 :** Ressources et salles avancées
- **Sprint 11 :** Documents administratifs
- **Sprint 12 :** Rapports et analytics

*(Voir section [Roadmap](#roadmap) pour les détails)*

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
---

## 🚀 Installation

### Prérequis

- Python 3.13+
- PostgreSQL 17+
- Git

### Étapes d'installation

#### 1. Cloner le projet
```bash
git clone https://github.com/Ing-MONTHE/University-Management-System.git
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
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

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

Le serveur sera accessible sur : **http://localhost:8000**

---

## ⚙️ Configuration

### Ports utilisés

- **Backend Django :** 8000
- **PostgreSQL :** 5432
- **Frontend (futur) :** 5173

---

## 📖 Utilisation

### Interface d'administration
```
http://localhost:8000/admin/
```

### Documentation API (Swagger)
```
http://localhost:8000/api/docs/
```

### Schéma OpenAPI
```
http://localhost:8000/api/schema/
```

---

## 🔌 API Documentation

### Authentification

#### Obtenir un token
```bash
POST /api/auth/login/
{
  "username": "admin",
  "password": "Admin123!"
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
    "email": "admin@university.cm"
  }
}
```

#### Utiliser le token
```bash
GET /api/facultes/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📅 Sprints du projet

| Sprint | Titre | Statut | Modules | Endpoints |
|--------|-------|--------|---------|-----------|
| 1 | Infrastructure & Auth | ✅ Terminé | User, Role, Permission | ~25 |
| 2 | Structure académique | ✅ Terminé | AnneeAcademique, Faculte, Departement, Filiere, Matiere | ~40 |
| 3 | Étudiants & Enseignants | ✅ Terminé | Etudiant, Enseignant, Inscription, Attribution | ~35 |
| 4 | Évaluations & Notes | ✅ Terminé | Evaluation, Note, Resultat, Deliberation | ~40 |
| 5 | Emploi du temps | ✅ Terminé | Batiment, Salle, Creneau, Cours, Conflit | ~45 |
| 6 | Bibliothèque | ✅ Terminé | Categorie, Livre, Emprunt | ~30 |
| 7 | Absences & Présences | ✅ Terminé | FeuillePresence, Presence, JustificatifAbsence | ~32 |
| 8 | Finance & Scolarité | ✅ Terminé | FraisScolarite, Paiement, Bourse, Facture | ~45 |
| 9 | Communications | ✅ Terminé | Annonce, Notification, Message, PreferenceNotification | ~50 |
| 10 | Ressources avancées | ⏳ À faire | Equipement, Reservation, Maintenance | - |
| 11 | Documents admin | ⏳ À faire | Attestation, Certificat, Releve | - |
| 12 | Analytics & Reports | ⏳ À faire | Dashboard, Rapport, Export | - |

**Progression globale : 75% (9/12 sprints) | ~342 endpoints créés**

---

## 🗺️ Roadmap

### Sprint 7 : Absences & Présences (Prochainement)
**Suivi de l'assiduité des étudiants**

**Fonctionnalités prévues :**
- Feuilles de présence par cours/créneau
- Gestion des absences (justifiées/non justifiées)
- Upload de justificatifs (certificats médicaux, etc.)
- Calcul automatique du taux de présence
- Alertes pour absences répétées (> seuil)
- Statistiques d'assiduité par étudiant/matière
- Rapports de présence pour enseignants

**Endpoints estimés :** ~25

---

### Sprint 8 : Finance & Scolarité
**Gestion complète des finances universitaires**

**Fonctionnalités prévues :**
- Définition des frais de scolarité (par filière, niveau, année)
- Gestion des tranches de paiement
- Enregistrement des paiements (espèces, virement, mobile money)
- Génération automatique de reçus et factures
- Gestion des bourses et exonérations
- Suivi des impayés avec relances
- Statistiques financières (recettes, taux de recouvrement)
- Tableau de bord financier

**Endpoints estimés :** ~35

---

### Sprint 9 : Communications & Notifications
**Système de communication intégré**

**Fonctionnalités prévues :**
- Gestion des annonces et actualités
- Système de notifications push
- Notifications par email (SMTP)
- Notifications par SMS (API Twilio/Nexmo)
- Messagerie interne entre utilisateurs
- Alertes système automatiques :
  - Notes disponibles
  - Emploi du temps modifié
  - Absences répétées
  - Paiements en retard
  - Livres à rendre
- Historique des notifications

**Endpoints estimés :** ~30

---

### Sprint 10 : Ressources & Salles Avancées
**Gestion approfondie des ressources**

**Fonctionnalités prévues :**
- Gestion des équipements (projecteurs, ordinateurs, laboratoires)
- Système de réservation de salles
- Calendrier de disponibilité
- Gestion de la maintenance (préventive, curative)
- Suivi de l'état des équipements
- Historique des interventions
- Statistiques d'utilisation des ressources

**Endpoints estimés :** ~25

---

### Sprint 11 : Documents Administratifs
**Génération automatique de documents officiels**

**Fonctionnalités prévues :**
- Attestations de scolarité (PDF automatique)
- Relevés de notes officiels
- Certificats de diplôme
- Lettres de recommandation
- Documents justificatifs personnalisables
- Templates modifiables
- Signature électronique
- Archivage sécurisé

**Endpoints estimés :** ~20

---

### Sprint 12 : Rapports & Analytics
**Business Intelligence universitaire**

**Fonctionnalités prévues :**
- Tableaux de bord interactifs (directeurs, doyens, admin)
- Statistiques académiques avancées :
  - Taux de réussite par filière/année
  - Évolution des effectifs
  - Performance des enseignants
  - Utilisation des ressources
- Rapports d'activité automatiques
- Exports multiformats (PDF, Excel, CSV)
- Graphiques et visualisations (Chart.js)
- Prédictions et tendances (ML basique)

**Endpoints estimés :** ~30

---

### Sprint 13+ : Frontend React (Phase 2 du projet)
**Interface utilisateur moderne**

**Technologies :**
- React 19+ avec TypeScript
- Tailwind CSS 4+
- Vite (build tool)
- React Router 7
- Recharts (graphiques)

**Modules frontend prévus :**
- Interface d'authentification
- Dashboard administrateur
- Portail étudiant
- Portail enseignant
- Gestion académique
- Bibliothèque en ligne
- Consultation emploi du temps
- Messagerie intégrée

---

## 🎯 Métriques du projet

### Actuellement
- **Lines of Code :** ~26,000+
- **Models :** 39
- **Serializers :** 88+
- **ViewSets :** 41
- **API Endpoints :** ~342
- **Admin Interfaces :** 39
- **Migrations :** 15

### À terme (tous sprints)
- **API Endpoints estimés :** ~400+
- **Models estimés :** ~50+
- **Pages frontend estimées :** ~40+

---

## 🌟 Points forts du système

### **Gestion intelligente des conflits**
Détection automatique en temps réel des conflits de planning (salle, enseignant, capacité).

### **Validation métier complète**
Règles métier implémentées à tous les niveaux (emprunts, inscriptions, notes, cours).

### **Génération automatique**
Matricules, moyennes, emplois du temps, pénalités, décisions de jury.

### **Statistiques en temps réel**
Chaque module offre des statistiques détaillées pour le pilotage.

### **Traçabilité totale**
Historique complet des actions via AuditLog et timestamps sur tous les modèles.

### **Scalabilité**
Architecture modulaire permettant l'ajout facile de nouvelles fonctionnalités.

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

### Version 0.9.0 (Actuelle - Janvier 2026)
- ✅ Sprint 1 : Infrastructure & Auth (~25 endpoints)
- ✅ Sprint 2 : Structure académique (~40 endpoints)
- ✅ Sprint 3 : Étudiants & Enseignants (~35 endpoints)
- ✅ Sprint 4 : Évaluations & Notes (~40 endpoints)
- ✅ Sprint 5 : Emploi du temps (~45 endpoints)
- ✅ Sprint 6 : Bibliothèque (~30 endpoints)
- ✅ Sprint 7 : Absences & Présences (~32 endpoints)
- ✅ Sprint 8 : Finance & Scolarité (~45 endpoints)
- ✅ Sprint 9 : Communications & Notifications (~50 endpoints) ✨ NOUVEAU
- **Total : ~342 endpoints fonctionnels**

### Prochaines versions
- **0.10.0** : Ressources avancées
- **0.11.0** : Documents administratifs
- **1.0.0** : Version backend complète (12 sprints)
- **2.0.0** : Version complète avec frontend React

---

**Développé avec ❤️ pour une gestion universitaire moderne et efficace**