"""Unified, provider-agnostic LLM client (OpenAI-compatible chat completions).

Usage
-----
    from llm_client import LLMClient
    client = LLMClient(provider="deepseek", model="deepseek-chat")
    text = client.complete("hello", system="You are helpful.")

To switch provider/model in the future, change ONLY:
  * provider  -> key in PROVIDERS below
  * model     -> model name string
  * api key   -> export the matching *_API_KEY env var (or pass api_key=...)

No third-party dependencies (stdlib only), so it runs anywhere Python runs.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

PROVIDERS: dict[str, dict[str, str]] = {
    # provider   : base_url (OpenAI-compatible), default model, key env var
    "river": {
        "base_url": "https://api.river.ai/v1",
        "default_model": "deepseek-ai/DeepSeek-V4.1-Flash",
        "api_key_env": "RIVER_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "deepseek/deepseek-chat",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}

_RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}


class LLMClient:
    """Minimal chat-completions client with retries. Provider = a PROVIDERS key."""

    def __init__(
        self,
        provider: str = "deepseek",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 90,
        max_retries: int = 4,
        temperature: float = 0.0,
        max_tokens: int = 128,
    ) -> None:
        if provider not in PROVIDERS:
            raise ValueError(
                f"unknown provider {provider!r}; known: {sorted(PROVIDERS)}"
            )
        conf = PROVIDERS[provider]
        self.provider = provider
        self.base_url = (base_url or conf["base_url"]).rstrip("/")
        self.model = model or conf["default_model"]
        self.api_key = api_key or os.environ.get(conf["api_key_env"])
        if not self.api_key:
            raise RuntimeError(
                f"no API key for provider {provider!r}: set the "
                f"{conf['api_key_env']} environment variable "
                f"(e.g. export {conf['api_key_env']}=sk-...) or pass api_key=..."
            )
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens

    # ------------------------------------------------------------------ API
    def chat(self, messages: list[dict[str, str]]) -> str:
        """Send chat messages, return the assistant text (content)."""
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                choices = payload.get("choices") or []
                if not choices:
                    raise RuntimeError(f"no choices in response: {str(payload)[:200]}")
                return choices[0]["message"]["content"] or ""
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:300]
                last_error = RuntimeError(f"API HTTP {exc.code}: {detail}")
                if exc.code in _RETRYABLE_HTTP and attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                raise last_error from exc
            except OSError as exc:
                # Covers URLError, TimeoutError and raw socket errors such as
                # "Can't assign requested address" (temporary port exhaustion)
                # or connection resets - all retryable.
                last_error = RuntimeError(f"network error: {exc}")
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                raise last_error from exc
        raise last_error if last_error else RuntimeError("call failed")

    def complete(self, prompt: str, system: str | None = None) -> str:
        """Convenience wrapper for a single user prompt (optional system msg)."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)


if __name__ == "__main__":
    c = LLMClient()
    print(f"provider={c.provider} model={c.model} base_url={c.base_url}")
    print("reply:", c.complete("Reply with exactly: OK"))
