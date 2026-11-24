# UE-AD-A1-REST & UE-AD-A1-MIXTE

## Martin VIDAL & Yann LACAZE

## Présentation

Movie et Booking exposent une API GraphQL.

User et Schedule exposent une API REST.

## Lancer le projet

Installez Docker et Docker Compose, démarrez Docker, puis lancez depuis la racine
du projet :

```bash
sh launch.sh
```

Le script copie les fichiers communs `requirements.txt` et `lib/utils.py` dans
chaque service, puis construit et démarre les conteneurs. Il écrase les copies
locales de ces fichiers. Pour arrêter le projet, utilisez `Ctrl+C`.

## Les services

Tous les services sont écrits en Python avec Flask et sont exécutés dans des
conteneurs Docker.

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
