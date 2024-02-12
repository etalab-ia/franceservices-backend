# Albert backend

## Préambule

Ce projet contient le code source d'Albert, l'agent conversationnel de l'administration française, développé par les équipes du Datalab de la Direction Interministérielle du Numérique (DINUM). Albert a été créé pour citer ses sources et est spécialisé pour répondre à des questions administratives en français.

Albert est encore en développement et en amélioration continue. Il est conçu pour être utilisé sous la responsabilité d'un agent public.


## Déploiement / *Deployment*

Pour déployer le projet Albert, vous référez à la documentation dédies : [docs/deploiment](./docs/deploiement/). 


## Pré-requis : exécution de PyAlbert

Utilisez l'outil en ligne de commande `pyalbert` pour créer les ensembles de données et les modèles nécessaires. La documentation peut être consultée en exécutant `./pyalbert.py --help` :

1. [x] téléchargement du corpus de données en français -- `pyalbert download`.
2. [x] prétraitement et mise en forme du corpus de données -- `pyalbert make_chunks`.
3. [x] alimenter les moteurs de recherche d'indexation <index/vector> -- `pyalbert index`
3. [ ] affiner les LLMs. Script indépendant situé dans le dépôt `pyalbert`, répertoire `finetuning/`.
4. [x] évaluation des modèles -- `pyalbert evaluate`.

**REMARQUE** : L'étape 3 cache une étape qui consiste à construire les embeddings à partir de morceaux de texte (chunks). Cette étape nécessite une grande puissance de calcul GPU et peut être réalisée avec la commande `pyalbert make_embeddings`. Cette commande créera les données requises pour les index vectoriels construits avec l'option `pyalbert index --index-type e5`. Vous pouvez consulter la [section de déploiement](/api/README.md#deploy) du fichier Lisez-moi de l'API pour voir toutes les étapes impliquées dans le processus de construction.


## Structure du dépôt / *Folder structure* 

- \_data/ : contient des données volatiles et volumineuses téléchargées par pyalbert.
- api/ : le code de l'API principale.
- api_vllm/ : le code de l'API vllm.
- commons/ : code partagé par différents modules, comme le client API Albert, et l'encodeur d'invite.
- sourcing/ : code derrière `pyalbert download ...` et `pyalbert make_chunks`.
- ir/ : code derrière `pyalbert index ...`
- évaluation/ : code derrière `pyalbert évaluer ...`
- scripts/ : Divers scripts de tests, non (encore) intégrés à pyalbert.
- tests/ : Divers scripts utilitaires, non (encore) intégrés à pyalbert.
- contrib/ : fichiers de configuration pour déployer Albert.
- docs/ : ressources documentaires.
- wiki/ : ressources wiki.


### API

L'API est construite sur plusieurs services :

- L'API LLM (intensive en GPU) : Cette API est gérée par vllm, et l'exécutable se trouve dans api_vllm/.
- Une base de données vectorielle (pour la recherche sémantique), basée sur Qdrant.
- Un moteur de recherche (pour la recherche de texte intégral), basé sur ElasticSearch.
- L'API principale/exposée : l'exécutable de l'application et les configurations se trouvent dans le dossier api/.

Consultez le [Readme](/api/README.md) dédié pour plus d'informations sur la configuration de l'API, les tests et le déploiement.


## Antisèche de commandes Docker pour débugguer

Pour lister les containers actifs de manière claire :
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

Pour afficher les logs d'erreur dún container spécifique :
```bash
docker logs [CONTAINER_NAME]
```

Acceder à la ligne de commande d'un container qui est deja en cours d'éxecution :
```bash
docker exec -e API_URL=[API_URL] -e FRONT_URL=[API_URL] --gpus all --network="host" -it --rm -p 8090:8090 --name miaou-api-v2 registry.gitlab.com/etalab-datalab/llm/albert-backend/api-v2:latest /bin/sh
```

Arrêter et enlever un container qui tourne :
```bash
docker rm -f [CONTAINER_NAME]
```

Démarrer un conteneur en mode interactif pour le débugger, tout en le supprimant automatiquement après avoir quitté :
```bash
docker run -e API_URL=[API_URL] -e FRONT_URL=[API_URL] --rm --gpus all --network="host" -it -p 8090:8090 --name miaou-api-v2 registry.gitlab.com/etalab-datalab/llm/albert-backend/api-v2:latest /bin/sh
```


## Contribuer

TODO


## License

TODO


## Remerciements

TODO
