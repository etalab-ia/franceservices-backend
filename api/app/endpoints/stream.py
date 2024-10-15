import json
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from spacy.lang.fr import French
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import auto_set_chat_name
from app.deps import get_current_user, get_db

from pyalbert import get_logger
from pyalbert.clients import LlmClient
from pyalbert.config import ACTIVATE_SSE_WRAPPER
from pyalbert.prompt import (
    SamplingParams,
    check_url,
    correct_mail,
    correct_number,
    correct_url,
    get_prompter,
)
from pyalbert.utils import sse_decode_chunk

router = APIRouter()
logger = get_logger()


def de_sse_wrapper(generator):
    """Wrap the generatoror to return the full raw reponse once the iterator ends."""
    raw_response = ""
    for chunk in generator:
        try:
            raw_response += sse_decode_chunk(chunk)
        except Exception as err:
            logger.error(f"Failed to decode chunk ({err}): {chunk}")

        yield chunk

    return raw_response


def sse_wrapper(generator):
    """Fromat a raw stream to be SSE compatible (format used by openai stream).
    Wrap the generatoror to return the full raw reponse once the iterator ends.
    """
    acc = []
    raw_response = ""
    stream_activate = False
    for t in generator:
        # Strip stream
        if not stream_activate and t.isspace():
            continue
        else:
            stream_activate = True

        # Accumulate word
        raw_response += t
        acc.append(t)
        if t.endswith((" ", "\n")) or t.startswith((" ", "\n")):
            yield "data: " + json.dumps("".join(acc)) + "\n\n"
            acc = []

    if len(acc) > 0:
        yield "data: " + json.dumps("".join(acc)) + "\n\n"

    eos_code = json.dumps("[DONE]")
    yield f"data: {eos_code}\n\n"
    return raw_response


def postprocess_sse_wrapper(generator, postprocessing):
    # @DEBUG: the return value of the generator is lost. See yield from...
    nlp = French()
    nlp.add_pipe("sentencizer")
    bucket = []
    bucket_out = ""
    eos_code = "[DONE]"
    url_dict, mail_dict, number_dict = [], [], []
    whitelist_path = os.environ.get("API_WHITELIST_FILE", "/data/whitelist/whitelist.json")

    for words in generator:
        try:
            _, _, data = words.decode("utf-8").partition("data: ")
            text = json.loads(data)
            bucket.append(text)

        except AttributeError:
            _, _, data = words.encode("utf-8").decode("utf-8").partition("data: ")
            text = json.loads(data)
            bucket.append(text)

        doc = nlp("".join(bucket))

        if len(list(doc.sents)) == 2:
            bucket_out = str(list(doc.sents)[0])

            if "check_mail" in postprocessing:
                mail_dict.extend(correct_mail(text=bucket_out, whitelist_path=whitelist_path)[1])
                bucket_out = correct_mail(text=bucket_out, whitelist_path=whitelist_path)[0]

            if "check_number" in postprocessing:
                number_dict.extend(
                    correct_number(text=bucket_out, whitelist_path=whitelist_path)[1]
                )
                bucket_out = correct_number(text=bucket_out, whitelist_path=whitelist_path)[0]

            if "check_url" in postprocessing:
                url_dict.extend(correct_url(text=bucket_out, whitelist_path=whitelist_path)[1])
                bucket_out = correct_url(text=bucket_out, whitelist_path=whitelist_path)[0]

            if bucket_out[-1] == "." or bucket_out[-1] == "?":
                bucket_out += " "  # Adding a space after "." or "?" at the end of each sentence

            yield f"number_dict: {number_dict} mail_dict: {mail_dict} url_dict: {url_dict} data: {json.dumps(bucket_out)}\n\n"
            bucket_out = ""
            bucket = [str(list(doc.sents)[1])]

        elif (
            len(list(doc.sents)) == 1 and eos_code in bucket
        ):  # For the last sentence of the generated text
            bucket_out = str(list(doc.sents)[0])
            bucket_out = bucket_out.replace(eos_code, "")

            if "check_mail" in postprocessing:
                mail_dict.extend(correct_mail(text=bucket_out, whitelist_path=whitelist_path)[1])
                bucket_out = correct_mail(text=bucket_out, whitelist_path=whitelist_path)[0]

            if "check_number" in postprocessing:
                number_dict.extend(
                    correct_number(text=bucket_out, whitelist_path=whitelist_path)[1]
                )
                bucket_out = correct_number(text=bucket_out, whitelist_path=whitelist_path)[0]

            if "check_url" in postprocessing:
                url_dict.extend(correct_url(text=bucket_out, whitelist_path=whitelist_path)[1])
                bucket_out = correct_url(text=bucket_out, whitelist_path=whitelist_path)[0]

            yield f"number_dict: {number_dict} mail_dict: {mail_dict} url_dict: {url_dict} data: {json.dumps(bucket_out)}\n\n"
            # yield of the last sentence

            bucket_out = eos_code
            if (
                "check_url" in postprocessing
            ):  # Checking all url's status code and fullfilling url_dict with full urls having a status code = 200
                for dict in url_dict:
                    if dict["old_url"] == check_url(
                        url=dict["old_url"],
                        whitelist_path=whitelist_path,
                        check_status_code=True,
                    ):
                        dict["new_url_full"] = check_url(
                            url=dict["old_url"],
                            whitelist_path=whitelist_path,
                            check_status_code=True,
                        )
                    else:
                        dict["new_url_full"] = ""

            yield f"number_dict: {number_dict} mail_dict: {mail_dict} url_dict: {url_dict} data: {json.dumps(bucket_out)}\n\n"
            # yielding the end_of_stream token and full dictionnaries


@router.get("/streams", response_model=list[schemas.Stream], tags=["stream"])
def read_streams(
    skip: int = 0,
    limit: int = 100,
    chat_id: int | None = None,
    desc: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[schemas.Stream]:
    streams = crud.stream.get_streams(
        db, user_id=current_user.id, skip=skip, limit=limit, chat_id=chat_id, desc=desc
    )
    return [stream.to_dict() for stream in streams]


@router.post("/stream", response_model=schemas.Stream, tags=["public", "stream"])
def create_user_stream(
    stream: schemas.StreamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.Stream:
    return crud.stream.create_stream(db, stream, user_id=current_user.id).to_dict()


@router.post("/stream/chat/{chat_id}", tags=["stream"])
def create_chat_stream(
    chat_id: int,
    stream: schemas.StreamCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.Stream:
    db_chat = crud.chat.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(404, detail="Chat not found")

    if db_chat.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    if not db_chat.streams:
        background_tasks.add_task(auto_set_chat_name, chat_id, stream)

    db_stream = crud.stream.create_stream(db, stream, user_id=current_user.id, chat_id=chat_id)
    return db_stream.to_dict()


@router.get("/stream/{stream_id}", response_model=schemas.Stream, tags=["stream"])
def read_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.Stream:
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if not (
        current_user.is_admin
        or current_user.id in (db_stream.user_id, getattr(db_stream.chat, "user_id", None))
    ):
        raise HTTPException(403, detail="Forbidden")

    return db_stream.to_dict()


# TODO: turn into async ?
@router.get(
    "/stream/{stream_id}/start", response_class=StreamingResponse, tags=["public", "stream"]
)
def start_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> StreamingResponse:
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if current_user.id not in (db_stream.user_id, getattr(db_stream.chat, "user_id", None)):
        raise HTTPException(403, detail="Forbidden")

    # Get and configure the request parameters
    # --
    stream_id = db_stream.id
    model_name = db_stream.model_name
    mode = db_stream.mode
    query = db_stream.query
    # @DEBUG: This should be passed once, when the stream start, and not saved (pass parameters to the first call to start_stream)
    limit = db_stream.limit
    context = db_stream.context
    institution = db_stream.institution
    links = db_stream.links
    temperature = db_stream.temperature
    should_sids = db_stream.should_sids
    must_not_sids = db_stream.must_not_sids
    postprocessing = db_stream.postprocessing

    sources = None
    if db_stream.sources:
        sources = [source.source_name for source in db_stream.sources]

    history = None
    if db_stream.with_history:
        if not db_stream.chat_id:
            raise HTTPException(
                403, detail="No chat_id found. Stream with history requires a chat session."
            )

        history = []
        history_ = (
            db.query(models.Stream)
            .filter(models.Stream.chat_id == db_stream.chat.id)
            .order_by(models.Stream.id.asc())
        )
        history_size = history_.count()
        for i, stream in enumerate(history_):
            if not stream.query:
                # Occurs is a previous generation failed
                continue
            if not stream.response and i < history_size - 1:
                # Occurs if a generation was early stopped
                continue
            history.extend(
                [
                    {"role": "user", "content": stream.query},
                    {"role": "assistant", "content": stream.response},
                ]
            )
        # This should only remove the last (empty) assistant item.
        history = [item for item in history if item["content"] is not None]

    # Build the prompt
    # --
    # Build prompt
    prompter = get_prompter(model_name, mode)
    # We pass a mix of all kw arguments used by all prompters...
    # This is allowed because each prompter accepts **kwargs arguments...
    prompt = prompter.make_prompt(
        query=query,
        institution=institution,
        context=context,
        links=links,
        limit=limit,
        sources=sources,
        should_sids=should_sids,
        must_not_sids=must_not_sids,
        history=history,
    )

    # Ptompt length in number of words
    if isinstance(prompt, list):
        prompt_len = sum([len(m["content"].split()) for m in prompt])
    else:
        prompt_len = len(prompt.split())

    if prompt_len * 1.25 > prompter.sampling_params["max_tokens"] * 0.8:
        raise HTTPException(413, detail="Prompt too large")

    # Keep reference of rag used sources if any
    rag_sources = []
    if prompter.sources:
        rag_sources = prompter.sources

    # Allow client to tune the sampling parameters.
    sampling_params = prompter.get_upstream_sampling_params()
    sampling_params.update(
        {
            k: getattr(db_stream, k, None)
            for k in SamplingParams.model_fields
            if getattr(db_stream, k, None)
        }
    )

    # TODO: turn into async
    # Streaming case
    def generate():
        # Get the stream generator
        llm_client = LlmClient(model_name)
        generator = llm_client.generate(prompt, stream=True, **sampling_params)
        if ACTIVATE_SSE_WRAPPER:
            # Vllm.openai already returns an SSE encoded stream
            generator = sse_wrapper(generator)
        else:
            generator = de_sse_wrapper(generator)

        if postprocessing:
            # Postprocess the output stream
            generator = postprocess_sse_wrapper(generator, postprocessing)

        # Stream !
        crud.stream.set_is_streaming(db, db_stream, True)
        raw_response = ""
        try:
            while True:
                try:
                    yield next(generator)
                except StopIteration as e:
                    raw_response = e.value
                    break
        finally:
            # Get and refresh stream to prevent the following error:
            # sqlalchemy.orm.exc.ObjectDereferencedError: Can't emit change event
            # for attribute 'Stream.is_streaming' - parent object of type <Stream>
            # has been garbage collected.
            _db_stream = crud.stream.get_stream(db, stream_id)
            db.refresh(_db_stream)
            crud.stream.set_is_streaming(db, _db_stream, False, commit=False)
            crud.stream.set_rag_data(db, _db_stream, str(prompt), raw_response.strip(), rag_sources)

    return StreamingResponse(generate(), media_type="text/event-stream")


# TODO: stop has no effect for vllm (no callback), add warning in that case or handle it
@router.post("/stream/{stream_id}/stop", response_model=schemas.Stream, tags=["stream"])
def stop_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.Stream:
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    if current_user.id not in (db_stream.user_id, getattr(db_stream.chat, "user_id", None)):
        raise HTTPException(403, detail="Forbidden")

    crud.stream.set_is_streaming(db, db_stream, False)
    return db_stream.to_dict()
