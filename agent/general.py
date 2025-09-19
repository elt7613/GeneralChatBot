from pydantic_ai import Agent
from config.llm import general_llm
from tools.date_time import get_date, get_time
from pydantic import BaseModel,Field
from pydantic_ai.usage import UsageLimits
from agent.history import GeneralAgentHistory
from states.system_state import SystemState

class OutputModel(BaseModel):
    response: str = Field(..., description="The response from the agent")

agent = Agent(
    general_llm,
    system_prompt=(
        "You are a helpful assistant.\n"
    ),
    tools=[
        get_date,
        get_time,
    ],
    toolsets=[],
    output_type=OutputModel
)

async def general_agent(state: SystemState):
    # Conversation history
    history = await GeneralAgentHistory.load_or_create(state.get("workflow_id"))
    
    user_input = state.get("user_input", {})
    user_res = user_input.get("response", "")
    
    composed_input = f"Conversation so far:\n{history.messages}\n\nUser: {user_res}"

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