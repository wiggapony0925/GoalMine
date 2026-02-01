import os
from openai import AsyncOpenAI

# Initialize the async client
# Ensure OPENAI_API_KEY is set in .env
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def query_llm(system_prompt, user_content, model="gpt-4o", temperature=0.7):
    """
    Helper function to query OpenAI Chat Completion.
    """
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error querying LLM: {str(e)}"
