# Guide pour obtenir un jeton d'accès à l'API Albert

Ce document vous guide à travers les étapes pour obtenir et gérer vos jetons d'accès pour l'API Albert.

### Étape 1 : Obtenir une clé d'API temporaire

Commencez par obtenir une clé d'API temporaire qui vous permettra de faire des requêtes initiales. Remplacez `<votre adresse email>` et `<votre mot de passe>` par vos informations d'identification :

```bash
curl -X POST -H "Content-Type: application/json" -d '{"email":"<votre adresse email>","password":"<votre mot de passe>"}' https://albert.etalab.gouv.fr/api/v2/sign_in
```

### Étape 2 : Enregistrez la clé d'API temporaire

Enregistrez la clé d'API temporaire obtenu dans une variable d'environnement pour faciliter son utilisation dans les requêtes futures :

```bash
export ALBERT_API_KEY=<le jeton obtenu>
```

### Étape 3 : Créer un jeton API

Une fois la clé d'API temporaire enregistrée, vous pouvez créer un jeton API permanent avec la commande suivante. Remplacez `my_token_name` par un nom significatif pour votre jeton :

```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ALBERT_API_KEY" -d '{"name":"my_token_name"}' https://albert.etalab.gouv.fr/api/v2/user/token/new
```

### Étape 4 : Lister vos jetons

Pour voir tous les jetons que vous avez créés, utilisez cette commande :

```bash
curl -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $ALBERT_API_KEY" https://albert.etalab.gouv.fr/api/v2/user/token
```

### Étape 5 : Supprimer un jeton

Pour supprimer un jeton spécifique, remplacez `$ALBERT_API_TOKEN` par le jeton que vous souhaitez supprimer :

```bash
curl -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $ALBERT_API_KEY" https://albert.etalab.gouv.fr/api/v2/user/token/$ALBERT_API_TOKEN
```

*Assurez-vous de sécuriser vos jetons et de ne les partager avec personne.*
