# LLM model available


|                       | base model              | type                    | dataset                                 | finetuning time    |  huggingface link           |
|-----------------------|-------------------------|-------------------------|-----------------------------------------|--------------------|-----------------------------|
|  fabrique-miaou       |  lama-hf-13b            |  completion             | experiences-spp                         |                    |                             |
|  fabrique-reference   |  lama-hf-13b            |  completion + rag       | experiences-spp + sheets-sp             |                    |                             |
|  albert-light         |  lama-chat-hf-13b       |  chat + rag             | french qa + sheet-sp                    |                    |                             |

- model prompt construction : [[commons/prompt_{model_name}]]
- fine-tuning script : [[finetuning/{model_name}]]
- api usage : [[docs/api.md]]
