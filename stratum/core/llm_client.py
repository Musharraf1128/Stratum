"""
LLM Client Wrapper — handles communication with multiple LLM providers.

Supported providers:
  - OpenAI (gpt-4o-mini, gpt-4o, gpt-4, gpt-3.5-turbo)
  - Claude / Anthropic (claude-3-5-sonnet, claude-3-haiku, claude-3-opus)
  - Gemini / Google (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash)

Accepts an API key and provider per-call, executes the prompt,
and returns a standardized LLMResponse.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Pricing table (USD per 1K tokens) ──────────────────────────────────────
PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o-mini":       {"prompt": 0.000150, "completion": 0.000600},
    "gpt-4o":            {"prompt": 0.00250,  "completion": 0.01000},
    "gpt-4":             {"prompt": 0.03000,  "completion": 0.06000},
    "gpt-3.5-turbo":     {"prompt": 0.00050,  "completion": 0.00150},
    # Anthropic / Claude
    "claude-3-5-sonnet-latest": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku-20240307":  {"prompt": 0.00025, "completion": 0.00125},
    "claude-3-opus-latest":     {"prompt": 0.015, "completion": 0.075},
    # Google / Gemini
    "gemini-1.5-flash":  {"prompt": 0.000075, "completion": 0.000300},
    "gemini-1.5-pro":    {"prompt": 0.00125,  "completion": 0.00500},
    "gemini-2.0-flash":  {"prompt": 0.000075, "completion": 0.000300},
    "gemini-2.5-flash":  {"prompt": 0.000150, "completion": 0.000600},
}

# Default models per provider
DEFAULT_MODELS: dict[str, str] = {
    "openai":  "gpt-4o-mini",
    "claude":  "claude-3-5-sonnet-latest",
    "gemini":  "gemini-2.5-flash",
}

TIMEOUT_SECONDS = 60


@dataclass
class LLMResponse:
    """Standardized response from an LLM call."""
    output: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    finish_reason: str
    model: str


def _compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Compute USD cost from token counts and model pricing."""
    pricing = PRICING.get(model, {})
    if not pricing:
        # Try partial match
        for key in PRICING:
            if key in model or model in key:
                pricing = PRICING[key]
                break
    prompt_cost = (prompt_tokens / 1000) * pricing.get("prompt", 0)
    completion_cost = (completion_tokens / 1000) * pricing.get("completion", 0)
    return round(prompt_cost + completion_cost, 8)


def _get_default_model(provider: str) -> str:
    return DEFAULT_MODELS.get(provider, "gpt-4o-mini")


# ─── OpenAI ──────────────────────────────────────────────────────────────────

def _call_openai(
    api_key: str, prompt: str, model: str,
    system_prompt: Optional[str], temperature: float, max_tokens: int,
) -> LLMResponse:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

    if response.status_code != 200:
        _raise_api_error("OpenAI", response)

    data = response.json()
    choice = data["choices"][0]
    usage = data.get("usage", {})
    pt = usage.get("prompt_tokens", 0)
    ct = usage.get("completion_tokens", 0)
    actual_model = data.get("model", model)

    return LLMResponse(
        output=choice["message"]["content"],
        prompt_tokens=pt, completion_tokens=ct,
        total_tokens=usage.get("total_tokens", pt + ct),
        cost=_compute_cost(actual_model, pt, ct),
        finish_reason=choice.get("finish_reason", "unknown"),
        model=actual_model,
    )


# ─── Anthropic / Claude ─────────────────────────────────────────────────────

def _call_claude(
    api_key: str, prompt: str, model: str,
    system_prompt: Optional[str], temperature: float, max_tokens: int,
) -> LLMResponse:
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if system_prompt:
        body["system"] = system_prompt

    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=body,
        )

    if response.status_code != 200:
        _raise_api_error("Claude", response)

    data = response.json()
    content_blocks = data.get("content", [])
    output_text = "".join(
        b.get("text", "") for b in content_blocks if b.get("type") == "text"
    )
    usage = data.get("usage", {})
    pt = usage.get("input_tokens", 0)
    ct = usage.get("output_tokens", 0)
    actual_model = data.get("model", model)

    return LLMResponse(
        output=output_text,
        prompt_tokens=pt, completion_tokens=ct,
        total_tokens=pt + ct,
        cost=_compute_cost(actual_model, pt, ct),
        finish_reason=data.get("stop_reason", "unknown"),
        model=actual_model,
    )


# ─── Google / Gemini ─────────────────────────────────────────────────────────

def _call_gemini(
    api_key: str, prompt: str, model: str,
    system_prompt: Optional[str], temperature: float, max_tokens: int,
) -> LLMResponse:
    contents = []
    if system_prompt:
        contents.append({
            "role": "user",
            "parts": [{"text": f"System instruction: {system_prompt}"}]
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "Understood. I will follow those instructions."}]
        })
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )

    if response.status_code != 200:
        _raise_api_error("Gemini", response)

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    output_text = "".join(p.get("text", "") for p in parts)
    finish_reason = candidates[0].get("finishReason", "unknown")

    usage = data.get("usageMetadata", {})
    pt = usage.get("promptTokenCount", 0)
    ct = usage.get("candidatesTokenCount", 0)

    return LLMResponse(
        output=output_text,
        prompt_tokens=pt, completion_tokens=ct,
        total_tokens=pt + ct,
        cost=_compute_cost(model, pt, ct),
        finish_reason=finish_reason.lower(),
        model=model,
    )


# ─── Shared helpers ──────────────────────────────────────────────────────────

def _raise_api_error(provider: str, response: httpx.Response):
    try:
        error_json = response.json()
        if "error" in error_json:
            err = error_json["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        else:
            msg = json.dumps(error_json)
    except Exception:
        msg = response.text
    raise RuntimeError(f"{provider} API error ({response.status_code}): {msg}")


# ─── Main entry point ───────────────────────────────────────────────────────

def call_llm(
    api_key: str,
    prompt: str,
    provider: str = "openai",
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> LLMResponse:
    """
    Call an LLM provider.

    Args:
        api_key: The user's API key (plain text, decrypted by caller).
        prompt: The user/agent prompt to send.
        provider: One of "openai", "claude", "gemini".
        model: Model identifier (defaults to provider's default model).
        system_prompt: Optional system-level instruction.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in the completion.

    Returns:
        LLMResponse with output text, token counts, cost, and finish reason.
    """
    if not model:
        model = _get_default_model(provider)

    provider = provider.lower().strip()

    if provider == "openai":
        return _call_openai(api_key, prompt, model, system_prompt, temperature, max_tokens)
    elif provider in ("claude", "anthropic"):
        return _call_claude(api_key, prompt, model, system_prompt, temperature, max_tokens)
    elif provider in ("gemini", "google"):
        return _call_gemini(api_key, prompt, model, system_prompt, temperature, max_tokens)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
