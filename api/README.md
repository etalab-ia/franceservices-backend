# API

**La documentation de l'API est dans le dossier [docs/api](../docs/api) dédié pour plus d'informations sur la configuration de l'API, les tests et le déploiement.**

L'API est construite sur plusieurs services :

- L'API LLM (intensive en GPU) : Cette API est gérée par vllm, et l'exécutable se trouve dans api_vllm/.
- Une base de données vectorielle (pour la recherche sémantique), basée sur Qdrant.
- Un moteur de recherche (pour la recherche de texte intégral), basé sur ElasticSearch.
- L'API principale/exposée : l'exécutable de l'application et les configurations se trouvent dans le dossier api/.

