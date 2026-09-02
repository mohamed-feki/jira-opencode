import os

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from graph.state import AgentState

from agents.jira_agent_vf import (
    jira_agent_vf,
    create_mcp_client,
    get_mcp_tools,
    create_subtasks,
)
from agents.analysis_agent import (
    analysis_agent,
    classify_ticket,
    decompose_ticket,
)
from agents.prompt_agent import prompt_agent
from agents.opencode_agent import opencode_agent


AUTO_SPLIT_COMPLEX_TICKETS = os.getenv(
    "AUTO_SPLIT_COMPLEX_TICKETS",
    "true",
).lower() == "true"


def classify_ticket_node(state: AgentState) -> AgentState:

    if not AUTO_SPLIT_COMPLEX_TICKETS:
        print("📊 Automatic ticket splitting is disabled; treating ticket as SIMPLE")
        return {"complexity": "SIMPLE"}

    ticket = state["ticket"]
    content = f"{ticket.get('summary', '')}\n{ticket.get('description', '')}"
    print(f"📊 Classifying ticket {ticket.get('key', 'UNKNOWN')}")
    return {"complexity": classify_ticket(content)}


async def split_ticket_node(state: AgentState) -> AgentState:

    ticket = state["ticket"]
    content = f"{ticket.get('summary', '')}\n{ticket.get('description', '')}"
    print(f"🧩 Split route selected for ticket {ticket.get('key', 'UNKNOWN')}")
    drafts = decompose_ticket(content)
    print(f"🧩 Decomposition returned {len(drafts)} drafts")
    mcp_client = await create_mcp_client()
    mcp_tools = await get_mcp_tools(mcp_client)
    print(f"🔧 MCP tools available for split: {[tool.name for tool in mcp_tools]}")
    create_tool = next(
        (
            tool
            for tool in mcp_tools
            if tool.name in ("createJiraIssue", "create_issue")
        ),
        None,
    )
    if create_tool is not None:
        print(
            f"🔧 Create tool schema: "
            f"{getattr(create_tool, 'args_schema', 'unavailable')}"
        )
    created_ids = await create_subtasks(mcp_tools, ticket["key"], drafts)
    print(
        f"✅ Parent ticket preserved: {ticket['key']}; child tickets: {created_ids}"
    )
    return {"subtasks": [{**draft, "key": key} for draft, key in zip(drafts, created_ids)]}


def route_complexity(state: AgentState) -> str:
    return "split" if state.get("complexity") == "COMPLEX" else "prompt"


# ============================================================
# WORKFLOW 1 : JIRA → ANALYSIS → PROMPT
# ============================================================

def build_prompt_graph():

    graph = StateGraph(AgentState)

    # --------------------------------------------------------
    # NODES
    # --------------------------------------------------------

    graph.add_node(
    "jira_agent_vf",
    jira_agent_vf
)

    graph.add_node(
        "analysis_agent",
        analysis_agent
    )

    graph.add_node(
        "classify_ticket",
        classify_ticket_node
    )

    graph.add_node(
        "split_ticket",
        split_ticket_node
    )

    graph.add_node(
        "prompt_agent",
        prompt_agent
    )

    # --------------------------------------------------------
    # EDGES
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "jira_agent_vf"
    )

    graph.add_edge(
        "jira_agent_vf",
        "analysis_agent"
    )

    graph.add_edge(
        "analysis_agent",
        "classify_ticket"
    )

    graph.add_conditional_edges(
        "classify_ticket",
        route_complexity,
        {"prompt": "prompt_agent", "split": "split_ticket"}
    )

    graph.add_edge("split_ticket", END)

    graph.add_edge(
        "prompt_agent",
        END
    )

    # --------------------------------------------------------
    # COMPILE
    # --------------------------------------------------------

    return graph.compile()


# ============================================================
# WORKFLOW 2 : OPENCODE
# ============================================================

def build_opencode_graph():

    graph = StateGraph(AgentState)

    # --------------------------------------------------------
    # NODE
    # --------------------------------------------------------

    graph.add_node(
        "opencode_agent",
        opencode_agent
    )

    # --------------------------------------------------------
    # EDGES
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "opencode_agent"
    )

    graph.add_edge(
        "opencode_agent",
        END
    )

    # --------------------------------------------------------
    # COMPILE
    # --------------------------------------------------------

    return graph.compile()







