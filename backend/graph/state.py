from typing import TypedDict, Optional, Dict, Any, Annotated

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):

    # ========================================================
    # USER
    # ========================================================

    user_request: str


    # ========================================================
    # MESSAGES / LLM
    # ========================================================

    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]


    # ========================================================
    # JIRA
    # ========================================================

    issue_key: str

    ticket: Dict[str, Any]


    # ========================================================
    # ANALYSIS
    # ========================================================

    analysis: str

    complexity: str

    subtasks: list[Dict[str, Any]]


    # ========================================================
    # PROMPT
    # ========================================================

    coding_instruction: str

    prompt_file: str


    # ========================================================
    # OPENCODE
    # ========================================================

    opencode_result: str

    opencode_return_code: Optional[int]




    # ========================================================
    # ERROR
    # ========================================================

    error: Optional[str]