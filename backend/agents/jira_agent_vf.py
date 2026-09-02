# ============================================================
# JIRA AI AGENT — MCP VERSION
#
# Architecture:
#
# FastAPI
#    ↓
# jira_agent()
#    ↓
# LangGraph
#    ↓
# Ollama
#    ↓
# MCP Tool : getJiraIssue
#    ↓
# Atlassian Rovo MCP
#    ↓
# Jira
#
# ============================================================


# ============================================================
# 1. IMPORTS
# ============================================================

import os
import json
import base64

from dotenv import load_dotenv

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from langchain_ollama import ChatOllama

from langgraph.graph import (
    StateGraph,
    END,
)

from langgraph.prebuilt import ToolNode

from langchain_mcp_adapters.client import (
    MultiServerMCPClient
)

from graph.state import AgentState


# ============================================================
# 2. ENVIRONMENT
# ============================================================

load_dotenv(
    override=True
)

print("✅ .env chargé")


# ============================================================
# 3. OLLAMA CONFIGURATION
# ============================================================

OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY"
)

if not OLLAMA_API_KEY:

    raise ValueError(
        "❌ OLLAMA_API_KEY manquante."
    )


OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma4:31b-cloud"
)


# ============================================================
# 4. ATLASSIAN / JIRA CONFIGURATION
# ============================================================

JIRA_EMAIL = os.getenv(
    "JIRA_EMAIL"
)

ROVO_MCP_API_TOKEN = os.getenv(
    "ROVO_MCP_API_TOKEN"
)

JIRA_CLOUD_ID = os.getenv(
    "JIRA_CLOUD_ID"
)

JIRA_URL = os.getenv(
    "JIRA_URL"
)

if not JIRA_EMAIL:

    raise ValueError(
        "❌ JIRA_EMAIL manquant."
    )


if not ROVO_MCP_API_TOKEN:

    raise ValueError(
        "❌ ROVO_MCP_API_TOKEN manquant."
    )


if not JIRA_CLOUD_ID:

    raise ValueError(
        "❌ JIRA_CLOUD_ID manquant."
    )


print(
    "✅ Jira Cloud ID chargé :",
    JIRA_CLOUD_ID
)


# ============================================================
# 5. OLLAMA
# ============================================================

llm = ChatOllama(

    model=OLLAMA_MODEL,

    base_url="https://ollama.com",

    client_kwargs={

        "headers": {

            "Authorization":
                f"Bearer {OLLAMA_API_KEY}"

        }

    },

    temperature=0,

)


print(
    f"✅ Ollama configuré : {OLLAMA_MODEL}"
)


# ============================================================
# 6. TEST OLLAMA
# ============================================================

try:

    llm.invoke(
        "Réponds uniquement : connexion OK"
    )

    print(
        "✅ Connexion réussie à Ollama Cloud"
    )

except Exception as e:

    raise RuntimeError(
        f"❌ Erreur Ollama : {e}"
    )


# ============================================================
# 7. FORMAT TICKET
# ============================================================

def format_ticket(
    data: dict
) -> dict:

    """
    Transforme la réponse brute de getJiraIssue
    en ticket simplifié utilisable par les autres agents.
    """

    while isinstance(data, dict):

        if "fields" in data or "key" in data:
            break

        nested_data = next(
            (
                data.get(name)
                for name in (
                    "issue",
                    "result",
                    "data",
                    "structuredContent",
                )
                if isinstance(data.get(name), dict)
            ),
            None,
        )

        if nested_data is None:
            break

        data = nested_data

    fields = data.get(
        "fields"
    )

    if not isinstance(fields, dict):
        fields = data


    status = fields.get("status") or fields.get("jiraStatus") or {}


    issue_type = fields.get("issuetype") or fields.get("issueType") or {}


    priority = fields.get(
        "priority",
        {}
    )


    project = fields.get(
        "project",
        {}
    )


    reporter = fields.get(
        "reporter",
        {}
    )


    assignee = fields.get(
        "assignee"
    )


    return {

        "key":
            data.get(
                "key"
            ),

        "summary":
            fields.get(
                "summary"
            ),

        "description":
            fields.get(
                "description"
            ),

        "status":
            status.get(
                "name"
            ) if isinstance(status, dict)
            else None,

        "issue_type":
            issue_type.get(
                "name"
            ) if isinstance(issue_type, dict)
            else None,

        "priority":
            priority.get(
                "name"
            ) if isinstance(priority, dict)
            else None,

        "project":
            project.get(
                "name"
            ) if isinstance(project, dict)
            else None,

        "project_key":
            project.get(
                "key"
            ) if isinstance(project, dict)
            else None,

        "reporter":
            reporter.get(
                "displayName"
            ) if isinstance(reporter, dict)
            else None,

        "assignee":
            assignee.get(
                "displayName"
            ) if isinstance(assignee, dict)
            else None,

        "created": fields.get("created") or fields.get("createdAt"),

        "updated": fields.get("updated") or fields.get("updatedAt"),

    }


# ============================================================
# 8. MCP CLIENT
# ============================================================

async def create_mcp_client():

    print(
        "\n🔌 Connexion au serveur Atlassian MCP..."
    )


    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    credentials = (
        f"{JIRA_EMAIL}:{ROVO_MCP_API_TOKEN}"
    )


    encoded_credentials = (
        base64.b64encode(
            credentials.encode("utf-8")
        ).decode("utf-8")
    )


    # --------------------------------------------------------
    # MCP Client
    # --------------------------------------------------------

    mcp_client = MultiServerMCPClient({

        "atlassian": {

            "transport":
                "streamable_http",

            "url":
                os.getenv(
                    "ATLASSIAN_MCP_URL",
                    "https://mcp.atlassian.com/v1/mcp",
                ),

            "headers": {

                "Authorization":
                    f"Basic {encoded_credentials}"

            }

        }

    })


    print(
        "✅ Client Atlassian MCP créé"
    )


    return mcp_client


# ============================================================
# 9. RÉCUPÉRER LES TOOLS MCP
# ============================================================

async def get_mcp_tools(
    mcp_client
):

    print(
        "\n🔧 Récupération des Tools MCP..."
    )


    try:

        mcp_tools = await (
            mcp_client.get_tools()
        )

    except Exception as e:

        raise RuntimeError(
            f"""
❌ Impossible de récupérer les Tools Atlassian MCP.

Erreur :

{e}
"""
        )


    print(
        "\n🔧 Tools Atlassian MCP disponibles :"
    )


    for tool in mcp_tools:

        print(
            f"   -> {tool.name}"
        )


    return mcp_tools


async def fetch_jira_issue_mcp(
    mcp_tools,
    issue_key: str
) -> dict:

    tool = next(
        (
            tool
            for tool in mcp_tools
            if tool.name == "getJiraIssue"
        ),
        None,
    )

    if tool is None:
        raise RuntimeError(
            "❌ Le Tool MCP getJiraIssue est indisponible."
        )

    content = await tool.ainvoke({
        "cloudId": JIRA_CLOUD_ID,
        "issueIdOrKey": issue_key,
        "responseContentFormat": "markdown",
    })

    if isinstance(content, list):
        content = next(
            (
                item.get("text")
                for item in content
                if isinstance(item, dict) and item.get("text")
            ),
            content,
        )

    if isinstance(content, str):
        print(
            f"📥 Jira MCP response before parsing: length={len(content)}, "
            f"preview={content[:300]!r}"
        )
        try:
            content = json.loads(content)
        except json.JSONDecodeError as exc:
            print(
                f"❌ JSON parse failed in fetch_jira_issue_mcp: line={exc.lineno}, "
                f"column={exc.colno}, position={exc.pos}, message={exc.msg}"
            )
            raise RuntimeError(
                "❌ Jira MCP returned invalid JSON while reading the ticket."
            ) from exc

    if isinstance(content, dict) and content.get("error"):
        raise RuntimeError(
            f"❌ Atlassian MCP a refusé la requête : {content.get('message')}"
        )

    if not isinstance(content, dict):
        raise RuntimeError(
            "❌ Réponse MCP Jira invalide."
        )

    return content


async def resolve_subtask_issue_type(
    mcp_tools,
    project_key: str,
) -> str:

    metadata_tool = next(
        (
            tool
            for tool in mcp_tools
            if tool.name == "getJiraProjectIssueTypesMetadata"
        ),
        None,
    )
    if metadata_tool is None:
        raise RuntimeError(
            "❌ MCP ne fournit pas getJiraProjectIssueTypesMetadata; "
            "impossible de déterminer le type de sous-tâche du projet."
        )

    try:
        response = await metadata_tool.ainvoke({
            "cloudId": JIRA_CLOUD_ID,
            "projectIdOrKey": project_key,
        })
    except Exception as exc:
        raise RuntimeError(
            f"❌ Impossible de récupérer les types Jira du projet {project_key}: {exc}"
        ) from exc

    if isinstance(response, list):
        response = next(
            (
                item.get("text")
                for item in response
                if isinstance(item, dict) and item.get("text")
            ),
            response,
        )
    if isinstance(response, str):
        if response.startswith("MCP error"):
            raise RuntimeError(
                f"❌ Jira issue-type metadata request was rejected: {response}"
            )
        try:
            response = json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"❌ Réponse invalide des métadonnées de types Jira: {response[:300]!r}"
            ) from exc

    if isinstance(response, dict):
        response = response.get("result") or response.get("data") or response
    issue_types = response.get("issueTypes", []) if isinstance(response, dict) else response
    if not isinstance(issue_types, list):
        issue_types = []

    for issue_type in issue_types:
        if not isinstance(issue_type, dict):
            continue
        name = issue_type.get("name")
        normalized_name = str(name or "").strip().lower().replace("-", " ")
        if (
            issue_type.get("subtask") is True
            or issue_type.get("isSubtask") is True
            or issue_type.get("isSubTask") is True
            or normalized_name in ("subtask", "sub task")
        ):
            if name:
                return str(name)

    available = [
        issue_type.get("name")
        for issue_type in issue_types
        if isinstance(issue_type, dict) and issue_type.get("name")
    ]
    raise RuntimeError(
        f"❌ Aucun type de sous-tâche disponible dans le projet {project_key}. "
        f"Types disponibles: {available}"
    )


async def create_subtasks(
    mcp_tools,
    parent_ticket_id: str,
    subtasks: list[dict]
) -> list[str]:

    tool = next(
        (
            tool
            for tool in mcp_tools
            if tool.name in ("createJiraIssue", "create_issue")
        ),
        None,
    )
    if tool is None:
        raise RuntimeError(
            "MCP_WRITE_TOOLS_UNAVAILABLE: Atlassian MCP did not expose "
            "createJiraIssue. Enable Jira write access for this connection."
        )

    project_key = parent_ticket_id.split("-", 1)[0]
    issue_type_name = await resolve_subtask_issue_type(
        mcp_tools,
        project_key,
    )
    print(
        f"🔧 Jira subtask issue type for {project_key}: {issue_type_name}"
    )
    created_ids = []
    for subtask in subtasks:
        payload = {
            "cloudId": JIRA_CLOUD_ID,
            "projectKey": project_key,
            "issueTypeName": issue_type_name,
            "summary": subtask["title"],
            "description": subtask["description"],
            "parent": parent_ticket_id,
            "additional_fields": {
                "labels": subtask.get("labels", []),
            },
            "contentFormat": "markdown",
        }

        print(
            f"📤 Calling MCP tool {tool.name} for parent {parent_ticket_id}; "
            f"payload fields={list(payload)}"
        )
        try:
            result = await tool.ainvoke(payload)
        except Exception as exc:
            print(
                f"❌ MCP create call failed for {subtask['title']}: "
                f"{type(exc).__name__}: {exc}"
            )
            raise RuntimeError(
                f"❌ MCP createJiraIssue failed for subtask "
                f"'{subtask['title']}': {exc}"
            ) from exc

        if isinstance(result, list):
            result = next(
                (
                    item.get("text")
                    for item in result
                    if isinstance(item, dict) and item.get("text")
                ),
                result,
            )

        if isinstance(result, str):
            print(
                f"📤 createJiraIssue response before parsing: length={len(result)}, "
                f"preview={result[:300]!r}"
            )
            if result.startswith("MCP error"):
                raise RuntimeError(
                    f"❌ MCP createJiraIssue rejected the request: {result}"
                )
            try:
                result = json.loads(result)
            except json.JSONDecodeError as exc:
                print(
                    f"❌ JSON parse failed in create_subtasks: line={exc.lineno}, "
                    f"column={exc.colno}, position={exc.pos}, message={exc.msg}"
                )
                raise RuntimeError(
                    "❌ Jira MCP returned invalid JSON while creating a subtask."
                ) from exc

        if isinstance(result, dict):
            if result.get("error"):
                raise RuntimeError(
                    f"❌ MCP createJiraIssue returned an error: "
                    f"{result.get('message') or result.get('error')}"
                )
            result = result.get("issue") or result.get("result") or result

        if not isinstance(result, dict):
            raise RuntimeError(
                f"❌ Réponse invalide de createJiraIssue pour : {subtask['title']}"
            )

        created_id = result.get("key") or result.get("id")
        if not created_id:
            raise RuntimeError(
                f"❌ createJiraIssue n'a retourné aucun identifiant pour : {subtask['title']}"
            )

        print(
            f"✅ Sous-tâche créée sous {parent_ticket_id} : {created_id}"
        )
        created_ids.append(created_id)
    return created_ids


async def close_ticket(
    mcp_tools,
    ticket_id: str,
    reason: str
) -> None:

    if not any(tool.name == "transitionJiraIssue" for tool in mcp_tools):
        raise RuntimeError(
            "❌ MCP ne fournit pas transitionJiraIssue. Activez les outils d'écriture Jira."
        )

    raise RuntimeError(
        "❌ MCP fournit seulement la lecture des transitions; aucune transition d'écriture n'est disponible."
    )


# ============================================================
# 10. JIRA AGENT
# ============================================================

async def jira_agent_vf(
    state: AgentState
) -> dict:

    """
    Récupère un ticket Jira via Atlassian MCP.

    Retourne :

    {
        "issue_key": "KAN-1",
        "ticket": {...}
    }
    """

    # ========================================================
    # RÉCUPÉRER ISSUE KEY DEPUIS LE STATE
    # ========================================================

    issue_key = state["issue_key"]

    # ========================================================
    # NORMALISATION
    # ========================================================

    issue_key = (
        issue_key
        .strip()
        .upper()
    )

    if not issue_key:

        raise ValueError(
            "❌ Issue key manquante."
        )


    print(
        "\n"
        + "=" * 60
    )

    print(
        "🔎 JIRA AGENT — MCP"
    )

    print(
        "=" * 60
    )

    print(
        f"Ticket : {issue_key}"
    )


    # ========================================================
    # MCP CLIENT
    # ========================================================

    mcp_client = await create_mcp_client()


    # ========================================================
    # MCP TOOLS
    # ========================================================

    mcp_tools = await get_mcp_tools(
        mcp_client
    )

    raw_ticket = await fetch_jira_issue_mcp(
        mcp_tools,
        issue_key
    )

    ticket = format_ticket(
        raw_ticket
    )

    if not ticket.get("key"):
        raise RuntimeError(
            "❌ Le Tool MCP n'a pas retourné les données du ticket."
        )

    print("Le Tool MCP a pu retourné les données du ticket. //////////////////////////////")
    return {
        "issue_key": issue_key,
        "ticket": ticket
    }


    # ========================================================
    # LLM + TOOLS
    # ========================================================

    print(
        "\n🧠 Connexion des Tools au LLM..."
    )


    llm_with_tools = llm.bind_tools(
        mcp_tools
    )


    print(
        "✅ Ollama peut utiliser les Tools MCP."
    )


    # ========================================================
    # AGENT NODE
    # ========================================================

    def agent_node(
        state: AgentState
    ):

        print(
            "\n"
            + "-" * 60
        )

        print(
            "🤖 AI AGENT NODE"
        )

        print(
            "-" * 60
        )


        response = (
            llm_with_tools.invoke(
                state["messages"]
            )
        )


        # ----------------------------------------------------
        # DEBUG TOOL CALL
        # ----------------------------------------------------

        if response.tool_calls:

            print(
                f"\n🔧 Le LLM demande "
                f"{len(response.tool_calls)} Tool(s)"
            )


            for tool_call in response.tool_calls:

                print(
                    f"\n   Tool : "
                    f"{tool_call['name']}"
                )

                print(
                    f"   Args : "
                    f"{tool_call['args']}"
                )


        else:

            print(
                "\n💬 Le LLM répond directement."
            )


        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        #
        # On ne cherche PAS encore le ToolMessage ici.
        #
        # Le ToolNode va d'abord exécuter getJiraIssue.
        #
        # Ensuite LangGraph reviendra dans agent_node.
        #
        # ----------------------------------------------------

        return {

            "messages": [
                response
            ]

        }


    # ========================================================
    # TOOL NODE
    # ========================================================

    tool_node = ToolNode(
        mcp_tools
    )


    # ========================================================
    # DECISION
    # ========================================================

    def should_continue(
        state: AgentState
    ):

        last_message = (
            state["messages"][-1]
        )


        if last_message.tool_calls:

            print(
                "\n🔀 Décision : use_tool"
            )

            return "use_tool"


        print(
            "\n🔀 Décision : END"
        )

        return END


    # ========================================================
    # BUILD GRAPH
    # ========================================================

    graph = StateGraph(
        AgentState
    )


    graph.add_node(
        "agent",
        agent_node
    )


    graph.add_node(
        "use_tool",
        tool_node
    )


    graph.set_entry_point(
        "agent"
    )


    graph.add_conditional_edges(

        "agent",

        should_continue,

        {

            "use_tool":
                "use_tool",

            END:
                END,

        }

    )


    graph.add_edge(

        "use_tool",

        "agent"

    )


    app = graph.compile()


    print(
        "\n✅ LangGraph compilé !"
    )


    # ========================================================
    # SYSTEM MESSAGE
    # ========================================================

    messages = [

        SystemMessage(

            content=f"""

Tu es un AI Agent spécialisé dans Jira.

Tu peux utiliser les Tools Atlassian MCP.

Pour récupérer un ticket Jira :

1. Utilise obligatoirement le Tool getJiraIssue.
2. Le ticket demandé est : {issue_key}
3. Pour cloudId utilise obligatoirement :

{JIRA_CLOUD_ID}

4. Ne mets jamais "your-cloud-id".
5. Récupère les données du ticket.
6. Ne prétends jamais avoir récupéré
   un ticket si le Tool MCP n'a pas retourné
   les données.

"""

        ),

        HumanMessage(

            content=
                f"Récupère le ticket {issue_key}"

        )

    ]


    # ========================================================
    # EXECUTION LANGGRAPH
    # ========================================================

    result = await app.ainvoke({

        "messages":
            messages,

        "issue_key":
            issue_key

    })


    # ========================================================
    # RÉCUPÉRER LE TOOL MESSAGE
    # ========================================================

    ticket = None


    print(
        "\n📦 Analyse des messages LangGraph..."
    )


    for message in result["messages"]:

        print(
            "\nTYPE :",
            type(message)
        )


        # ----------------------------------------------------
        # TOOL MESSAGE
        # ----------------------------------------------------

        if message.type == "tool":

            print(
                "🔧 ToolMessage détecté."
            )


            try:

                tool_content = (
                    message.content
                )


                # ------------------------------------------------
                # MCP retourne une liste
                # ------------------------------------------------

                if isinstance(
                    tool_content,
                    list
                ):

                    json_text = (
                        tool_content[0]["text"]
                    )

                else:

                    json_text = (
                        tool_content
                    )


                # ------------------------------------------------
                # JSON string → dict
                # ------------------------------------------------

                raw_ticket = json.loads(
                    json_text
                )


                # ------------------------------------------------
                # FORMAT
                # ------------------------------------------------

                ticket = format_ticket(
                    raw_ticket
                )


                print(
                    "\n🎫 TICKET FORMATÉ :"
                )

                print(
                    ticket
                )


                break


            except Exception as e:

                print(
                    "\n❌ Erreur format_ticket :"
                )

                print(
                    e
                )


    # ========================================================
    # VALIDATION
    # ========================================================

    if not ticket:

        raise RuntimeError(
            "❌ Le ticket Jira n'a pas pu être récupéré."
        )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "issue_key":
            issue_key,

        "ticket":
            ticket

    }
