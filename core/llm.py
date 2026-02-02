import os
import json
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from data.scripts.data import MODEL_CONFIG
from core.log import get_logger

logger = get_logger("LLM")

# Initialize client once
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
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
    Robust LLM Query with:
    1. Automatic Retries (Tenacity) - 3 attempts with exponential backoff
    2. JSON Mode Enforcement (Critical for Agents)
    3. Centralized Model Routing
    4. Validation for JSON responses
    
    Args:
        system_prompt: System instructions for the LLM
        user_content: User query/content
        model: Override model (optional)
        temperature: Override temperature (optional)
        config_key: Config key for model routing (e.g., 'market', 'tactics')
        json_mode: If True, enforces JSON output and validates it
    
    Returns:
        str: LLM response (validated JSON string if json_mode=True)
    """
    
    # 1. Configuration Routing
    # Defaults
    final_model = "gpt-4o" 
    final_temp = 0.7

    # Load specific config if provided (e.g., 'market' agent needs low temp)
    if config_key and config_key in MODEL_CONFIG:
        node = MODEL_CONFIG[config_key]
        if isinstance(node, dict):
            final_model = node.get("model", final_model)
            final_temp = node.get("temperature", final_temp)
        else:
            final_model = node  # Simple string config

    # Apply overrides
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
