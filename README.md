## ETALAB_CHATBOT

# Installation

Pour installer le projet, il suffit d'installer les dépendances avec la commande suivante :

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Il faut ensuite copier le fichier .env.template en .env et remplir les variables d'environnement.

# TODO : explain how to add the data xml and q_a

# Utilisation

Le projet marche avec un argument parser défini dans le fichier commands.py. Pour visualiser les commandes disponibles, il suffit de lancer la commande suivante :

```bash
python main.py --help
```

# Struture

Le projet est structuré de la manière suivante :

- main.py : fichier principal qui lance les commandes
- commands.py : fichier qui définit les commandes disponibles
- \_data : dossier qui contient les données

  - xml_files : dossier qui contient les fichiers xml
  - json_database : dossier qui contient les chunks de fiches sous format json

Chaque fonctionnalité du projet est organisé dans un dossier qui contient les fichiers suivants :

- params.py : fichier qui contient les paramètres de la fonctionnalité
- \_main.py : fichier principal qui contient la logique pour exécuter la fonctionnalité

Les fonctionnalités sont les suivantes :

- xml_parsing : contient la logique pour parser les fichiers xml et les transformer en fiches sous format JSON. Chaque élement JSON correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.
- corpus_generation : contient la logique pour générer des questions à partir des fiches sous format JSOn et à répondre à ces questions.
- fine_tuning : permet d'entraîner un modèle XGEN de Salesforce via le Trainer d'HuggingFace. Le modèle est entraîné sur un corpus de questions / réponses générées par openai à partir des JSON.

## Génération de dataset

### Génération des questions

La fonction qui génère les questions est generate_questions, dans le \_main.py du dossier corpus_generation.

Les prompts sont dans le fichier corpus_generation/gpt_generators/questions_generators.py voici le fonctionnement en détail

##### Class GPTQuestionGnerator

Les questions sont générées à partir des xml parsés en chunk. Pour générer les questions, on récupère une certaine quantité de chunks liés à une seule et même fiche. Une liste des mots clés est ensuite générée dans la fonction get_keywords.
Ces keywords sont ensuite intégrée dans la fonction get_questions afin de récupérer n questions sur ces mots-clés. Il est spécifié de numéroter les questions parce qu'openai décide de le faire une fois sur deux sinon et ne respecte pas la consigne "Ne numérote pas les questions"

##### Class GPTQuestionReformulation

La reformulation de questions se fait à partir d'une seule question en entrée.
Celle-ci se verra alors transformée deux fois à la première personne et deux fois en langage familier.
Les autres niveaux de langue ne sont pas utiles, openai s'exprimant déjà en langage courant et le langage soutenu ne changeant pas assez la question.

##### Fonctionnement de generate_questions

Après avoir ouvert le fichier contenant les xml parsés et crée le fichier qui va contenir les questions (tous deux modifiables dans params.py), il ne reste plus qu'à générer puis reformuler les questions avant de les insérer dans le csv de sortie.
Pour choisir le nombre de questions à générer à partir d'un set de mots-clés, il faut modifier le paramètres

## fine-tuning

## inference

<< indiquer ou changer les confs. Donner les paths pour modifier. Ne pas arcoder, séparer du code.>>
