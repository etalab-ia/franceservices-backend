import json

from app import crud, models, schemas
from app.clients.api_vllm_client import ApiVllmClient
from app.config import WITH_GPU
from app.deps import get_current_user, get_db

from app.core.llm import auto_set_chat_name
if not WITH_GPU:
    from app.core.llm_gpt4all import gpt4all_callback, gpt4all_generate

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from commons import get_prompter

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/streams", response_model=list[schemas.Stream])
def read_streams(
    skip: int = 0,
    limit: int = 100,
    chat_id: int | None = None,
    desc: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    streams = crud.stream.get_streams(
        db, user_id=current_user.id, skip=skip, limit=limit, chat_id=chat_id, desc=desc
    )
    return [stream.to_dict() for stream in streams]


@router.post("/stream", response_model=schemas.Stream)
def create_user_stream(
    stream: schemas.StreamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.stream.create_stream(db, stream, user_id=current_user.id).to_dict()


@router.post("/stream/chat/{chat_id}")
def create_chat_stream(
    chat_id: int,
    stream: schemas.StreamCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_chat = crud.chat.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(404, detail="Chat not found")

    if db_chat.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    if not db_chat.streams:
        background_tasks.add_task(auto_set_chat_name, chat_id, stream)

    db_stream = crud.stream.create_stream(db, stream, user_id=current_user.id, chat_id=chat_id)
    return db_stream.to_dict()


@router.get("/stream/{stream_id}", response_model=schemas.Stream)
def read_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if current_user.id not in (db_stream.user_id, getattr(db_stream.chat, "user_id", None)):
        raise HTTPException(403, detail="Forbidden")

    return db_stream.to_dict()


# TODO: turn into async ?
@router.get("/stream/{stream_id}/start", response_class=StreamingResponse)
def start_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if current_user.id not in (db_stream.user_id, getattr(db_stream.chat, "user_id", None)):
        raise HTTPException(403, detail="Forbidden")

    stream_id = db_stream.id
    model_name = db_stream.model_name
    mode = db_stream.mode
    query = db_stream.query
    # @DEBUG: This should be passed once, when the stream start, and not saved (pass parameters to the first call to start_stream)
    limit = db_stream.limit
    user_text = db_stream.user_text
    context = db_stream.context
    institution = db_stream.institution
    links = db_stream.links
    temperature = db_stream.temperature
    should_sids = db_stream.should_sids
    must_not_sids = db_stream.must_not_sids
    sources = None
    if db_stream.sources:
        sources = [source.source_name for source in db_stream.sources]

    # TODO: turn into async
    # Streaming case
    def generate():
        # Build prompt (warning, it's extra sensitive + avoid carriage return):
        prompter = get_prompter(model_name, mode)
        # We pass a mix of all kw arguments used by all prompters...
        # This is allowed because each prompter accepts **kwargs arguments...
        prompt = prompter.make_prompt(
            experience=user_text,
            institution=institution,
            context=context,
            links=links,
            query=query,
            limit=limit,
            sources=sources,
            should_sids=should_sids,
            must_not_sids=must_not_sids,
        )

        if (
            "max_tokens" in prompter.sampling_params
            and len(prompt.split()) * 1.25 > prompter.sampling_params["max_tokens"] * 0.8
        ):
            raise HTTPException(413, detail="Prompt too large")

        # Keep reference of rag used sources if any
        rag_sources = []
        if prompter.sources:
            rag_sources = prompter.sources

        # Allow client to tune the sampling parameters.
        sampling_params = prompter.sampling_params
        for k in ["max_tokens", "temperature", "top_p"]:
            v = getattr(db_stream, k, None)
            if v:
                sampling_params.update({k: v})

        # Get the right stream generator
        if WITH_GPU:
            api_vllm_client = ApiVllmClient(url=prompter.url)
            generator = api_vllm_client.generate(prompt, **sampling_params)
        else:
            callback = gpt4all_callback(db, stream_id)
            generator = gpt4all_generate(prompt, callback=callback, temp=temperature)

        # Stream !
        crud.stream.set_is_streaming(db, db_stream, True)
        try:
            acc = []
            raw_response = ""
            for t in generator:
                acc.append(t)
                raw_response += t
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
            crud.stream.set_is_streaming(db, _db_stream, False, commit=False)
            crud.stream.set_rag_output(db, _db_stream, raw_response, rag_sources)

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

    if current_user.id not in (db_stream.user_id, getattr(db_stream.chat, "user_id", None)):
        raise HTTPException(403, detail="Forbidden")

    crud.stream.set_is_streaming(db, db_stream, False)
    return db_stream.to_dict()
