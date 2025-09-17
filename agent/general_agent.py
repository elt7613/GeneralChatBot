from pydantic_ai import Agent
from config.llm import general_llm
from tools.date_time import get_date, get_time
from pydantic import BaseModel,Field

class OutputModel(BaseModel):
    response: str = Field(..., description="The response from the agent")

general_agent = Agent(
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
