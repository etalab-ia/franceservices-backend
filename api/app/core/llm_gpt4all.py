from gpt4all import GPT4All
from sqlalchemy.orm import Session

from app import crud
from app.config import ROOT_DIR, WITH_GPU

if WITH_GPU:
    gpt4all_model = None
else:
    gpt4all_model = GPT4All("ggml-model-fabrique-q4_K.bin", model_path=ROOT_DIR)


def gpt4all_callback(db: Session, stream_id):
    def _gpt4all_callback(token_id, token_string):
        # TODO: handle case when no stream
        stream = crud.stream.get_stream(db, stream_id)
        db.refresh(stream)  # important !
        return stream.is_streaming

    return _gpt4all_callback


# TODO: turn into async
def gpt4all_generate(prompt, callback=None, max_tokens=500, temp=20, streaming=True):
    kwargs = {
        "max_tokens": max_tokens,
        "temp": temp / 100,
        "streaming": streaming,
    }
    if callback:
        kwargs["callback"] = callback
    yield from gpt4all_model.generate(prompt, **kwargs)
