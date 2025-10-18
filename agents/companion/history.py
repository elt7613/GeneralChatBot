from typing import ClassVar
from storage.redis.agent_history.base import BaseAgentHistory

# General Agent History
class GeneralAgentHistory(BaseAgentHistory):
    agent_type: ClassVar[str] = "general_agent"


# Companion Agent History
class CompanionAgentHistory(BaseAgentHistory):
    agent_type: ClassVar[str] = "companion_agent"
    