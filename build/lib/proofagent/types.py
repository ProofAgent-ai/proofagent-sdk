from typing import TypedDict, NotRequired, Any


class LogEntry(TypedDict):
    turn_index: int
    user_message: str
    agent_answer: str
    context: NotRequired[dict[str, Any]]


class ToolConfig(TypedDict, total=False):
    id: str
    name: str
    description: str


class InternalAgentConfig(TypedDict):
    id: str
    role: str
    description: str
