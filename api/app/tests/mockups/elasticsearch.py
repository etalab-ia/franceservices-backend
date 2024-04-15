from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck():
    return "ok"


@app.get("/search")
async def search():
    return "todo"


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
