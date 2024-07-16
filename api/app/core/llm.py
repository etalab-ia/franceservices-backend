from typing import Iterable

from app import crud, schemas
from app.db.session import SessionLocal

from pyalbert.clients import LlmClient
from pyalbert.prompt import get_prompter


def auto_set_chat_name(chat_id: int, stream: schemas.StreamCreate) -> str | Iterable[str] | None:
    with SessionLocal() as db:
        model_name = stream.model_name
        query = " ".join(
            stream.query.split(" ")[:512]
        )  # 512 words should be sufficient to title the query

        # Build prompt
        query = f"Synthétise la demande suivante en un court titre de quelque mots (pas plus de 8 mots) permettant d'identifier la thématique. Le titre doit être court, clair et accrocheur:\n\n{query}"
        prompter = get_prompter(model_name)
        prompt = prompter.make_prompt(query=query)

        # Generate
        llm_client = LlmClient(model_name)
        result = llm_client.generate(prompt, temperature=0.2)
        chat_name = result.choices[0].message.content
        chat_name = chat_name.strip("\"' ")

        # Update db_chat
        db_chat = crud.chat.get_chat(db, chat_id)
        if not db_chat:
            return

        db_chat.chat_name = chat_name
        db.commit()
        return chat_name
