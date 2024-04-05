# Albert backend

Ce projet contient le code source d'Albert, l'agent conversationnel de l'administration française, développé par les équipes du Datalab de la Direction Interministérielle du Numérique (DINUM). Albert a été créé pour citer ses sources et est spécialisé pour répondre à des questions administratives en français.

Albert est encore en développement et en amélioration continue. Il est conçu pour être utilisé sous la responsabilité d'un agent public.


## Déploiement

Pour déployer le projet Albert, référez-vous à la documentation dédiée : [docs/deploiment](./docs/deploiement/). 


## Pré-requis : exécution de PyAlbert

Utilisez l'outil en ligne de commande `pyalbert` pour créer les ensembles de données et les modèles nécessaires. La documentation peut être consultée en exécutant `./pyalbert.py --help` :

1. téléchargement du corpus de données en français -- `pyalbert download_rag_sources --help`.
2. prétraitement et mise en forme du corpus de données -- `pyalbert make_chunks --help`.
3. alimenter les moteurs de recherche d'indexation <index/vector> -- `pyalbert index --help`
4. évaluation des modèles -- `pyalbert evaluate --help`.


## Structure du dépôt

- pyalbert/ : Bibliothèque Albert et CLI: Boîte à outils Albert : récupérer et analyser des données, construire des blocs, alimenter le moteur de recherche, créer et traiter des invites, clients API..
- api/ : le code de l'API d'Albert.
- llm/ : le code de l'API des LLM et modèle d'embeddings.
- databases/ : Code de déploiement de la base de données et des moteurs de recherche.
- contrib/ : fichiers de configuration pour déployer Albert.
- docs/ : ressources documentaires.


## Contribuer

TODO


## License

TODO


## Remerciements

TODO
