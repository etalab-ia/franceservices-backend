# Environments

| name | branch | provider | host | 
| --- | --- | --- | --- |
| franceservices | staging | outscale | staging-franceservices |
| franceservices | main | outscale | prod-franceservices |
| dinum | staging | outscale | staging-dinum |
| dinum | main | outscale | prod-dinum 

## CI/CD secret variables

| key | environment | type | protected | info |
| --- | --- | --- | --- | --- |
| STAGING__ENV_FILE | dinum | file | no | Environment variables file for staging branch of dinum environment [(1)](#1-env-files) | 
| STAGING__ENV_FILE | franceservices | file | no | Environment variables file for staging branch of france service environment [(1)](#1-env-files) |
| PROD__ENV_FILE | dinum | file |  yes | Environment variables file for main branch (protected) of dinum environment [(1)](#1-env-files) |
| PROD__ENV_FILE | franceservices | file |  yes | Environment variables file for main branch (protected) of dinum environment [(1)](#1-env-files) |
| ID_RSA | * | file | no | Private SSH key of deployment service account (gitlab) |
| VLLM_ROUTING_TABLE | * | file | no | VLLM routing table file for dinum environment [(2)](#2-config-table-files) |
| CORPUS_RESSOURCES_TABLE | * | file | no | Corpus ressources table file for dinum environment [(2)](#2-config-table-files) |
| WHITELIST_RESSOURCES_TABLE | * | file | no | Whitelist ressources table file for franceservices [(2)](#2-config-table-files) |
| CI_API_IMAGE_TAG | * | variable | no | Docker tag of API image (ex: 1.0.0), upgrade it with each build |
| CI_VLLM_IMAGE_TAG | * | variable | no | Docker tag of VLLM image (ex: 1.0.0), upgrade it with each build |

#### 1. Env files

Environment variables file must contain the following variables:

| key | value | environment | info |
| --- | --- | --- | --- |
| SERVER_USER | gitlab | * | User name of the deployment service account |
| SERVER_IP | *** | * | Server DNS or IP where Docker containers are deployed |
| VLLM_IMAGE_TAG | *** | * | VLLM image tag, upgrade it with each build |
| API_IMAGE_TAG | *** | * | api image tag, upgrade it with each build |
| OSC_REGION | eu-west \| cloudgouv-eu-west-1 | staging | Outscale VM region, only for link GPU during staging CI/CD pipeline |
| OSC_SUBREGION | eu-west-2a \| cloudgouv-eu-west-1a | staging | Outscale VM subregion, only for link GPU during staging CI/CD pipeline |
| OSC_ACCESS_KEY | *** | staging | Outscale access key, only for link GPU during staging CI/CD pipeline |
| OSC_SECRET_KEY | *** | staging | Outscale secret key, only for link GPU during staging CI/CD pipeline  |
| OSC_VM_ID | *** | staging | Outscale VM ID, only for link GPU during staging CI/CD pipeline |
| OSC_GPU_MODEL_NAME | nvidia-p6 \| nvidia-v100 \| nvidia-p100 \| nvidia-a100 \| nvidia-a100-80 | staging | Outscale GPU model name, only for link GPU during staging CI/CD pipeline. Refer to the [Outscale documentation](https://docs.outscale.com/fr/userguide/%C3%80-propos-des-flexible-GPU.html) |
| OSC_CPU_GENERATION | v5 \| v6 | staging | Outscale CPU generation, only for link GPU during staging CI/CD pipeline. Refer to the [Outscale documentation](https://docs.outscale.com/fr/userguide/%C3%80-propos-des-flexible-GPU.html) |
| ENV | prod | * |  |
| SECRET_KEY | *** | * |  |
| FIRST_ADMIN_USERNAME | language_model | * |  |
| FIRST_ADMIN_EMAIL | language_model@data.gouv.fr | * |  |
| FIRST_ADMIN_PASSWORD | *** | * | |
| MJ_API_KEY | *** | * |  |
| MJ_API_SECRET | *** | * |  |
| POSTGRES_PASSWORD | *** | * |  |
| CONTACT_EMAIL | albert-contact@data.gouv.fr | * |  |

#### 2. Config table files

Examples ot table files (vllm routing, corpus and whitelist) are in [pyalbert/examples](../pyalbert/examples/) directory.