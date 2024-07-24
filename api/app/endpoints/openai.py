import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy.orm import Session

from app import models
from app.core import albert_request_intercept
from app.deps import get_current_user

from pyalbert import get_logger
from pyalbert.config import LLM_API_VER, LLM_TABLE
from pyalbert.schemas import RagChatCompletionRequest
from pyalbert.schemas.openai import ChatCompletionRequest

logger = get_logger()

router = APIRouter()


async def forward_stream(
    url: str, request: Request, headers: dict | None = None, json: dict | None = None
):
    """Asynchronous generator function that relay a stream from request to a given target API."""
    async with httpx.AsyncClient(timeout=20) as client:
        async with client.stream(
            request.method,
            url,
            headers=headers,
            params=request.query_params,
            json=json,
        ) as response:
            #response.raise_for_status() ?
            async for chunk in response.aiter_raw():
                yield chunk


@router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], tags=["openai"]
)
async def openai_api_proxy(
    request: Request,
    path: str,  # authentication needed
    current_user: models.User = Depends(get_current_user),
):
    """
    Proxy endpoint that forwards requests to the OpenAI API.

    This endpoint acts as a proxy, forwarding incoming requests to the OpenAI API
    with the same method, headers, query parameters, and JSON body. It supports GET, POST,
    PUT, DELETE, and PATCH methods.

    If the JSON body contains a key "stream" with a value of True, the response from the
    OpenAI API is streamed back to the client as Server-Sent Events (SSE). Otherwise, the
    response is returned normally.

    Parameters:
    - request (Request): The incoming HTTP request.
    - path (str): The sub-path to be appended to the OpenAI API base URL.

    Returns:
    - StreamingResponse: If "stream" is True in the JSON body, returns a streaming response
      with the content from the OpenAI API.
    - JSON: If "stream" is not present or False, returns the JSON response from the OpenAI API.

    Raises:
    - HTTPException: If the JSON body is invalid or if there is an error forwarding the request.
    """
    client = httpx.AsyncClient(timeout=20)

    # Determine if we need to forward a JSON body
    json_body = None
    stream = False
    model = None
    target_url = None
    prompter = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # Request Interception
            json_body = await request.json()
            stream = json_body.get("stream", stream)
            model = json_body.get("model")
            if not model:
                raise HTTPException(status_code=403, detail="model parameter is required.")
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Invalid JSON body ({err})")

        _model = next((m for m in LLM_TABLE if m["model"] == model), None)
        if not _model:
            raise HTTPException(status_code=403, detail="LLM model not found: %s" % model)

        target_url = (
            f"{_model['url']}/{LLM_API_VER}/{path}" if LLM_API_VER else f"{_model['url']}/{path}"
        )

        if path == "chat/completions":
            json_data = RagChatCompletionRequest(**json_body)
            json_data, prompter = await run_in_threadpool(albert_request_intercept, json_data)
            upstream_fields = set(RagChatCompletionRequest.model_fields.keys()) - set(ChatCompletionRequest.model_fields.keys())  # fmt: off
            # Warning: The JSON body will include all default values defined in the schema,
            # potentially leading to unnecessary network payload.
            # Furthermore, it causes openapi openai issue due to non-aligned default_factory value in the spec.
            json_body = json_data.model_dump(exclude=upstream_fields, exclude_unset=True)

    else:
        raise NotImplementedError

    headers_to_keep = ["Authorization"]
    headers = {h: request.headers[h] for h in headers_to_keep if h in request.headers}

    try:
        if stream:
            # Return a streaming response
            return StreamingResponse(
                content=forward_stream(target_url, request, headers=headers, json=json_body),
                media_type="text/event-stream",
            )

        # Forward the request to the target API
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.query_params,
            json=json_body,
        )
        response.raise_for_status()

        # Return the response from the target API
        data = response.json()

        # Add sources if any
        # @TODO: Align pyalbert.Prompter with RagContext.
        # @TODO: Handle other strategy (see tools in albert-api)
        sources = getattr(prompter, "sources", None)
        if sources:
            data["rag_context"] = [{"strategy":"last", "references":sources}]

        return data
    except httpx.HTTPStatusError as err:
        error_detail = err.response.json()
        raise HTTPException(status_code=err.response.status_code, detail=error_detail)
    except httpx.RequestError as err:
        logger.error(f"{err}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        await client.aclose()
