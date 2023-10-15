import json

from app import crud, models, schemas
from app.clients.api_vllm_client import ApiVllmClient
from app.config import WITH_GPU
from app.core.llm_gpt4all import gpt4all_callback, gpt4all_generate
from app.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from commons import get_prompter

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/streams", response_model=list[schemas.Stream])
def read_streams(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    streams = crud.stream.get_streams(db, current_user.id, skip=skip, limit=limit)
    return streams


@router.post("/stream", response_model=schemas.Stream)
def create_stream(
    stream: schemas.StreamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.stream.create_stream(db, stream, current_user.id)


@router.get("/stream/{stream_id}", response_model=schemas.Stream)
def read_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if db_stream.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    return db_stream


# TODO: turn into async
@router.get("/stream/{stream_id}/start", response_class=StreamingResponse)
def start_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if db_stream.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    stream_id = db_stream.id
    model_name = db_stream.model_name
    mode = db_stream.mode
    query = db_stream.query
    # @DEBUG: This should be passed once a request time, and not saved (pass parameters to the first call to start_stream)
    limit = db_stream.limit
    user_text = db_stream.user_text
    context = db_stream.context
    institution = db_stream.institution
    links = db_stream.links
    temperature = db_stream.temperature

    # TODO: turn into async
    # Streaming case
    def generate():
        # Buid prompt (warning, it's extra sensitive + avoid carriage return):
        prompter = get_prompter(model_name, mode)
        # We pass a mix of all kw arguments used by all prompters...
        # This is allows because each prompter accept a **kwargs arguments...
        prompt = prompter.make_prompt(
            experience=user_text,
            institution=institution,
            context=context,
            links=links,
            query=query,
            limit=limit,
        )
        sampling_params = prompt.sampling_params
        for k in ["max_tokens", "temperature", "top_p"]:
            v = getattr(db_stream, k)
            if v:
                v = v * 100 if k == "temperature" else v
                sampling_params.update({k: v})

        # Get the right stream generator
        if WITH_GPU:
            api_vllm_client = ApiVllmClient()
            generator = api_vllm_client.generate(prompt, **sampling_params)
        else:
            callback = gpt4all_callback(db, stream_id)
            generator = gpt4all_generate(prompt, callback=callback, temp=temperature)

        # Stream !
        crud.stream.set_is_streaming(db, db_stream, True)
        try:
            acc = []
            for t in generator:
                acc.append(t)
                if t.endswith((" ", "\n")) or t.startswith((" ", "\n")):
                    yield "data: " + json.dumps("".join(acc)) + "\n\n"
                    acc = []

            if len(acc) > 0:
                yield "data: " + json.dumps("".join(acc)) + "\n\n"

            eos_code = json.dumps("[DONE]")
            yield f"data: {eos_code}\n\n"
        finally:
            # Get and refresh stream to prevent the following error:
            # sqlalchemy.orm.exc.ObjectDereferencedError: Can't emit change event
            # for attribute 'Stream.is_streaming' - parent object of type <Stream>
            # has been garbage collected.
            _db_stream = crud.stream.get_stream(db, stream_id)
            db.refresh(_db_stream)
            crud.stream.set_is_streaming(db, _db_stream, False)

    return StreamingResponse(generate(), media_type="text/event-stream")


# TODO: stop has no effect for vllm (no callback), add warning in that case or handle it
@router.post("/stream/{stream_id}/stop", response_model=schemas.Stream)
def stop_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if db_stream.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    crud.stream.set_is_streaming(db, db_stream, False)
    return db_stream
