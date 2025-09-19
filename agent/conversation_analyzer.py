from langgraph.graph import END
from pydantic_ai import Agent
from config.llm import conversation_analyzer_llm
from pydantic import BaseModel, Field
from typing import List
from states.system_state import SystemState
from pydantic_ai.usage import UsageLimits
from .history import GeneralAgentHistory,CompanionAgentHistory
from prompts.conversation_analyzer import conversation_analyzer_promot
import os
import asyncio
import json

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

agent = Agent(
    conversation_analyzer_llm,
    system_prompt=conversation_analyzer_promot,
    output_type=ConversationAnalyzed
)

# Getting the different agnet histories dynamically
async def get_conversation_history(agent_name: str):
    """
    """
    histories = {
        "general_agent": GeneralAgentHistory,
        "companion_agent": CompanionAgentHistory
    }

    return histories[agent_name]

# Conversation Analyzer agent 
async def conversation_analyzer_agent(state: SystemState):
    """
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
        
        # Write file asynchronously
        def write_file():
            with open(f"conversation_analyzed/{state.get('workflow_id')}.json", "w") as f:
                json.dump(data.model_dump(), f, indent=2)
        
        await asyncio.to_thread(write_file)
    except Exception as e:
        raise Exception(f"Agent failed: {e}")

    return {}


