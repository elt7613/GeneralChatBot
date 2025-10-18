from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

companion_llm = OpenAIChatModel(
    'openai/gpt-4.1-mini',
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)

conversation_analyzer_llm = OpenAIChatModel(
    'deepseek/deepseek-chat-v3.1',
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)

journal_analyzer_llm = OpenAIChatModel(
    'deepseek/deepseek-chat-v3.1',
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)