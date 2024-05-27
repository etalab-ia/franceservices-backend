# Templates de prompt

Afin d'utiliser un modèle LLM avec Albert, il faut ajouter les fichiers suivants dans le [dépôt HuggingFace](https://huggingface.co/AgentPublic) :
- `prompt_config.yml`

Ce fichier expose les templates de prompt qui sont supportés par le modèle, en utilisant le format jinja, et la façon dont ils doivent être formatés.
Vous pouvez trouver un exemple dans le [dépôt `albert-light`](https://huggingface.co/AgentPublic/albertlight-7b) : https://huggingface.co/AgentPublic/albertlight-7b/blob/main/prompt_config.yml

Voici un exemple commenté de ce fichier pour le modèle `AgentPublic/albertlight-7b` :

```prompt_config.yml
# Indique le format général du prompt, en particulier dans le cadre d'un chat ou d'une conversation.
# Indiquez "null" pour aucun formatage.
# D'autres formats seront pris en charge à l'avenir, comme chatml ou mistral.
prompt_format : llama-chat

# La longueur maximale du contexte dans l'ensemble de jetons lors de l'entraînement de l'ajustement fin.
max_tokens : 2048

# La liste des invites supportées pour le modèle. 
# Voici la liste des champs supportés :
* mode (obligatoire) : le nom pour identifier le prompt
# * template (obligatoire) : un fichier template jinja qui doit être présent dans le dépôt HuggingFace, et qui supporte un ensemble de variables documentées dans la section [[Variables de prompt]]
# * system_prompt : une invite système optionnelle, supportée par de nombreux LLM.
# * default : une valeur par défaut pour les variables et méta-variables
invites :
  - mode: simple
    system_prompt: "a particular system prompt..."
    template: simple_prompt_template.jinja

  - mode: rag
    template: rag_prompt_template.jinja
    default:
      limit: 4
```

Et voici les fichiers modèles jinja correspondants :

```simple_prompt_template.jinja
{{query}}
```

```rag_prompt_template.jinja
Utilisez les éléments de contexte à votre disposition ci-dessous pour répondre à la question finale. Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse.

{% for chunk in sheet_chunks %}
{{chunk.url}} : {{chunk.title}} {% if chunk.context %}({{chunk.context}}){% endif %}
{{chunk.text}} {% if not loop.last %}{{"\n"}}{% endif %}
{% endfor %}

Question: {{query}}
```

## Variables de prompt

Albert fournit un ensemble de variables qui peuvent être utilisées dans les templates de prompt, comme le montrent les exemples de fichiers modèles précédents.
Ces variables sont particulièrement utiles pour modéliser les prompts RAG.
Voici la liste des variables supportées :

- `query` : `str` # Le texte de l'utilisateur query/question/input
- `context` : `str` # Une chaîne de contexte supplémentaire...
- `links` : `str` # une chaîne de liens supplémentaire...
- `institution` : `str` # une chaîne institutionnelle supplémentaire...
- `most_similar_experience` : `str` # Expérience la plus similaire à {quête}
- `experience_chunks` : `list[dict]` # une liste d'expériences sémantiquement similaires chunks.
- `sheet_chunks` : `list[dict]` # une liste de morceaux de feuilles sémantiquement similaires.

Chaque chunk **experience** est une structure de type `dict` avec les éléments suivants disponibles :
- `id_experience`,
- `titre`,
- `description`,
- `intitule_typologie_1`,
- `reponse_structure_1`,

Chaque chunk **sheet** est une structure de type `dict` avec les éléments suivants disponibles :
- `hash`,
- `sid`,
- `title`,
- `url`,
- `introduction`,
- `text`,
- `contexte`,
- `theme`,
- `surtitre`,
- `source`,
- `related_questions`,
- `web_services`,
