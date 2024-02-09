from gpt4all import GPT4All
from sqlalchemy.orm import Session

from app import crud
from app.config import ENV, ROOT_DIR, TINY_ALBERT_LOCAL_PATH, WITH_GPU


if WITH_GPU and ENV != "dev":
    gpt4all_model = None
else:
    if TINY_ALBERT_LOCAL_PATH:
        gpt4all_model = GPT4All(str(TINY_ALBERT_LOCAL_PATH), model_path=ROOT_DIR)
    else:
        raise Exception("Tiny Albert model not found locally, please check config.py")


def gpt4all_callback(db: Session, stream_id):
    def _gpt4all_callback(token_id, token_string):
        # TODO: handle case when no stream
        stream = crud.stream.get_stream(db, stream_id)
        db.refresh(stream)  # important !
        return stream.is_streaming

    return _gpt4all_callback


# TODO: turn into async
def gpt4all_generate(prompt, callback=None, max_tokens=512, temp=20, streaming=True):
    kwargs = {
        "max_tokens": max_tokens,
        "temp": temp / 100,
        "streaming": streaming,
    }
    if callback:
        kwargs["callback"] = callback

    if streaming:
        yield from gpt4all_model.generate(prompt, **kwargs)
    else:
        return gpt4all_model.generate(prompt, **kwargs)
