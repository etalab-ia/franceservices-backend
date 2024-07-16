# Albert RAG API

## Overview
The Albert API supports the v1 OpenAI API, including system prompts, conversation handling, temperature control, and streaming. Additionally, we have introduced a Retrieval-Augmented Generation (RAG) extension toenhance user queries with relevant sources.

## Authentication
To use the API, you need to authenticate with an API token. Ensure that you include the token in the header of your requests.

## Endpoints

### 1. Standard LLM API

**Endpoint**
```
POST /api/v1/chat/completions
```

- See https://platform.openai.com/docs/api-reference/chat/create for the full list supported parameters. 
- See https://huggingface.co/AgentPublic to see the available models.


#### Example Request
```bash
curl -X POST https://albert.etalab.gouv.fr/api/v1/chat/completions \
-H "Authorization: Bearer YOUR_API_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "model" : "AgentPulic/llama3-instruct-8b",
  "messages": [
    { "role": "system", "content": "Réponds dans un style francais ancien, moyenâgeux." },
    { "role": "user", "content": "Comment déclarer un revenue fiscal de référence ?" },
  ],
  "temperature": 0.7,
}'
```

### 2. RAG Extension
#### Endpoint
```
POST /api/v1/chat/completions
```

#### Parameters
- `rag`: (string, optional) Only "last" is supported for now, which the current RAG implementation of ALbert that augment the last user query with French data references
- `limit`: (integer, optional) Limit the number of references added.
- `sources`: (array, optional) List of sources to search for references. Source available: "service-public", "travail-emploi".

#### Example Request
```bash
curl -X POST https://albert.etalab.gouv.fr/api/v1/chat/completions \
-H "Authorization: Bearer YOUR_API_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "model" : "AgentPulic/llama3-instruct-8b",
  "messages": [
    { "role": "system", "content": "Réponds dans un style ancien, moyenâgeux" },
    { "role": "user", "content": "Comment déclarer un revenue fiscal de référence ?" },
  "rag": {
      "mode": "rag",
      "strategy": "last",
      "limit": 5
  }
}'
```

## Note
- The API does not store user conversations.
- User must authenticated to use the API.


