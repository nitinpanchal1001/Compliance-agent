"""LiteLLM wrapper — routes chat completions to the configured provider/model.

Reasoning uses JSON-mode so the model returns structured, parseable output. The
provider is whatever LiteLLM resolves from the model name (gpt-4o → OpenAI,
claude-* → Anthropic, ollama/* → local), using API keys from the environment.
"""

import json

import litellm
import structlog

from core.config import get_settings

settings = get_settings()
log = structlog.get_logger()

# Don't blow up if a provider doesn't support an optional param we pass.
litellm.drop_params = True


def chat_json(
    system: str,
    user: str,
    model: str | None = None,
    temperature: float | None = None,
    max_retries: int = 2,
) -> dict:
    """Call the LLM and parse a JSON object from its reply.

    Raises the last error if every attempt fails (caller decides whether to retry
    the surrounding task).
    """
    model = model or settings.litellm_reasoning_model
    temperature = settings.reasoning_temperature if temperature is None else temperature

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = litellm.completion(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or "{}"
            return json.loads(content)
        except json.JSONDecodeError as e:
            last_err = e
            log.warning("llm.json_parse_failed", attempt=attempt, error=str(e))
        except Exception as e:
            last_err = e
            log.warning("llm.call_failed", attempt=attempt, model=model, error=str(e))

    assert last_err is not None
    raise last_err
