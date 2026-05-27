"""
API routes for the Cloudflare LLM Proxy.
Provides OpenAI-compatible endpoints that proxy requests to Cloudflare Workers AI.
"""

import json
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from auth import verify_admin_key, verify_proxy_api_key
from config import settings
from database import generate_api_key, list_api_keys, revoke_api_key

router = APIRouter()

# ---------------------------------------------------------------------------
# Cloudflare API helpers
# ---------------------------------------------------------------------------

CF_BASE = "https://api.cloudflare.com/client/v4"


def _cf_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.cloudflare_api_token}",
        "Content-Type": "application/json",
    }


def _cf_url(path: str) -> str:
    return f"{CF_BASE}/accounts/{settings.cloudflare_account_id}{path}"


# ---------------------------------------------------------------------------
# Pydantic models for OpenAI-compatible request / response
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str
    content: str | list[dict[str, Any]] | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    seed: Optional[int] = None
    stop: Optional[str | list[str]] = None


class EmbeddingRequest(BaseModel):
    model: str
    input: str | list[str]
    encoding_format: Optional[str] = None


# ---------------------------------------------------------------------------
# Admin endpoints  (protected by ADMIN_API_KEY)
# ---------------------------------------------------------------------------


@router.get("/admin/keys", dependencies=[Depends(verify_admin_key)])
async def get_api_keys():
    """List all proxy API keys (without exposing the full key values)."""
    keys = list_api_keys()
    return {"keys": keys}


@router.post("/admin/keys", dependencies=[Depends(verify_admin_key)])
async def create_api_key(name: str = "default"):
    """Generate a new proxy API key."""
    key_data = generate_api_key(name)
    return {"key": key_data}


@router.delete("/admin/keys/{key_id}", dependencies=[Depends(verify_admin_key)])
async def delete_api_key(key_id: int):
    """Revoke a proxy API key by its ID."""
    success = revoke_api_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"detail": "API key revoked"}


# ---------------------------------------------------------------------------
# OpenAI-compatible endpoints  (protected by proxy API key)
# ---------------------------------------------------------------------------


@router.get("/v1/models", dependencies=[Depends(verify_proxy_api_key)])
async def list_models():
    """
    Return a list of available models.
    We return a curated list of popular Workers AI models.
    Users can browse the full list at https://developers.cloudflare.com/workers-ai/models/
    """
    models = [
        {
            "id": "@cf/meta/llama-3.1-8b-instruct",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/meta/llama-3.1-70b-instruct",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/meta/llama-3.2-3b-instruct",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/meta/llama-3.2-11b-instruct",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/mistral/mistral-7b-instruct-v0.1",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/mistral/mistral-7b-instruct-v0.2-lora",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@hf/thebloke/deepseek-coder-6.7b-instruct-awq",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/qwen/qwen2-7b-instruct",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/qwen/qwen2-72b-instruct",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/openai/gpt-oss-120b",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
        {
            "id": "@cf/baai/bge-large-en-v1.5",
            "object": "model",
            "created": 1720000000,
            "owned_by": "cloudflare",
        },
    ]
    return {"object": "list", "data": models}


@router.post("/v1/chat/completions", dependencies=[Depends(verify_proxy_api_key)])
async def chat_completions(request: ChatCompletionRequest, raw_request: Request):
    """
    OpenAI-compatible chat completions endpoint.
    Proxies the request to Cloudflare Workers AI.
    Supports both streaming and non-streaming responses.
    """
    if not settings.cloudflare_account_id or not settings.cloudflare_api_token:
        raise HTTPException(
            status_code=500,
            detail="Cloudflare credentials not configured on the proxy server",
        )

    # Build the Cloudflare API request body
    cf_payload: dict[str, Any] = {
        "messages": [m.model_dump() for m in request.messages],
    }

    # Copy over optional parameters if provided
    for field in (
        "temperature",
        "top_p",
        "top_k",
        "max_tokens",
        "stream",
        "frequency_penalty",
        "presence_penalty",
        "seed",
    ):
        val = getattr(request, field, None)
        if val is not None:
            cf_payload[field] = val

    # Handle 'stop' parameter
    if request.stop is not None:
        if isinstance(request.stop, list):
            cf_payload["stop"] = request.stop
        else:
            cf_payload["stop"] = [request.stop]

    # Determine the Cloudflare model endpoint
    model_path = request.model
    cf_url = _cf_url(f"/ai/run/{model_path}")

    # ---- Streaming ----
    if request.stream:
        return await _stream_chat_completion(cf_url, cf_payload, request.model)

    # ---- Non-streaming ----
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(cf_url, headers=_cf_headers(), json=cf_payload)
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, detail=f"Error contacting Cloudflare API: {e}"
            )

    if response.status_code != 200:
        detail = _extract_cf_error(response)
        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        )

    cf_result = response.json()
    cf_response_text = cf_result.get("result", {}).get("response", "")

    # Build OpenAI-compatible response
    openai_response = {
        "id": f"chatcmpl-{id(cf_response_text)}",
        "object": "chat.completion",
        "created": 1720000000,
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": cf_response_text,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": cf_result.get("result", {}).get("prompt_tokens", 0),
            "completion_tokens": cf_result.get("result", {}).get("completion_tokens", 0),
            "total_tokens": cf_result.get("result", {}).get("total_tokens", 0),
        },
    }

    return openai_response


async def _stream_chat_completion(cf_url: str, cf_payload: dict, model: str):
    """
    Handle streaming chat completions.
    Cloudflare supports SSE streaming, which we convert to OpenAI-compatible SSE format.
    """
    cf_payload["stream"] = True

    async def event_stream():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", cf_url, headers=_cf_headers(), json=cf_payload
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    yield f"data: {json.dumps({'error': {'message': error_body.decode(), 'type': 'cf_error'}})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                # Cloudflare streams SSE events as "data: {...}\n\n"
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # strip "data: " prefix
                    if data_str == "[DONE]":
                        yield "data: [DONE]\n\n"
                        return

                    try:
                        cf_chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Cloudflare streaming response format:
                    # {"response": "...", "p": null}
                    response_text = cf_chunk.get("response", "")

                    openai_chunk = {
                        "id": f"chatcmpl-{id(response_text)}",
                        "object": "chat.completion.chunk",
                        "created": 1720000000,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "content": response_text,
                                },
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(openai_chunk)}\n\n"

                # Send final [DONE] if stream ended naturally
                yield "data: [DONE]\n\n"

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/v1/embeddings", dependencies=[Depends(verify_proxy_api_key)])
async def embeddings(request: EmbeddingRequest):
    """
    OpenAI-compatible embeddings endpoint.
    Proxies the request to Cloudflare Workers AI.
    """
    if not settings.cloudflare_account_id or not settings.cloudflare_api_token:
        raise HTTPException(
            status_code=500,
            detail="Cloudflare credentials not configured on the proxy server",
        )

    cf_url = _cf_url(f"/ai/run/{request.model}")

    cf_payload: dict[str, Any] = {}
    if isinstance(request.input, list):
        cf_payload["text"] = request.input
    else:
        cf_payload["text"] = request.input

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(cf_url, headers=_cf_headers(), json=cf_payload)
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, detail=f"Error contacting Cloudflare API: {e}"
            )

    if response.status_code != 200:
        detail = _extract_cf_error(response)
        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        )

    cf_result = response.json()
    cf_data = cf_result.get("result", {}).get("data", [])

    # Build OpenAI-compatible response
    openai_response = {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "index": i,
                "embedding": item,
            }
            for i, item in enumerate(cf_data)
        ],
        "model": request.model,
        "usage": {
            "prompt_tokens": cf_result.get("result", {}).get("prompt_tokens", 0),
            "total_tokens": cf_result.get("result", {}).get("total_tokens", 0),
        },
    }

    return openai_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_cf_error(response: httpx.Response) -> str:
    """Extract a human-readable error message from a Cloudflare API error response."""
    try:
        body = response.json()
        errors = body.get("errors", [])
        if errors:
            return errors[0].get("message", str(errors))
        return body.get("error", str(body))
    except Exception:
        return response.text[:500]
