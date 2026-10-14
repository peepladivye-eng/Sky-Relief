"""
SkyRelief — unified LLM / VLM client.

All calls go through this module so retry logic, JSON parsing and error
handling are in one place.  The client is OpenAI-compatible; set
LLM_BASE_URL to use Nebius, Together, Groq, or local Ollama.
Gemini support is provided via google-generativeai when LLM_BASE_URL
contains "generativelanguage.googleapis.com".
"""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from config import (
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, VLM_MODEL, LLM_MAX_RETRIES
)
from schemas import LLMError

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ── helpers ───────────────────────────────────────────────────────────────────

def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        h["Authorization"] = f"Bearer {LLM_API_KEY}"
    return h


def _encode_image(path: Path) -> str:
    """Return base64-encoded image string."""
    return base64.b64encode(path.read_bytes()).decode()


def _strip_json_fence(text: str) -> str:
    """Remove ```json … ``` fences that models sometimes emit."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first and last fence lines
        inner = lines[1:] if lines[0].startswith("```") else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner)
    return text


# ── core call ─────────────────────────────────────────────────────────────────

def _chat(
    messages: list[dict],
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    timeout: float = 60.0,
) -> str:
    """
    Send a chat-completion request; return raw assistant text.
    Raises httpx.HTTPStatusError on non-2xx.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=_headers(), json=payload)
        r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


# ── public API ────────────────────────────────────────────────────────────────

def llm_json(
    system: str,
    user: str,
    schema: Type[T],
    model: str | None = None,
    temperature: float = 0.2,
) -> T | LLMError:
    """
    Call the text LLM; parse the response as *schema*.
    Retries once on parse failure.  Returns LLMError on persistent failure.
    """
    model = model or LLM_MODEL
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            raw = _chat(messages, model=model, temperature=temperature)
            cleaned = _strip_json_fence(raw)
            return schema.model_validate_json(cleaned)
        except (ValidationError, json.JSONDecodeError) as exc:
            log.warning("LLM parse error attempt %d: %s", attempt + 1, exc)
            if attempt < LLM_MAX_RETRIES:
                # Add correction message and retry
                messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Your response was not valid JSON matching the required schema. "
                        f"Error: {exc}. "
                        f"Please respond with ONLY valid JSON, no markdown fences."
                    ),
                })
        except Exception as exc:
            log.error("LLM call failed: %s", exc)
            return LLMError(error=str(exc))
    return LLMError(error="Max retries exceeded", raw=raw)  # type: ignore[possibly-undefined]


def vlm_json(
    system: str,
    user_text: str,
    image_paths: list[Path],
    schema: Type[T],
    model: str | None = None,
    temperature: float = 0.2,
) -> T | LLMError:
    """
    Call the vision LLM with up to N images (sent as base64 data URIs).
    Parse response as *schema*.  Retries once.
    """
    model = model or VLM_MODEL

    content: list[dict] = []
    for img in image_paths:
        suffix = img.suffix.lstrip(".").lower()
        mime   = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{_encode_image(img)}"},
        })
    content.append({"type": "text", "text": user_text})

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": content},
    ]
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            raw = _chat(messages, model=model, temperature=temperature)
            cleaned = _strip_json_fence(raw)
            return schema.model_validate_json(cleaned)
        except (ValidationError, json.JSONDecodeError) as exc:
            log.warning("VLM parse error attempt %d: %s", attempt + 1, exc)
            if attempt < LLM_MAX_RETRIES:
                messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": (
                            f"Your response was not valid JSON. Error: {exc}. "
                            "Respond with ONLY valid JSON, no markdown fences."
                        ),
                    }],
                })
        except Exception as exc:
            log.error("VLM call failed: %s", exc)
            return LLMError(error=str(exc))
    return LLMError(error="Max retries exceeded", raw=raw)  # type: ignore[possibly-undefined]


def llm_available() -> bool:
    """Quick connectivity check — returns False if no API key or base URL set."""
    return bool(LLM_BASE_URL and LLM_API_KEY)
