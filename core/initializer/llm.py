import os
import json
import openai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from data.scripts.data import MODEL_CONFIG
from core.log import get_logger

from core.config import settings

logger = get_logger("LLM")

# Initialize client once
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        json.JSONDecodeError, 
        ValueError, 
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.RateLimitError
    )),
    reraise=True
)
async def query_llm(
    system_prompt: str, 
    user_content: str, 
    model: str = None,
    temperature: float = None,
    config_key: str = None, 
    json_mode: bool = False
) -> str:
    """
    Robust LLM Query with central configuration.
    """
    
    # 1. Configuration Routing (Prioritize settings.json > model_config.json)
    # Defaults
    final_model = settings.get('llm.default_model', 'gpt-4o')
    final_temp = settings.get('llm.temperature', 0.7)
    
    # Check settings.json for agent-specific config first
    if config_key:
        agent_config = settings.get(f'llm.{config_key}')
        if isinstance(agent_config, dict):
            final_model = agent_config.get("model", final_model)
            final_temp = agent_config.get("temperature", final_temp)
        
        # Fallback to legacy model_config.json if not in settings
        elif config_key in MODEL_CONFIG:
            node = MODEL_CONFIG[config_key]
            if isinstance(node, dict):
                final_model = node.get("model", final_model)
                final_temp = node.get("temperature", final_temp)
            else:
                final_model = node  # Simple string config

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
        if settings.get('app.detailed_request_logging'):
            logger.info(f"📤 LLM Request [{final_model}]: {system_prompt[:50]}... | User: {user_content[:50]}...")

        response = await client.chat.completions.create(
            model=final_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=final_temp,
            response_format=response_format
        )
        
        content = response.choices[0].message.content.strip()
        
        if settings.get('app.detailed_request_logging'):
             logger.info(f"📥 LLM Response: {content[:100]}...")

        # 4. Validation
        if json_mode:
            try:
                # Specific check to ensure valid JSON before returning
                json.loads(content)
                logger.debug(f"✅ Valid JSON received from {final_model}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ LLM failed to produce valid JSON. Retrying... Error: {e}")
                logger.debug(f"Invalid content: {content[:100]}")
                raise ValueError("Invalid JSON Output")  # Triggers @retry

        return content

    except Exception as e:
        logger.error(f"❌ LLM Failure [{config_key or 'General'}] on {final_model}: {e}")
        raise e  # Let Tenacity handle the retry
