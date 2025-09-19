from pydantic_ai import Agent
from config.llm import companion_llm
from tools.date_time import get_date, get_time
from pydantic import BaseModel,Field
from prompts.companion import companion_prompt
from states.system_state import SystemState
from pydantic_ai.usage import UsageLimits
from .history import CompanionAgentHistory

class OutputModel(BaseModel):
    response: str = Field(..., description="The response from the agent")
    confidence: int = Field(..., description="The confidence level for the response with understanding user's input out of 5.")

agent = Agent(
    companion_llm,
    system_prompt=companion_prompt,
    tools=[
        get_date,
        get_time,
    ],
    output_type=OutputModel
)


async def companion_agent(state: SystemState):
    """

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

    try:
        # Use async version of the agent
        result = await agent.run(
            composed_input,
            usage_limits=UsageLimits(request_limit=None)
        )
    except Exception as e:
        raise Exception(f"Agent failed: {e}")

    history.messages.append({
        "user": user_input,
        "assistant": result.output.response
    })
    await history.save(state.get("workflow_id"))

    return {
        "agent_response": result.output.response,
        "previous_agent": state.get("agent_name")
    }