from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

general_llm = OpenAIChatModel(
    'google/gemini-2.5-flash-lite',
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)