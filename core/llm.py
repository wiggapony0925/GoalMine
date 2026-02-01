import os
import json
import logging
from openai import AsyncOpenAI

logger = logging.getLogger("GoalMine")

# Initialize the async client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Model Config
CONFIG_PATH = "data/model_config.json"
try:
    with open(CONFIG_PATH, "r") as f:
        MODEL_CONFIG = json.load(f)
except Exception as e:
    logger.warning(f"Could not load model_config.json: {e}. Using hardcoded defaults.")
    MODEL_CONFIG = {"default_model": "gpt-4o"}

async def query_llm(system_prompt, user_content, model=None, temperature=None, config_key=None):
    """
    Helper function to query OpenAI Chat Completion with Model Routing.
    """
    # 1. Determine Model & Temperature from Config or Defaults
    final_model = MODEL_CONFIG.get("default_model", "gpt-4o")
    final_temp = 0.7

    if config_key and config_key in MODEL_CONFIG:
        node = MODEL_CONFIG[config_key]
        if isinstance(node, dict):
            final_model = node.get("model", final_model)
            final_temp = node.get("temperature", final_temp)
        else:
            final_model = node

    # 2. Overrides from function arguments
    if model: final_model = model
    if temperature is not None: final_temp = temperature

    try:
        response = await client.chat.completions.create(
            model=final_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=final_temp
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM Error ({final_model}): {e}")
        return f"Error querying LLM: {str(e)}"
