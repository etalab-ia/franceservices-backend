# Pyalbert

PyAlbert une un module Python pour faciliter l'utilisation des modèles Albert.
Il permet de :

### Télécharger les sources de données du RAG
```bash
pyalbert make_chunks --structured
```

### Créer le fichier de liste blanche `.json` contenant les numéros de téléphone, les adresses mail et les URL de domaine extraits des annuaires locaux et nationaux :
```bash
pyalbert create_whitelist
```

### Créer les chunks de documents pour le RAG
```bash
pyalbert make_chunks --structured
```

### Créer les index de la base de données ElasticSearch qui contient les sources de données pour le RAG :
```bash
pyalbert index experiences --index-type bm25
pyalbert index sheets      --index-type bm25
pyalbert index chunks      --index-type bm25
```

### Créer les index de la base de données Qdrant qui contient les vecteurs d'embeddings :
```bash
pyalbert index experiences --index-type e5
pyalbert index chunks      --index-type e5
```

### Lancer l'API Albert en local (dev mode)
```bash
pyalbert serve
```
