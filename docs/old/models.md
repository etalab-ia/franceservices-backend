# LLM model available


|                       | base model              | type                    | dataset                                 | finetuning time    |  huggingface link           |
|-----------------------|-------------------------|-------------------------|-----------------------------------------|--------------------|-----------------------------|
|  fabrique-miaou       |  lama-hf-13b            |  completion             | experiences-spp                         |                    |                             |
|  fabrique-reference   |  lama-hf-13b            |  completion + rag       | experiences-spp + sheets-sp             |                    |                             |
|  albert-light         |  lama-chat-hf-13b       |  chat + rag             | french qa + sheet-sp                    |                    |                             |

- fine-tuning script : [[finetuning/{model_name}]]
- See the prompt_config.yml file that expose the prompts templates provided for each model.
