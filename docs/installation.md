# Installation

## Modèles


Les modèles Alberts sont déployable avec VLLM. Nous mettons à dispositions une API permettant d'embarquer un LLM Albert ainsi qu'une modèle d'embeddings pour le RAG. Pour plus d'informations sur les modèles, rendez-vous sur la page [modeles.md](./modeles.md).

* Build

    ```bash
    docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./llm/Dockerfile ./llm
    ```

* Run

    ```bash
    docker compose --env-file ./llm/.env.example up --detach
    ```

    >  ⚠️ Si vous ne spécifiez pas de modèle d'embeddings le endpoint `/embeddings` retournera une réponse 404 et il sera masqué dans le swagger.

Vous pouvez accéder au swagger de l'API du modèle sur [http://localhost:8000/docs](http://localhost:8000/docs).


* Sans GPU : GPT4all

    Si vous ne disposez pas de GPU, vous trouverez dans un [fichier Dockerfile](../contrib/gpt4all/Dockerfile) pour build l'image de l'API avec GPT4All (à la place de VLLM). Cette API est sur le format de l'API VLLM précédement décrite mais ne nécessite pas utilisation de GPU. Toutefois, celle-ci est maintenu en *best efforts* par les équipes. Voici les modèles actuels disponibles sans GPU :

    - [AgentPublic/albert-tiny](https://huggingface.co/AgentPublic/albert-tiny)
