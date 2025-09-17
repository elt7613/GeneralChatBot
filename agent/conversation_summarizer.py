from pydantic_ai import Agent
from config.llm import general_llm
from pydantic import BaseModel, Field
from typing import List

class ConversationSummary(BaseModel):
    """Model for conversation summarization output"""
    main_intent: str = Field(..., description="The primary purpose or goal of the conversation")
    key_points: List[str] = Field(..., description="List of important topics, decisions, or insights discussed")
    summary: str = Field(..., description="Comprehensive summary of the entire conversation")
    message_count: int = Field(..., description="Total number of messages in the conversation")
    conversation_topics: List[str] = Field(..., description="Main topics or subjects discussed")


summarization_agent = Agent(
    general_llm,
    system_prompt=(
        "You are an expert conversation analyzer and summarizer. Your role is to analyze complete conversations "
        "and provide structured, comprehensive summaries before they are archived.\n\n"
        
        "Your tasks:\n"
        "1. Identify the main intent/purpose of the conversation\n"
        "2. Extract key points, decisions, and important information\n"
        "3. Create a concise but comprehensive summary\n"
        "4. Identify all topics discussed\n"
        "5. Count total messages and identify participants\n\n"
        
        "Guidelines:\n"
        "- Focus on actionable information and decisions made\n"
        "- Preserve important context and details\n"
        "- Be objective and factual in your analysis\n"
        "- If the conversation covers multiple topics, organize them clearly\n"
        "- For technical conversations, preserve key terminology and concepts\n"
        "- If no clear intent emerges, describe it as 'General conversation/chat'\n\n"
        
        "Input format: You will receive the complete conversation history as a formatted string."
    ),
    tools=[],
    toolsets=[],
    output_type=ConversationSummary
)


