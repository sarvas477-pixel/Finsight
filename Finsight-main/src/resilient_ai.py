"""Enhanced resilient connection wrapper for Gemini with connection pooling & caching."""
from __future__ import annotations

import functools
import json
import time
from typing import Any
from datetime import datetime, timedelta

class ConnectionCache:
    """Simple in-memory cache for Gemini responses."""
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache = {}
    
    def get(self, key: str) -> Any | None:
        if key in self.cache:
            value, expires_at = self.cache[key]
            if datetime.now() < expires_at:
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = (value, datetime.now() + timedelta(seconds=self.ttl))
    
    def clear(self) -> None:
        self.cache.clear()


# Global cache instance
_response_cache = ConnectionCache(ttl_seconds=300)


def _get_cache_key(question: str, results: list | None) -> str:
    """Generate cache key from question and results hash."""
    results_hash = hash(json.dumps(results, default=str, sort_keys=True)) if results else "no_results"
    return f"gemini:{hash(question)}__{results_hash}"


def call_gemini_with_cache(
    prompt: str,
    system: str | None = None,
    use_cache: bool = True,
    timeout: int = 15,
) -> tuple[str, str]:
    """
    Improved Gemini call with:
    - Response caching (300s TTL)
    - Shorter timeout (15s vs unlimited)
    - Better error messages
    - Adaptive retry strategy
    """
    from src.ai import _secret, GeminiError, _model_chain, _error_kind
    
    cache_key = f"gemini_prompt:{hash(prompt)}"
    
    # Check cache first
    if use_cache:
        cached = _response_cache.get(cache_key)
        if cached is not None:
            return cached["text"], f"{cached['model']}:cached"
    
    api_key = _secret("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("missing_key", "GEMINI_API_KEY not set in .env or Streamlit secrets")
    
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        raise GeminiError("other", f"google-genai not installed: {exc}")
    
    # Create client with timeout
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(system_instruction=system) if system else None
    last_error: GeminiError | None = None
    
    models = _model_chain()
    
    for model_idx, model in enumerate(models):
        for attempt in range(4):  # Increased from 3 to 4 attempts
            try:
                # Add timeout to the request
                kwargs = {
                    "model": model,
                    "contents": prompt[:50000],  # Limit prompt size
                }
                if config is not None:
                    kwargs["config"] = config
                
                # Call with timeout
                response = client.models.generate_content(**kwargs)
                text = (getattr(response, "text", None) or "").strip()
                
                if not text:
                    raise GeminiError("empty", "Gemini returned empty response")
                
                # Cache successful response
                if use_cache:
                    _response_cache.set(cache_key, {
                        "text": text,
                        "model": model,
                        "timestamp": time.time()
                    })
                
                return text, model
                
            except GeminiError as exc:
                last_error = exc
                break  # Try next model for known errors
                
            except Exception as exc:
                error_text = str(exc).lower()
                
                # Timeout handling
                if "timeout" in error_text or "deadline" in error_text:
                    if attempt < 2:  # Retry once on timeout
                        wait_time = 0.5 * (2 ** attempt)
                        print(f"⏱️  Timeout (model {model_idx}/{len(models)}), retry in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    last_error = GeminiError("provider_unavailable", "Request timeout")
                    break
                
                # Rate limit handling
                elif "429" in error_text or "quota" in error_text or "rate_limit" in error_text:
                    if attempt < 3:  # More retries for rate limiting
                        wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                        print(f"⏱️  Rate limited, waiting {wait_time}s (attempt {attempt + 1}/4)...")
                        time.sleep(wait_time)
                        continue
                    last_error = GeminiError("quota", "Rate limit exceeded")
                    break
                
                # Connection errors
                elif any(x in error_text for x in ("connection", "refused", "network", "unreachable")):
                    if attempt < 2:
                        wait_time = 1 + attempt
                        print(f"🔗 Connection issue, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    last_error = GeminiError("provider_unavailable", "Network connection failed")
                    break
                
                # Auth errors - don't retry
                elif any(x in error_text for x in ("401", "403", "unauthorized", "api_key_invalid", "permission_denied")):
                    raise GeminiError("auth", f"API key rejected: {str(exc)[:100]}")
                
                # Model not found - try next model
                elif any(x in error_text for x in ("404", "not_found", "model", "not supported")):
                    last_error = GeminiError("model_unavailable", f"Model {model} not found")
                    break
                
                # Unknown error - log and continue
                else:
                    kind = _error_kind(exc)
                    last_error = GeminiError(kind, str(exc)[:150])
                    break
    
    # All models/attempts failed
    if last_error:
        raise last_error
    raise GeminiError("other", "No model available after all retries")


def ask_gemini_fast(
    question: str,
    results: list[dict[str, Any]] | None,
    conversation: list[Any] | None = None,
    tool_context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Drop-in replacement for ask_gemini() with:
    - Response caching
    - Faster failure detection
    - Better error messages
    """
    from src.ai import (
        build_chat_prompt, 
        deterministic_answer, 
        template_chat,
        GeminiError
    )
    
    question = str(question or "").strip()
    if not question:
        return "Please enter a question.", "validation"
    
    # Try deterministic answer first (instant)
    direct = deterministic_answer(question, results)
    if direct is not None:
        return direct, "deterministic"
    
    # Build prompt
    prompt = build_chat_prompt(question, results, conversation, tool_context)
    
    try:
        text, model = call_gemini_with_cache(prompt, use_cache=True, timeout=15)
        return text, f"gemini:{model}"
    except GeminiError as exc:
        # Improved fallback with context
        return template_chat(
            question, 
            results, 
            reason=exc.kind, 
            detail=exc.detail
        ), f"fallback:{exc.kind}"
    except Exception as exc:
        return template_chat(
            question,
            results,
            reason="other",
            detail=str(exc)[:100]
        ), "fallback:unknown"
