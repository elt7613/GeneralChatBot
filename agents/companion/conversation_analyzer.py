from langgraph.graph import END
from pydantic_ai import Agent
from config.llm import conversation_analyzer_llm
from pydantic import BaseModel, Field
from typing import List,Dict,Any
from states.system_state import SystemState
from pydantic_ai.usage import UsageLimits
from .history import GeneralAgentHistory,CompanionAgentHistory
from prompts.companion.conversation_analyzer import conversation_analyzer_promot
import os
import asyncio

class SessionMetadata(BaseModel):
    companion_name: str = Field(..., description="Companion name used in the session")
    companion_gender: str = Field(..., description="Gender specified for the companion")
    interaction_type: str = Field(..., description="Primary classification of the interaction type")

class IntentAnalysis(BaseModel):
    primary_intent: str = Field(..., description="Main purpose or goal the user had for the conversation")
    secondary_intents: List[str] = Field(..., description="List of underlying needs or secondary purposes")
    intent_fulfillment: str = Field(..., description="Scale 1-10 with reasoning on how well intents were fulfilled")
    evolving_needs: str = Field(..., description="How the user's needs or intents changed during conversation")

class EmotionalProfile(BaseModel):
    initial_state: str = Field(..., description="User's emotional condition at the start of conversation")
    emotional_journey: List[str] = Field(..., description="Key emotional transitions throughout the conversation")
    final_state: str = Field(..., description="User's emotional condition at the end of conversation")
    emotional_needs: List[str] = Field(..., description="Types of emotional support or validation the user was seeking")
    triggers: List[str] = Field(..., description="Topics or responses that caused significant emotional reactions")

class RelationshipDynamics(BaseModel):
    interaction_style: str = Field(..., description="Communication pattern observed (formal, casual, intimate, etc.)")
    trust_indicators: List[str] = Field(..., description="Signs of user comfort, openness, and trust")
    companion_performance: str = Field(..., description="Assessment of how effectively the AI companion performed")
    attachment_signals: str = Field(..., description="Indicators of relationship development or bonding")

class ContextualInsights(BaseModel):
    session_quality: str = Field(..., description="Overall satisfaction and quality indicators")
    user_engagement: str = Field(..., description="Level of active participation and investment from user")
    conversation_flow: str = Field(..., description="Assessment of natural vs forced conversation dynamics")
    preferred_topics: List[str] = Field(..., description="Subjects the user actively engaged with or showed interest in")
    avoided_topics: List[str] = Field(..., description="Subjects the user deflected, avoided, or showed discomfort with")

class Recommendations(BaseModel):
    companion_improvements: List[str] = Field(..., description="Suggestions for better companion interaction in future")
    user_patterns: str = Field(..., description="Behavioral patterns and preferences observed")
    future_session_guidance: str = Field(..., description="Recommendations on how to better serve this user")

class ConversationAnalyzed(BaseModel):
    session_metadata: SessionMetadata = Field(..., description="Basic session information and context")
    intent_analysis: IntentAnalysis = Field(..., description="Analysis of user intents and goal fulfillment")
    emotional_profile: EmotionalProfile = Field(..., description="User's emotional journey and needs")
    relationship_dynamics: RelationshipDynamics = Field(..., description="Analysis of interaction patterns and rapport")
    contextual_insights: ContextualInsights = Field(..., description="Session quality and engagement insights")
    recommendations: Recommendations = Field(..., description="Actionable insights for future improvements")

def format_list_section(title: str, items: List[str]) -> str:
    lines = [f"- **{title}**"]
    lines.extend(f"  - {item}" for item in items)
    return "\n".join(lines)

def format_analysis_to_markdown(data: ConversationAnalyzed) -> str:
    sections = ["# Conversation Analysis"]

    sections.append("## Session Metadata")
    sections.append(f"- **Companion Name**: {data.session_metadata.companion_name}")
    sections.append(f"- **Companion Gender**: {data.session_metadata.companion_gender}")
    sections.append(f"- **Interaction Type**: {data.session_metadata.interaction_type}")

    sections.append("\n## Intent Analysis")
    sections.append(f"- **Primary Intent**: {data.intent_analysis.primary_intent}")
    sections.append(format_list_section("Secondary Intents", data.intent_analysis.secondary_intents))
    sections.append(f"- **Intent Fulfillment**: {data.intent_analysis.intent_fulfillment}")
    sections.append(f"- **Evolving Needs**: {data.intent_analysis.evolving_needs}")

    sections.append("\n## Emotional Profile")
    sections.append(f"- **Initial State**: {data.emotional_profile.initial_state}")
    sections.append(format_list_section("Emotional Journey", data.emotional_profile.emotional_journey))
    sections.append(f"- **Final State**: {data.emotional_profile.final_state}")
    sections.append(format_list_section("Emotional Needs", data.emotional_profile.emotional_needs))
    sections.append(format_list_section("Triggers", data.emotional_profile.triggers))

    sections.append("\n## Relationship Dynamics")
    sections.append(f"- **Interaction Style**: {data.relationship_dynamics.interaction_style}")
    sections.append(format_list_section("Trust Indicators", data.relationship_dynamics.trust_indicators))
    sections.append(f"- **Companion Performance**: {data.relationship_dynamics.companion_performance}")
    sections.append(f"- **Attachment Signals**: {data.relationship_dynamics.attachment_signals}")

    sections.append("\n## Contextual Insights")
    sections.append(f"- **Session Quality**: {data.contextual_insights.session_quality}")
    sections.append(f"- **User Engagement**: {data.contextual_insights.user_engagement}")
    sections.append(f"- **Conversation Flow**: {data.contextual_insights.conversation_flow}")
    sections.append(format_list_section("Preferred Topics", data.contextual_insights.preferred_topics))
    sections.append(format_list_section("Avoided Topics", data.contextual_insights.avoided_topics))

    sections.append("\n## Recommendations")
    sections.append(format_list_section("Companion Improvements", data.recommendations.companion_improvements))
    sections.append(f"- **User Patterns**: {data.recommendations.user_patterns}")
    sections.append(f"- **Future Session Guidance**: {data.recommendations.future_session_guidance}")

    return "\n".join(sections) + "\n"

agent = Agent(
    conversation_analyzer_llm,
    system_prompt=conversation_analyzer_promot,
    output_type=ConversationAnalyzed,
    retries=5,
    output_retries=5,
)

# Getting the different agnet histories dynamically
async def get_conversation_history(agent_name: str):
    """
    Retrieves the appropriate conversation history class based on the agent name.
    
    This function maps agent names to their corresponding history management classes,
    allowing the conversation analyzer to access the correct conversation history
    for analysis regardless of which agent was previously active.
    
    Args:
        agent_name (str): The name of the agent whose history is needed.
                         Must be one of: "general_agent", "companion_agent"
    
    Returns:
        Type[Union[GeneralAgentHistory, CompanionAgentHistory]]: The history class
        corresponding to the specified agent name.
    """
    histories = {
        "general_agent": GeneralAgentHistory,
        "companion_agent": CompanionAgentHistory
    }

    return histories[agent_name]

# Conversation Analyzer agent 
async def conversation_analyzer_agent(state: SystemState) -> Dict[str,Any]:
    """
    Analyzes completed conversations to provide comprehensive insights and recommendations.
    
    This agent performs deep analysis of conversation sessions between users and other agents
    (general_agent or companion_agent), generating detailed psychological, emotional, and
    behavioral insights. The analysis includes intent fulfillment, emotional journey,
    relationship dynamics, and actionable recommendations for improvement.
    
    Args:
        state (SystemState): The current system state containing:
            - previous_agent: The name of the agent whose conversation to analyze
            - workflow_id: Unique identifier for the conversation session
    
    Returns:
        dict: Empty dictionary (analysis results are saved to file)
    """
    # Conversation history
    agent_history = await get_conversation_history(state.get("previous_agent"))
    history = await agent_history.load_or_create(state.get("workflow_id"))
    
    prompt = f"""
    # Conversation History:
    {history.messages}

    Analyze the conversation.
    """

    try:
        # Use async version of the agent
        result = await agent.run(
            prompt,
            usage_limits=UsageLimits(request_limit=None)
        )

        # Ensure directory exists (async)
        await asyncio.to_thread(os.makedirs, "conversation_analyzed", exist_ok=True)

        data = result.output

        markdown_content = format_analysis_to_markdown(data)

        # Write file asynchronously
        def write_file():
            with open(f"conversation_analyzed/{state.get('workflow_id')}.md", "w") as f:
                f.write(markdown_content)
        
        await asyncio.to_thread(write_file)
        
        return {
            "conversation_analyzed": markdown_content
        }
    except Exception as e:
        raise Exception(f"Agent failed: {e}")



