# UE-AD-A1-REST & UE-AD-A1-MIXTE

**Auteurs : Martin Vidal et Yann Lacaze**

## Présentation du projet

Ce projet met en œuvre une application composée de quatre services :

- **User** expose une API REST pour gérer les utilisateurs.
- **Movie** et **Booking** exposent des API GraphQL et utilisent MongoDB.
- **Schedule** propose une API gRPC pour gérer les séances.

Le projet a évolué au fil de plusieurs branches :

- `TP1` contient la version REST.
- `TP2` ajoute GraphQL pour les services Movie et Booking.
- `GRPC-Mango` contient la version complète, avec l'ensemble des services.

## Authentification et rôles

Le service **User** gère l'inscription et la connexion. Après une connexion réussie,
il renvoie un token JWT à utiliser pour les opérations protégées.

1. Créez un compte avec `POST http://localhost:3203/register` :

   ```json
   { "name": "User Test", "password": "mon-mot-de-passe" }
   ```

   Un compte créé reçoit automatiquement le rôle `user`.
2. Connectez-vous avec `POST http://localhost:3203/login`, en envoyant les mêmes
   champs `name` et `password`. La réponse contient `access_token`.
3. Pour une opération protégée, transmettez le token dans l'en-tête HTTP :

   ```text
   Authorization: Bearer <access_token>
   ```

   Pour GraphQL, ajoutez cet en-tête à la requête envoyée à `/graphql`. Pour
   l'appel gRPC de suppression d'un programme, transmettez-le comme métadonnée
   `authorization` avec la valeur `Bearer <access_token>`.

Les utilisateurs de démonstration sont dans `user/databases/users.json` : par
exemple, `Chris Rivers` a le rôle `admin` et `Peter Curley` le rôle `user`
(mot de passe de démonstration : `test`).

Les contrôles de rôles et de propriété actuellement appliqués sont :

- **Admin requis** pour supprimer un film (Movie) ou un programme (Schedule).
- **Propriétaire ou admin** pour supprimer un compte User.
- **Propriétaire uniquement** pour supprimer une réservation Booking.
- Les lectures, ainsi que les autres opérations de création ou modification,
  ne demandent actuellement pas de token.

Cette authentification est prévue pour la démonstration : la clé JWT est
configurée directement dans le code et les contrôles ne couvrent pas toutes les
opérations. Elle ne doit pas être considérée comme une configuration de
production.

## Lancer le projet

Installez Docker et Docker Compose, démarrez Docker, puis lancez depuis la racine
du projet :

```bash
sh launch.sh
```

Le script copie les fichiers communs `requirements.txt`, `lib/utils.py`, `lib/auth.py` dans
chaque service, puis construit et démarre les conteneurs. Il écrase les copies
locales de ces fichiers.

## Les services

Tous les services composants l'application sont :

- **Movie — port 3200** : utilise GraphQL avec Ariadne et stocke les films et
  les acteurs dans MongoDB avec PyMongo. Il permet de rechercher, créer,
  modifier et supprimer des films, ainsi que de consulter leurs acteurs.
  Son point d'entrée est `http://localhost:3200/graphql`.
- **Booking — port 3201** : utilise GraphQL avec Ariadne et stocke les
  réservations dans MongoDB avec PyMongo. Une réservation contient un
  utilisateur et ses séances. Avant de la créer, Booking vérifie auprès de User
  que l'utilisateur existe, puis auprès de Schedule que les films sont
  programmés aux dates demandées. Son point d'entrée est
  `http://localhost:3201/graphql`.
- **Schedule — port 50052** : utilise gRPC pour consulter, créer et
  supprimer les programmes de séances. Les données sont stockées dans un fichier
  JSON du conteneur. Lors de la création d'un programme, Schedule interroge
  Movie en GraphQL pour vérifier que les films existent.
- **User — port 3203** : expose une API REST pour consulter, créer, modifier et
  supprimer des utilisateurs. Les données sont chargées depuis un fichier JSON
  du conteneur.

MongoDB est accessible sur le port `27017` et Mongo Express, son interface web,
sur `http://localhost:8081`. Les fichiers JSON de Movie et Booking servent à
initialiser leurs collections lorsqu'elles n'existent pas encore. Leurs données
sont ensuite lues et modifiées dans MongoDB, sans réimport à chaque démarrage.

## Tester avec Postman

Importez la collection Postman fournie à la racine du projet pour tester les
services REST et GraphQL. Les requêtes gRPC ne sont pas incluses dans cette
collection : dans Postman, créez une requête gRPC vers `localhost:50052` et
chargez le fichier [`schedule.proto`](schedule/schedule.proto).

Exemples de corps de requête :

**GetSchedule**

```json
{
  "value": "20151130"
}
```

**AddSchedule**

```json
{
  "date": "20151206",
  "movies_id": [
    "720d006c-3a57-4b6a-b18f-9b713b073f3c",
    "a8034f44-aee4-44cf-b32c-74cf452aaaae"
  ]
}
```

**DeleteSchedule**

```json
{
  "date": "20151206"
}
```

La suppression d'un programme nécessite un compte `admin`. Ajoutez son JWT
aux métadonnées gRPC avec la clé `authorization` et la valeur
`Bearer <access_token>`.
