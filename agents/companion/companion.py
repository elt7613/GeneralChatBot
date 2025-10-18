from pydantic_ai import Agent
from config.llm import companion_llm
from tools.date_time import get_date, get_time
from pydantic import BaseModel,Field
from prompts.companion.companion import companion_prompt
from states.system_state import SystemState
from pydantic_ai.usage import UsageLimits
from .history import CompanionAgentHistory
from typing import Dict, Any
from utils.file_input import file_to_prompt_parts
import logging

class OutputModel(BaseModel):
    response: str = Field(..., description="The response from the agent")
    confidence: int = Field(..., description="The confidence level for the response with understanding user's input out of 5.")

agent = Agent(
    companion_llm,
    system_prompt=companion_prompt,
    retries=5,
    output_retries=5,
    tools=[
        get_date,
        get_time,
    ],
    output_type=OutputModel
)

async def companion_agent(state: SystemState) -> Dict[str,Any]:
    """
    Companion agent that provides personalized emotional support and companionship to users.
    
    This agent creates a personalized companion experience based on user-specified companion
    characteristics (name, gender) and maintains conversation history to build rapport and
    provide consistent emotional support throughout the interaction.
    
    Args:
        state (SystemState): The current system state containing:
            - workflow_id: Unique identifier for the conversation session
            - user_input: Dictionary containing:
                - response: The user's message/response
                - companion_name: Name of the companion (e.g., "Emma", "Alex")
                - companion_gender: Gender of the companion ("male", "female", etc.)
                - file: Optional file attachment (currently unused)
    
    Returns:
        dict: Dictionary containing:
            - agent_response: The companion's response to the user
            - previous_agent: The name of this agent for state tracking
    """
    # Conversation history
    history = await CompanionAgentHistory.load_or_create(state.get("workflow_id"))
    
    user_input = state.get("user_input", {})
    user_resposne = user_input.get("response", "")
    companion_name = user_input.get("companion_name", "")
    companion_gender = user_input.get("companion_gender", "")
    file = user_input.get("file", None)
    
    composed_input = f"""
        # Conversation History: 
        {history.messages}
        
        # User's Input:
        - user_response: {user_resposne}
        - companion_name: {companion_name}
        - companion_gender: {companion_gender}
    """

    # Build prompt parts with optional file attachment
    parts = await file_to_prompt_parts(composed_input, file)
    try:
        has_attachment = any(not isinstance(p, str) for p in parts)
        attachment_types = [type(p).__name__ for p in parts if not isinstance(p, str)]
        logging.info(
            "companion_agent: built prompt parts; has_attachment=%s types=%s",
            has_attachment,
            attachment_types,
        )
    except Exception:
        # Never fail because of logging
        pass

    try:
        # Use async version of the agent
        result = await agent.run(
            parts,
            usage_limits=UsageLimits(request_limit=None)
        )
    except Exception as e:
        raise Exception(f"Agent failed: {e}")

    history.messages.append({
        "user": user_input,
        "assistant": result.output.response
    })
    await history.save(workflow_id=state.get("workflow_id"), user_id=state.get("user_id"))

    return {
        "agent_response": result.output.response,
        "previous_agent": "companion_agent"
    }