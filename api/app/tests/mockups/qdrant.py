from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/healthcheck")
async def healtcheck():
    return "ok"


@app.post("/collections/{collection_name}/points/search")
async def search(collection_name: str):
    # @DEBG: see id encoding for qdrant in ir/qdrant.py
    data = [
        {
            "id": "1".encode("utf8").hex(),
            "version": 0,
            "score": 0,
            "payload": {
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
        },
        {
            "id": "2".encode("utf8").hex(),
            "version": 0,
            "score": 0,
            "payload": {
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
        },
    ]

    data = {"time": 0, "status": "ok", "result": data}

    return JSONResponse(data)
