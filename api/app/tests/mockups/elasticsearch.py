from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck():
    return "ok"


@app.post("/{index_name}/_search")
async def search(index_name: str):
    data = []

    data = {
        "took": 30,
        "timed_out": False,
        "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": 1000, "relation": "eq"},
            "max_score": 1.3862944,
            "hits": [
                {
                    "_index": index_name,
                    "_type": "_doc",
                    "_id": "1",
                    "_score": 1.3862944,
                    "_source": {
                        "hash": "d6b6a6314786cb5d",
                        "sid": "F17757",
                        "title": "Promotion interne dans la fonction publique",
                        "url": "https://www.service-public.fr/particuliers/vosdroits/F17757",
                        "introduction": "La promotion interne permet d' accéder à des fonctions ...",
                        "context": "",
                        "theme": "Travail - Formation",
                        "surtitre": "Fiche pratique",
                        "source": "service-public",
                        "related_questions": [
                            {
                                "question": "Catégorie, corps, cadre d'emplois, grade et échelon : quelles différences ?",
                                "sid": "F12344",
                                "url": "https://www.service-public.fr/particuliers/vosdroits/F12344",
                            }
                        ],
                        "web_services": [],
                    },
                    "highlight": {
                        "title": ["Introduction to <em>Python</em>"],
                        "content": ["<em>Python</em> is a versatile programming language..."],
                    },
                },
                {
                    "_index": index_name,
                    "_type": "_doc",
                    "_id": "2",
                    "_score": 0.3862944,
                    "_source": {
                        "hash": "64c7c74f7fa1a47c",
                        "sid": "F3024",
                        "title": "Un intérimaire a-t-il droit à un congé pour un projet de transition professionnelle ?",
                        "url": "https://www.service-public.fr/particuliers/vosdroits/F3024",
                        "introduction": "Si vous êtes travailleur temporaire (souvent appelé intérimaire )...",
                        "text": "Si vous êtes travailleur temporaire (souvent appelé intérimaire ), vous pouvez ...",
                        "context": "",
                        "theme": "Travail - Formation",
                        "surtitre": "Question-réponse",
                        "source": "service-public",
                        "related_questions": [],
                        "web_services": [
                            {
                                "title": "Trouver son opérateur CEP",
                                "institution": "France compétences",
                                "url": "https://mon-cep.org/",
                                "type": "Téléservice",
                            }
                        ],
                    },
                    "highlight": {
                        "title": ["Introduction to <em>Python</em>"],
                        "content": ["<em>Python</em> is a versatile programming language..."],
                    },
                },
            ],
        },
        "aggregations": {
            "categories": {
                "doc_count_error_upper_bound": 0,
                "sum_other_doc_count": 0,
                "buckets": [
                    {"key": "Programming", "doc_count": 2},
                    {"key": "Data Science", "doc_count": 1},
                ],
            }
        },
    }

    response = JSONResponse(data)
    response.headers["X-Elastic-Product"] = "Elasticsearch"
    return response


@app.get("/{index_name}/_doc/{uid}")
async def get(index_name: str, uid: str):
    data = {
        "_index": index_name,
        "_id": uid,
        "_version": 1,
        "_seq_no": 0,
        "_primary_term": 1,
        "found": True,
        "_source": {
            "id": "1",
            "hash": "hash_" + uid,
            "sid": "sid_" + uid,
            "title": "Promotion interne dans la fonction publique",
            "url": "https://www.service-public.fr/particuliers/vosdroits/F17757",
            "introduction": "La promotion interne permet d' accéder à des fonctions ...",
            "context": "",
            "theme": "Travail - Formation",
            "text": "Bonjour, comment allez-vous ?",
        },
    }
    response = JSONResponse(data)
    response.headers["X-Elastic-Product"] = "Elasticsearch"
    return response
