"""Current-task authority; not an operating-system security boundary."""
from .policy import CURRENT_POLICY,CurrentTaskPolicy,PolicyDecision,require_research_action,locked_research,FutureResearchAuthorization
from .broker import ActionBroker,ActionRequest,FixtureDeclaration
