import os
import json
import openai
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
)
import time
from core.log import get_logger

from core.config import settings

logger = get_logger("LLM")

# Initialize client once
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _is_quota_or_billing_error(exc):
    """Detects OpenAI quota/billing errors that should NOT be retried."""
    if isinstance(exc, openai.AuthenticationError):
        return True
    if isinstance(exc, openai.PermissionDeniedError):
        return True
    if isinstance(exc, openai.RateLimitError):
        error_msg = str(exc).lower()
        if "quota" in error_msg or "billing" in error_msg or "exceeded" in error_msg:
            return True
    return False


def _should_retry(exc):
    """Custom retry filter: retry transient errors, skip billing/quota errors."""
    if _is_quota_or_billing_error(exc):
        return False
    return isinstance(
        exc,
        (
            json.JSONDecodeError,
            ValueError,
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
        ),
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(_should_retry),
    reraise=True,
)
async def query_llm(
    system_prompt: str,
    user_content: str,
    model: str = None,
    temperature: float = None,
    config_key: str = None,
    json_mode: bool = False,
) -> str:
    """
    Robust LLM Query with central configuration.
    """

    # 1. Configuration Routing (New Structured Settings)
    # Defaults
    final_model = settings.get("GLOBAL_APP_CONFIG.llm_core.default_model", "gpt-4o")
    final_temp = settings.get("GLOBAL_APP_CONFIG.llm_core.temperature", 0.7)

    # Check settings for agent-specific config
    if config_key:
        # Priority 1: Check GLOBAL_APP_CONFIG (Most agents)
        agent_config = settings.get(f"GLOBAL_APP_CONFIG.llm_core.{config_key}")

        # Priority 2: Check CONVERSATION_FLOW_APP_CONFIG (Chat specific)
        if not agent_config:
            agent_config = settings.get(
                f"CONVERSATION_FLOW_APP_CONFIG.llm_chat.{config_key}"
            )

        if isinstance(agent_config, dict):
            final_model = agent_config.get("model", final_model)
            final_temp = agent_config.get("temperature", final_temp)

    # Apply direct overrides
    if model:
        final_model = model
    if temperature is not None:
        final_temp = temperature

    # 2. JSON Mode Logic
    # If the Agent requests JSON, force the model output format and temperature
    response_format = None
    if json_mode:
        response_format = {"type": "json_object"}
        final_temp = 0.2  # Force determinism for code/JSON

        # Ensure system prompt asks for JSON to avoid OpenAI 400 errors
        if "json" not in system_prompt.lower():
            system_prompt += "\n\nIMPORTANT: Output strictly in valid JSON format."

        logger.debug(f"JSON mode enabled for {config_key or 'query'}")

    try:
        # 3. Execution
        start_time = time.perf_counter()

        # High-level info for all users
        logger.info(f"📤 Querying {final_model} (Agent: {config_key or 'General'})")
        # Deep detail only for developers
        logger.debug(f"System Prompt: {system_prompt[:500]}...")
        logger.debug(f"User Content: {user_content[:500]}...")

        response = await client.chat.completions.create(
            model=final_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=final_temp,
            response_format=response_format,
        )

        latency = (time.perf_counter() - start_time) * 1000  # ms
        content = response.choices[0].message.content.strip()
        usage = response.usage

        # High-level results for all users
        token_info = f"Tokens: {usage.total_tokens} ({usage.prompt_tokens} in / {usage.completion_tokens} out)"
        logger.info(f"📥 Response from {final_model} in {latency:.0f}ms | {token_info}")
        # Raw response content only for developers
        logger.debug(f"Raw Response: {content}")

        # 4. Validation
        if json_mode:
            try:
                # Specific check to ensure valid JSON before returning
                json.loads(content)
                logger.debug(f"✅ Valid JSON received from {final_model}")
            except json.JSONDecodeError as e:
                logger.warning(
                    f"⚠️ LLM failed to produce valid JSON. Retrying... Error: {e}"
                )
                logger.debug(f"Invalid content: {content[:100]}")
                raise ValueError("Invalid JSON Output")  # Triggers @retry

        return content

    except openai.AuthenticationError as e:
        logger.critical(
            f"🔑 OPENAI AUTH ERROR [{config_key or 'General'}]: API key is invalid or expired. "
            f"Check your OPENAI_API_KEY environment variable. Details: {e}"
        )
        raise e

    except openai.RateLimitError as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "billing" in error_msg or "exceeded" in error_msg:
            logger.critical(
                f"💳 OPENAI QUOTA EXCEEDED [{config_key or 'General'}]: Your OpenAI account has run out of credits. "
                f"Add funds at https://platform.openai.com/account/billing. Details: {e}"
            )
            raise e  # Do NOT retry billing errors
        else:
            logger.warning(
                f"⏳ OPENAI RATE LIMITED [{config_key or 'General'}]: Too many requests. Will retry. Details: {e}"
            )
            raise e  # Let Tenacity handle transient rate limits

    except openai.PermissionDeniedError as e:
        logger.critical(
            f"🚫 OPENAI PERMISSION DENIED [{config_key or 'General'}]: Your API key lacks access to {final_model}. "
            f"Check your OpenAI plan and permissions. Details: {e}"
        )
        raise e

    except (openai.APIConnectionError, openai.APITimeoutError) as e:
        logger.error(
            f"🌐 OPENAI NETWORK ERROR [{config_key or 'General'}] on {final_model}: {e}"
        )
        raise e  # Let Tenacity handle the retry

    except Exception as e:
        logger.error(
            f"❌ LLM Failure [{config_key or 'General'}] on {final_model}: {type(e).__name__}: {e}"
        )
        raise e
