# ETALAB_CHATBOT

## Installation

Pour installer le projet, il suffit d'installer les dépendances avec la commande suivante :

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Il faut ensuite copier le fichier .env.template en .env et remplir les variables d'environnement. Finalement, il faut ajouter les fichiers xml présents aux urls suivantes dans le dossier \_data/xml_files :

- [Service Public FR - Guide vos droits et démarches particuliers](https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-particuliers/)
- [Service Public FR - Guide vos droits et démarches entreprendre](https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-entreprendre/)
- [Service Public FR - Guide vos droits et démarches associations](https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-associations/)

## Utilisation

Le projet marche avec un argument parser défini dans le fichier commands.py. Pour visualiser les commandes disponibles, il suffit de lancer la commande suivante :

```bash
python main.py --help
```

## Struture

Le projet est structuré de la manière suivante :

- `main.py` : fichier principal qui lance les commandes
- `commands.py` : fichier qui définit les commandes disponibles
- `_data` : dossier qui contient les données

  - `xml_files` : dossier qui contient les fichiers xml
  - `json_database` : dossier qui contient les chunks de fiches sous format json

Chaque fonctionnalité du projet est organisé dans un dossier qui contient les fichiers suivants :

- `params.py` : fichier qui contient les paramètres de la fonctionnalité
- `_main.py` : fichier principal qui contient la logique pour exécuter la fonctionnalité

Les fonctionnalités sont les suivantes :

- `xml_parsing` : contient la logique pour parser les fichiers xml et les transformer en fiches sous format JSON. Chaque élement JSON correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.
- `corpus_generation` : contient la logique pour générer des questions à partir des fiches sous format JSON et à répondre à ces questions via openai ou autres llm.
- `fine_tuning` : permet d'entraîner un modèle XGEN de Salesforce via le Trainer d'HuggingFace. Le modèle est entraîné sur un corpus de questions / réponses générées par openai à partir des JSON.
- `xml_parsing`: contient la logique pour parser les fichiers xml et les transformer en fiches sous format JSON. Chaque élement JSON correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.

## Corpus Generation

### Génération des questions

La fonction qui génère les questions est generate_questions, dans le \_main.py du dossier corpus_generation.

Les prompts sont dans le fichier corpus_generation/gpt_generators/questions_generators.py voici le fonctionnement en détail

#### Class GPTQuestionGnerator

Les questions sont générées à partir des xml parsés en chunk. Pour générer les questions, on récupère une certaine quantité de chunks liés à une seule et même fiche. Une liste des mots clés est ensuite générée dans la fonction get_keywords.
Ces keywords sont ensuite intégrée dans la fonction get_questions afin de récupérer n questions sur ces mots-clés. Il est spécifié de numéroter les questions parce qu'openai décide de le faire une fois sur deux sinon et ne respecte pas la consigne "Ne numérote pas les questions"

##### Class GPTQuestionReformulation

La reformulation de questions se fait à partir d'une seule question en entrée.
Celle-ci se verra alors transformée deux fois à la première personne et deux fois en langage familier.
Les autres niveaux de langue ne sont pas utiles, openai s'exprimant déjà en langage courant et le langage soutenu ne changeant pas assez la question.

##### Fonctionnement de generate_questions

Après avoir ouvert le fichier contenant les xml parsés et crée le fichier qui va contenir les questions (tous deux modifiables dans params.py), il ne reste plus qu'à générer puis reformuler les questions avant de les insérer dans le csv de sortie.
Pour choisir le nombre de questions à générer à partir d'un set de mots-clés, il faut modifier le paramètres

### Génération des réponses

Les questions doivent être stockées sous format csv, emplacement défini dans [corpus_generation.params.py](./corpus_generation/params.py). Un llm doit être choisi pour répondre à ces questions (actuellement possible : GPT-3.5-turbo ou XGEN) Pour générer les réponses, il faut lancer la commande suivante :

```bash
python main.py --xgen
python main.py --gpt
```

Les réponses sont ajoutées au fur et à mesure dans le csv de sortie

## fine-tuning

Il est possible de lancer un fine_tuning sur un modèle XGEN de Salesforce. Pour cela, il faut lancer la commande suivante :

```bash
python main.py --fine_tune_model
```

Les paramètres du fine-tuning sont définis dans le fichier [fine_tuning.params.py](./fine_tuning/params.py). Un exemple de la forme du dataset est disponible dans le fichier [fine_tuning/data/training/dataset-test.csv](./fine_tuning/data/training/dataset-test.csv)

## Retrieving

Afin de répondre aux questions, un algorithme de retrieving appelé BM25 est indiqué dans [commands.py](./commands.py) dans la varialbe `context_retriever`. Il est possible de changer cet algorithme en utilisant une base de données vectorisée appelée Weaviate. Pour cela, il faut lancer la commande suivante :

```bash
python main.py --run_weaviate_migration
```

Et ensuite, changer la variable `context_retriever` dans [commands.py](./commands.py) par la classe `WeaviateRetriver` défini dans [retrieving/vector_db/retriever.py](./retrieving/vector_db/retriever.py)
