from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy.orm import Session

from app import models
from app.core import generate_v0
from app.deps import get_current_user, get_db

from pyalbert.schemas import RagChatCompletionRequest
from pyalbert.schemas.openai import ChatCompletionResponse

router = APIRouter()


@router.post("/chat/completions", tags=["openai"])
async def create_chat_completion(
    request: RagChatCompletionRequest,
    raw_request: Request,
    db: Session = Depends(get_db),
    # authentication needed
    current_user: models.User = Depends(get_current_user),
):
    if len(request.messages) == 0:
        raise HTTPException(413, detail="Empty messages, please provide at least one message.")

    # @TODO: For vllm openai compatible request on the back
    # generator = await openai_serving_chat.create_chat_completion(request, raw_request)
    # if isinstance(generator, proto.ErrorResponse):
    #    return JSONResponse(content=generator.model_dump(), status_code=generator.code)
    generator = generate_v0(request)

    if request.stream:
        return StreamingResponse(content=generator, media_type="text/event-stream")
    else:
        assert isinstance(generator, ChatCompletionResponse)
        return JSONResponse(content=generator.model_dump())
