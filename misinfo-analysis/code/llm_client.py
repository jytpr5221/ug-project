"""Minimal OpenAI-compatible chat client (stdlib only)."""

import json
import os
import time
import urllib.error
import urllib.request

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.river.ai/v1",  # DeepSeek served via River
        "default_model": "deepseek-ai/DeepSeek-V4.1-Flash",
        "api_key_env": "RIVER_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-3.5-flash",
        "api_key_env": "GEMINI_API_KEY",
    },
    "merge": {
        "base_url": "https://api-gateway.merge.dev/v1",
        "default_model": "gpt-6.1-sol",
        "api_key_env": "MERGE_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "openai/gpt-oss-120b",
        "api_key_env": "GROQ_API_KEY",
    },
    "groq2": {
        "base_url": "https://api.groq.com/openai/v1",  # second account, extra quota
        "default_model": "openai/gpt-oss-120b",
        "api_key_env": "GROQ2_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "qwen/qwen3.8-flash",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}

_RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}
_USER_AGENT = "llm-eval-client/1.0"  # Groq's bot check rejects the default urllib UA


class LLMClient:
    def __init__(self, provider="deepseek", model=None, api_key=None, base_url=None,
                 timeout=90, max_retries=4, temperature=0.0, max_tokens=128):
        conf = PROVIDERS.get(provider)
        if conf is None:
            raise ValueError(f"unknown provider {provider!r}; known: {sorted(PROVIDERS)}")
        self.provider = provider
        self.base_url = (base_url or conf["base_url"]).rstrip("/")
        self.model = model or conf["default_model"]
        self.api_key = api_key or os.environ.get(conf["api_key_env"])
        if not self.api_key:
            raise RuntimeError(f"missing {conf['api_key_env']} for provider {provider!r}")
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, messages: list[dict[str, str]]) -> str:
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": _USER_AGENT,
        }
        url = f"{self.base_url}/chat/completions"

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(url, data=body, headers=headers)
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
                    time.sleep(20 * attempt if exc.code == 429 else 2 ** attempt)
                    continue
                raise last_error from exc
            except OSError as exc:  # timeouts, resets, temporary port exhaustion
                last_error = RuntimeError(f"network error: {exc}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise last_error from exc
        raise last_error or RuntimeError("call failed")

    def complete(self, prompt: str, system: str | None = None) -> str:
        messages = [{"role": "system", "content": system}] if system else []
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)


if __name__ == "__main__":
    c = LLMClient()
    print(c.provider, c.model)
    print(c.complete("Reply with exactly: OK"))
