# Environments

Le projet Albert est déployé sur plusieurs instances suivants les environnements suivants : 

| name | branch | provider | host | 
| --- | --- | --- | --- |
| franceservices | staging | outscale | staging-franceservices |
| franceservices | main | outscale | prod-franceservices |
| dinum | staging | outscale | staging-dinum |
| dinum | main | outscale | prod-dinum 

## CI/CD secret variables

Il est nécessaire pour un déploiement par la pipeline Gitlab de CI/CD (voir [.gitlab-ci.yml](../../.gitlab-ci.yml) de configurer les variables d'environnement suivantes dans les settings de votre repository Gitlab : 

| key | environment | type | protected | info |
| --- | --- | --- | --- | --- |
| STAGING__ENV_FILE | dinum \| franceservices | file | no | Environment variables file for staging environments [(1)](#1-env-files) | 
| PROD__ENV_FILE | dinum \| franceservices | file |  yes | Environment variables file for production environments [(1)](#1-env-files) |
| STAGING__LLM_ROUTING_TABLE | * | file | no | LLM routing table file for staging environments [(2)](#2-config-table-files) |
| PROD__LLM_ROUTING_TABLE | * | file | yes | LLM routing table file for production environments [(2)](#2-config-table-files) |
| CI_DEPLOY_USER | gitlab | * | User name of the deployment service account |
| CI_DEPLOY_USER_SSH_PRIVATE_KEY | * | file | no | Private SSH key of deployment service account (gitlab) |
| CI_API_IMAGE_TAG | * | variable | no | Docker tag of API image (ex: 1.0.0), upgrade it with each build |
| CI_VLLM_IMAGE_TAG | * | variable | no | Docker tag of VLLM image (ex: 1.0.0), upgrade it with each build |
| CI_GPT4ALL_IMAGE_TAG | * | variable | no | Docker tag of GPT4All image (ex: 1.0.0), upgrade it with each build |

#### 1. Env files

Le fichier de variable d'environnement (*STAGING__ENV_FILE* ou *PROD__ENV_FILE*) doit contenir les variables suivantes :

| key | value | environment | info |
| --- | --- | --- | --- |
| CI_DEPLOY_HOST | *** | * | Server DNS or IP where Docker containers are deployed |
| ENV | prod | * |  |
| SECRET_KEY | *** | * |  |
| FIRST_ADMIN_USERNAME | albert | * |  |
| FIRST_ADMIN_EMAIL | albert-contact@data.gouv.fr | * |  |
| FIRST_ADMIN_PASSWORD | *** | * | |
| MJ_API_KEY | *** | * |  |
| MJ_API_SECRET | *** | * |  |
| CONTACT_EMAIL | albert-contact@data.gouv.fr | * |  |
| POSTGRES_PASSWORD | *** | * | Mot de passe de la basede données PostgreSQL. |
| POSTGRES_PORT | *** | * | Port de la base de données PostgreSQL. |
| ELASTIC_PASSWORD | *** | * | Mot de passe de la basede données Elasticsearch. |
| ELASTIC_PORT | *** | * |  Port de la base de données Elasticsearch. |
| QDRANT_REST_PORT | *** | * |  Port REST de la base de données Qdrant. |

#### 2. Fichiers de configuration

Le déploiement utilise des fichiers de configuration qui sont à définir dans [pyalbert/config](../pyalbert/config/).