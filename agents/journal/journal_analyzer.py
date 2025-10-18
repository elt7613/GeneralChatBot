from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal

from config.llm import journal_analyzer_llm
from states.system_state import SystemState
from pydantic_ai.usage import UsageLimits
from prompts.journal.journal_analyzer import journal_analyzer_prompt
import asyncio


class JournalAnalysis(BaseModel):
    mood: Literal["happy", "sad", "angry", "anxious", "calm", "excited", "frustrated", "hopeful", "lonely", "grateful"] = Field(..., description="Primary mood classification")
    category: Literal["general", "emotions", "relationships", "work", "health", "goals", "reflection"] = Field(..., description="Primary journal category")
    analysis: str = Field(..., description="Markdown formatted summary of the journal intent")


def format_analysis_to_markdown(data: JournalAnalysis) -> str:
    sections = ["# Journal Intent Analysis"]
    sections.append(f"- **Mood**: {data.mood}")
    sections.append(f"- **Category**: {data.category}")
    sections.append("\n## Analysis")
    sections.append(data.analysis)
    return "\n".join(sections) + "\n"


journal_agent = Agent(
    journal_analyzer_llm,
    system_prompt=journal_analyzer_prompt,
    output_type=JournalAnalysis,
    retries=5,
    output_retries=5,
)


async def journal_analyzer_agent(state: SystemState) -> Dict[str, Any]:
    journal_entry = state.get("user_input", "").get("response", "")

    prompt = f"""
    # Journal Entry:
    {journal_entry}

    Analyze the journal entry.
    """

    result = await journal_agent.run(
        prompt,
        usage_limits=UsageLimits(request_limit=None)
    )

    analysis_output = result.output
    markdown_content = format_analysis_to_markdown(analysis_output)

    # Write file asynchronously
    def write_file():
        with open(f"journal_analyzed/{state.get('workflow_id')}.md", "w") as f:
            f.write(markdown_content)
    
    await asyncio.to_thread(write_file)

    return {
        "journal_analysis": analysis_output
    }
