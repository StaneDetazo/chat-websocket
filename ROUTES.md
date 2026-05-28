# Routes de l'API

## Routes visibles dans Swagger UI (/docs)

### Authentification
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/v1/auth/register` | Inscription |
| POST | `/v1/auth/login` | Connexion |
| POST | `/v1/auth/logout` | Déconnexion |
| GET | `/v1/auth/me` | Profil connecté |

### Utilisateurs
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/v1/users/` | Liste des utilisateurs |
| GET | `/v1/users/{id}` | Détail d'un utilisateur |

### Salons
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/v1/rooms/` | Créer un salon |
| GET | `/v1/rooms/` | Lister les salons |
| GET | `/v1/rooms/{id}` | Détail d'un salon |
| DELETE | `/v1/rooms/{id}` | Supprimer un salon |
| POST | `/v1/rooms/{id}/join` | Rejoindre un salon |
| POST | `/v1/rooms/{id}/leave` | Quitter un salon |
| GET | `/v1/rooms/{id}/members` | Membres d'un salon |
| GET | `/v1/rooms/{id}/messages` | Historique des messages d'un salon |

### Messages
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/v1/messages` | Envoyer un message |
| GET | `/v1/messages/search` | Rechercher des messages |
| PUT | `/v1/messages/{id}` | Modifier un message |
| DELETE | `/v1/messages/{id}` | Supprimer un message (soft delete) |
| POST | `/v1/private-messages` | Envoyer un message privé |
| GET | `/v1/private-messages/{user_id}` | Conversation privée |

### Administration (admin global)
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/v1/admin/users` | Lister tous les utilisateurs |
| POST | `/v1/admin/users/{id}/suspend` | Suspendre un utilisateur |
| POST | `/v1/admin/users/{id}/reactivate` | Réactiver un utilisateur |
| POST | `/v1/admin/rooms` | Créer un salon (admin) |
| GET | `/v1/admin/rooms` | Lister les salons (admin) |
| DELETE | `/v1/admin/rooms/{id}` | Supprimer un salon (admin) |

---

## Routes cachées (hors Swagger, mais fonctionnelles)

Ces routes fonctionnent via API directe mais n'apparaissent pas dans /docs.

### Gestion avancée des salons (admin de salon)
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/v1/rooms/{id}/admins` | Voir les admins d'un salon |
| POST | `/v1/rooms/{id}/members` | Ajouter un membre (admin salon) |
| DELETE | `/v1/rooms/{id}/members/{user_id}` | Retirer un membre (admin salon) |
| POST | `/v1/rooms/{id}/admins` | Promouvoir un admin (admin salon) |
| DELETE | `/v1/rooms/{id}/admins/{user_id}` | Rétrograder un admin (admin salon) |
| POST | `/v1/rooms/{id}/warnings` | Avertir un membre (admin salon ou global) |

### Administration des avertissements (admin global)
| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/v1/admin/warnings` | Donner un avertissement |
| GET | `/v1/admin/warnings/user/{user_id}` | Avertissements d'un utilisateur |
| GET | `/v1/admin/warnings/room/{room_id}` | Avertissements d'un salon |

### Liste brute (tous messages)
| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/v1/messages` | Tous les messages accessibles |

---

## WebSocket (hors Swagger)

| Route | Description |
|-------|-------------|
| `ws://host:8000/ws?token=<jwt>` | Connexion générale au chat temps réel |
| `ws://host:8000/ws/rooms/{room_id}?token=<jwt>` | Connexion directe à un salon |

### Événements WebSocket

**Client → Serveur :**
- `{"event": "join_room", "room_id": 1}`
- `{"event": "leave_room", "room_id": 1}`
- `{"event": "message", "room_id": 1, "content": "..."}`
- `{"event": "private_message", "receiver_id": 2, "content": "..."}`

**Serveur → Client :**
- `{"event": "connected", ...}`
- `{"event": "message", ...}`
- `{"event": "private_message", ...}`
- `{"event": "user_joined", ...}`
- `{"event": "user_left", ...}`
- `{"event": "error", ...}`
