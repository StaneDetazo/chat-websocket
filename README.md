# Chat Temps Réel avec WebSocket

Application de messagerie temps réel pour une université togolaise — étudiants et professeurs communiquent en temps réel, en privé ou en groupe.

## Stack Technique

- **API REST** : FastAPI (Python)
- **WebSocket** : Communication temps réel
- **Authentification** : JWT (JSON Web Token)
- **Base de données** : MySQL via SQLAlchemy ORM
- **Hachage** : PBKDF2-SHA256

## Prérequis

- Python 3.12+
- MySQL 8+
- `pip` (gestionnaire de paquets Python)

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-repo> chat-websocket
cd chat-websocket

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou : venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres MySQL

# 5. Lancer le serveur
uvicorn app.main:app --reload
```

Le serveur démarre sur `http://localhost:8000`.

## Documentation Interactive

Une fois le serveur lancé :

- **Swagger UI** : http://localhost:8000/docs
- **Redoc** : http://localhost:8000/redoc

## Structure du Projet

```
chat-websocket/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── auth.py       # Authentification (register, login, logout, me)
│   │       ├── users.py      # Gestion des utilisateurs
│   │       ├── rooms.py      # Salons + gestion membres/admins/avertissements
│   │       ├── messages.py   # Messages (publics, privés, recherche, soft delete)
│   │       └── admin.py      # Administration globale (suspendre, gérer, avertir)
│   ├── crud/
│   │   ├── user.py           # Opérations CRUD utilisateurs
│   │   ├── room.py           # Opérations CRUD salons + admins
│   │   ├── message.py        # Opérations CRUD messages (soft delete)
│   │   └── warning.py        # Opérations CRUD avertissements
│   ├── models/
│   │   ├── base.py           # Base déclarative SQLAlchemy
│   │   ├── user.py           # Modèle utilisateur
│   │   ├── room.py           # Modèle salon + RoomAdmin + Warning
│   │   ├── message.py        # Modèle message (soft delete)
│   │   └── warning.py        # Modèle avertissement
│   ├── schemas/
│   │   ├── user.py           # Schémas Pydantic utilisateur
│   │   ├── room.py           # Schémas Pydantic salon + admin
│   │   ├── message.py        # Schémas Pydantic message
│   │   └── warning.py        # Schémas Pydantic avertissement
│   ├── websocket/
│   │   └── handler.py        # Gestionnaire WebSocket temps réel
│   ├── config.py             # Configuration (variables d'environnement)
│   ├── database.py           # Connexion MySQL + initialisation
│   ├── dependencies.py       # Dépendances FastAPI (auth, DB)
│   ├── security.py           # JWT + hachage mots de passe
│   └── main.py               # Point d'entrée de l'application
├── .env                      # Variables d'environnement (ne pas committer)
├── .env.example              # Exemple de configuration
├── requirements.txt          # Dépendances Python
└── README.md
```

## API REST (v1)

### Authentification

| Méthode | Route | Description | Auth |
|---------|-------|-------------|------|
| `POST` | `/v1/auth/register` | Inscription | Non |
| `POST` | `/v1/auth/login` | Connexion | Non |
| `POST` | `/v1/auth/logout` | Déconnexion | Oui |
| `GET` | `/v1/auth/me` | Profil utilisateur connecté | Oui |

**Inscription** — `POST /v1/auth/register`
```json
{
  "username": "jean.dupont",
  "password": "motdepasse123"
}
```
Réponse : token JWT + informations utilisateur.

**Connexion** — `POST /v1/auth/login`
```json
{
  "username": "jean.dupont",
  "password": "motdepasse123"
}
```
Réponse : token JWT + informations utilisateur.

### Utilisateurs

| Méthode | Route | Description | Auth |
|---------|-------|-------------|------|
| `GET` | `/v1/users/` | Liste des utilisateurs | Oui |
| `GET` | `/v1/users/{id}` | Détail d'un utilisateur | Oui |

### Salons

| Méthode | Route | Description | Auth |
|---------|-------|-------------|------|
| `POST` | `/v1/rooms/` | Créer un salon (vous devenez admin) | Oui |
| `GET` | `/v1/rooms/` | Lister les salons | Oui |
| `GET` | `/v1/rooms/{id}` | Détail d'un salon (membres, admins) | Oui |
| `DELETE` | `/v1/rooms/{id}` | Supprimer un salon | Oui\* |
| `POST` | `/v1/rooms/{id}/join` | Rejoindre un salon | Oui |
| `POST` | `/v1/rooms/{id}/leave` | Quitter un salon | Oui |
| `GET` | `/v1/rooms/{id}/members` | Membres d'un salon | Oui |
| `POST` | `/v1/rooms/{id}/members` | Ajouter un membre (admin salon) | Oui |
| `DELETE` | `/v1/rooms/{id}/members/{user_id}` | Retirer un membre (admin salon) | Oui |
| `GET` | `/v1/rooms/{id}/admins` | Admins du salon | Oui |
| `POST` | `/v1/rooms/{id}/admins` | Promouvoir un admin (admin salon) | Oui |
| `DELETE` | `/v1/rooms/{id}/admins/{user_id}` | Rétrograder un admin (admin salon) | Oui |
| `POST` | `/v1/rooms/{id}/warnings` | Avertir un membre (admin salon ou global) | Oui |

\* Réservé au créateur, à un admin du salon, ou à l'admin global.

**Création d'un salon** — `POST /v1/rooms/`
```json
{
  "name": "salle-etude",
  "description": "Salle pour les révisions",
  "room_type": "public"
}
```
Types de salon : `public`, `private`, `readonly` (lecture seule).

Le créateur est automatiquement promu **admin du salon**.

**Ajouter un membre (admin)** — `POST /v1/rooms/{id}/members`
```json
{"user_id": 3}
```

**Promouvoir un admin (admin)** — `POST /v1/rooms/{id}/admins`
```json
{"user_id": 3}
```

### Messages

| Méthode | Route | Description | Auth |
|---------|-------|-------------|------|
| `POST` | `/v1/messages` | Envoyer un message | Oui |
| `GET` | `/v1/messages` | Tous les messages | Oui |
| `GET` | `/v1/messages/search?q=...` | Rechercher des messages | Oui |
| `PUT` | `/v1/messages/{id}` | Modifier un message | Oui\* |
| `DELETE` | `/v1/messages/{id}` | Supprimer un message (soft delete) | Oui\*\* |
| `GET` | `/v1/rooms/{id}/messages` | Historique d'un salon | Oui |
| `POST` | `/v1/private-messages` | Message privé | Oui |
| `GET` | `/v1/private-messages/{user_id}` | Conversation privée | Oui |

\* Réservé au propriétaire du message.
\*\* Réservé au propriétaire, à un admin du salon, ou à l'admin global. Le message est masqué (soft delete) : le contenu est remplacé par "Ce message a été supprimé".

**Envoyer un message dans un salon** — `POST /v1/messages`
```json
{
  "room_id": 1,
  "content": "Bonjour tout le monde!"
}
```

**Envoyer un message privé** — `POST /v1/private-messages`
```json
{
  "receiver_id": 2,
  "content": "Salut, comment ça va?"
}
```

### Administration (admin global uniquement)

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/v1/admin/users` | Lister tous les utilisateurs |
| `POST` | `/v1/admin/users/{id}/suspend` | Suspendre un utilisateur |
| `POST` | `/v1/admin/users/{id}/reactivate` | Réactiver un utilisateur |
| `POST` | `/v1/admin/rooms` | Créer un salon |
| `GET` | `/v1/admin/rooms` | Lister les salons avec membres et admins |
| `DELETE` | `/v1/admin/rooms/{id}` | Supprimer un salon |
| `POST` | `/v1/admin/warnings` | Donner un avertissement à un utilisateur |
| `GET` | `/v1/admin/warnings/user/{id}` | Avertissements reçus par un utilisateur |
| `GET` | `/v1/admin/warnings/room/{id}` | Avertissements dans un salon |

**Avertir un utilisateur** — `POST /v1/admin/warnings`
```json
{
  "user_id": 3,
  "room_id": 1,
  "reason": "Non-respect des règles du salon"
}
```

## WebSocket — Chat Temps Réel

### Connexion

```javascript
// Connexion générale
const ws = new WebSocket("ws://localhost:8000/ws?token=<votre_token_jwt>");

// Connexion directe à un salon
const ws = new WebSocket("ws://localhost:8000/ws/rooms/1?token=<votre_token_jwt>");
```

### Événements (client → serveur)

**Rejoindre un salon**
```json
{"event": "join_room", "room_id": 1}
```

**Quitter un salon**
```json
{"event": "leave_room", "room_id": 1}
```

**Envoyer un message dans un salon**
```json
{"event": "message", "room_id": 1, "content": "Bonjour à tous!"}
```

**Envoyer un message privé**
```json
{"event": "private_message", "receiver_id": 2, "content": "Salut en privé"}
```

### Événements (serveur → client)

**Connexion réussie**
```json
{"event": "connected", "message": "Bienvenue {username}! Vous êtes connecté au chat temps réel."}
```

**Nouveau message dans un salon**
```json
{
  "event": "message",
  "room_id": 1,
  "message_id": 42,
  "sender_id": 1,
  "sender_username": "jean.dupont",
  "content": "Bonjour à tous!",
  "created_at": "2026-05-28T10:30:00"
}
```

**Message privé reçu**
```json
{
  "event": "private_message",
  "message_id": 43,
  "sender_id": 1,
  "sender_username": "jean.dupont",
  "content": "Salut en privé",
  "receiver_id": 2,
  "receiver_username": "marie.curie",
  "created_at": "2026-05-28T10:31:00"
}
```

**Notification utilisateur**
```json
{"event": "user_joined", "room_id": 1, "user_id": 1, "username": "jean.dupont", "message": "jean.dupont a rejoint le salon"}
```
```json
{"event": "user_left", "room_id": 1, "user_id": 1, "username": "jean.dupont", "message": "jean.dupont a quitté le salon"}
```

**Erreur**
```json
{"event": "error", "message": "Ce salon est en lecture seule. Vous ne pouvez pas y écrire."}
```

## Gestion des Erreurs

| Code | Message | Situation |
|------|---------|-----------|
| 401 | Token invalide ou expiré | Connexion refusée (REST + WebSocket) |
| 401 | Nom d'utilisateur ou mot de passe incorrect | Échec de connexion |
| 403 | Compte suspendu | Utilisateur désactivé par un admin |
| 403 | Salon lecture seule | Tentative d'écriture dans un salon `readonly` |
| 403 | Vous n'êtes pas admin de ce salon | Action réservée aux admins du salon |
| 403 | Accès réservé aux administrateurs | Action réservée à l'admin global |
| 409 | Nom d'utilisateur déjà utilisé | Duplication lors de l'inscription |
| 409 | Salon déjà existant | Duplication lors de la création |
| 429 | Trop de requêtes | Rate limiting HTTP (60 req/min) |
| 429 | Trop de messages envoyés (WebSocket) | Rate limiting WebSocket (10 msg/10s) |
| 400 | Message > 2000 caractères | Message trop long |

## Sécurité

- **Mots de passe** : hachés avec PBKDF2-SHA256 (jamais stockés en clair)
- **JWT** : tokens signés avec HMAC-SHA256, expiration configurable
- **Rate Limiting** : 60 requêtes HTTP/min par IP, 10 messages WebSocket/10s
- **Validation** : tous les inputs sont validés par Pydantic
- **Soft Delete** : les messages supprimés sont masqués, pas effacés définitivement
- **Hiérarchie des rôles** :
  - **Admin global** (`is_admin=True`) : suspend/réactive, gère tous les salons, donne des avertissements
  - **Admin de salon** (table `room_admins`) : gère les membres, les admins, les avertissements dans son salon
  - **Utilisateur simple** : rejoint les salons, envoie des messages, supprime ses propres messages
- **Comptes** : suspension possible par un administrateur global
- **Channels** : les salons `readonly` bloquent les écritures

## Exemple d'Utilisation (cURL)

```bash
# 1. Inscription
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "jean", "password": "secret123"}'

# 2. Connexion (récupérer le token)
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "jean", "password": "secret123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 3. Créer un salon (vous devenez admin)
curl -X POST http://localhost:8000/v1/rooms/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "general", "room_type": "public"}'

# 4. Rejoindre un salon
curl -X POST http://localhost:8000/v1/rooms/1/join \
  -H "Authorization: Bearer $TOKEN"

# 5. Envoyer un message
curl -X POST http://localhost:8000/v1/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"room_id": 1, "content": "Bonjour!"}'

# 6. Historique du salon
curl -X GET http://localhost:8000/v1/rooms/1/messages \
  -H "Authorization: Bearer $TOKEN"

# 7. Rechercher des messages
curl -X GET "http://localhost:8000/v1/messages/search?q=bonjour" \
  -H "Authorization: Bearer $TOKEN"

# 8. Ajouter un membre (admin du salon)
curl -X POST http://localhost:8000/v1/rooms/1/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'

# 9. Promouvoir un admin (admin du salon)
curl -X POST http://localhost:8000/v1/rooms/1/admins \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'

# 10. Avertir un membre (admin du salon ou admin global)
curl -X POST http://localhost:8000/v1/rooms/1/warnings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2, "reason": "Spam dans le salon"}'

# 11. Supprimer un message (soft delete)
curl -X DELETE http://localhost:8000/v1/messages/1 \
  -H "Authorization: Bearer $TOKEN"

# 12. Message privé
curl -X POST http://localhost:8000/v1/private-messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"receiver_id": 2, "content": "Salut en privé"}'
```

## Configuration

Variables d'environnement (fichier `.env`) :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion MySQL | `mysql+pymysql://root:@localhost:3306/chat_db` |
| `SECRET_KEY` | Clé secrète JWT | (à générer) |
| `ALGORITHM` | Algorithme JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de validité du token | `60` |
| `DEBUG` | Mode debug | `true` |

## Notes sur les nouvelles tables

Le projet utilise `Base.metadata.create_all()` qui crée automatiquement les tables manquantes au démarrage. Les nouvelles tables (`room_admins`, `warnings`) et les nouvelles colonnes (`is_deleted`, `deleted_at`) seront créées automatiquement.

En développement, si vous aviez déjà une base existante, supprimez-la et relancez :
```sql
DROP DATABASE chat_db;
CREATE DATABASE chat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
