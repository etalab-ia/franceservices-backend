# Prompt template

In order to use a model LLM model with Albert, one must add the following files inside the [HuggingFace repository](https://huggingface.co/AgentPublic) :
- `prompt_config.yml`

This file expose the prompt template that are supported by the model, using jinja format, and how they should be formatted.
You can find an example in the [`albert-light` repository](https://huggingface.co/AgentPublic/albertlight-7b): https://huggingface.co/AgentPublic/albertlight-7b/blob/main/prompt_config.yml

Here is an commented example of this file for the `AgentPublic/albertlight-7b` model:

```prompt_config.yml
# This indicate how the general prompt format, especially in a chat/conversation setting.
# Indicate "null" for no formatting.
# More format will be supported in the future, such that chatml, or mistral.
prompt_format: llama-chat

# the max context lenght in token set during the training of the fine-tuning.
max_tokens: 2048

# The list of supported prompt for the model. 
# Here is the list the supported field:
# * mode (required): A name to identify a prompt
# * template (required): a jinja template file that should be present in the HuggingFace repository and that support a set of variables documented in the section [[Prompt Variables]]
# * system_prompt: An optionnal system prompt, supported by many LLM.
# * default: a set a default value for variables and meta-variables
prompts:
  - mode: simple
    system_prompt: "a particular system prompt..."
    template: simple_prompt_template.jinja

  - mode: rag
    template: rag_prompt_template.jinja
    default:
      limit: 4
```

And here are the corresponding jinja template files:

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

## Prompt Variables

Albert provides a set of variables that can be used in the prompt templates, as show in the previous template files examples.
It is in particular useful to model RAG prompts.
Here the list of the supported variables :

- `query`: `str` # The user text query/question/input
- `context`: `str` # A extra context string...
- `links`: `str`  # a extra links string...
- `institution`: `str` # an extra institution string...
- `most_similar_experience`: `str` # Most similar experience to {query}
- `experience_chunks`: `list[dict]` # a list of semantically similar experiences chunks.
- `sheet_chunks`: `list[dict]` # a list of semantically similar sheets chunks.

Each individual **experience** chunk is a dict like structure with the following items available:
- `id_experience`,
- `titre`,
- `description`,
- `intitule_typologie_1`,
- `reponse_structure_1`,

Each individual **sheet** chunk is a dict like structure with following items available:
- `hash`,
- `sid`,
- `title`,
- `url`,
- `introduction`,
- `text`,
- `context`,
- `theme`,
- `surtitre`,
- `source`,
- `related_questions`,
- `web_services`,
