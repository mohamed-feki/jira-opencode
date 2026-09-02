# ============================================================
# ANALYSIS AGENT
#
# Architecture:
#
# Jira Agent
#      ↓
# Ticket JSON
#      ↓
# Analysis Agent
#      ↓
# Load Analysis Skill
#      ↓
# Ollama / Gemma
#      ↓
# Markdown Analysis
#
# Responsibility:
# - récupérer le ticket depuis AgentState
# - charger le Skill d'analyse
# - envoyer ticket + skill à Ollama
# - récupérer l'analyse Markdown
# - retourner l'analyse dans AgentState
#
# The analysis_agent does NOT:
# - écrire du code
# - modifier le projet
# - générer le prompt OpenCode
# ============================================================


# ============================================================
# 1. IMPORTS
# ============================================================

import os
import json
from typing import Literal

from dotenv import load_dotenv

from langchain_ollama import ChatOllama

from graph.state import AgentState


# ============================================================
# 2. ENVIRONMENT
# ============================================================

load_dotenv(
    override=True
)

print(
    "✅ .env chargé pour Analysis Agent"
)


# ============================================================
# 3. OLLAMA CONFIGURATION
# ============================================================

OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY"
)


if not OLLAMA_API_KEY:

    raise ValueError(
        "❌ OLLAMA_API_KEY n'est pas défini."
    )


OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma4:31b-cloud"
)


# ============================================================
# 4. OLLAMA CLIENT
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
    f"✅ Analysis Agent connecté à Ollama : "
    f"{OLLAMA_MODEL}"
)


# ============================================================
# 5. LOAD ANALYSIS SKILL
# ============================================================

def load_analysis_skill() -> str:

    """
    Charge le Skill utilisé par l'Analysis Agent.

    Structure attendue :

    backend/
    │
    ├── agents/
    │   └── analysis_agent.py
    │
    └── skills/
        └── analysis_agent/
            └── skill.md
    """

    # --------------------------------------------------------
    # Répertoire backend
    # --------------------------------------------------------

    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )


    # --------------------------------------------------------
    # Chemin du Skill
    # --------------------------------------------------------

    skill_path = os.path.join(

        base_dir,

        "skills",

        "analysis_agent",

        "skill.md"

    )


    # --------------------------------------------------------
    # Vérification
    # --------------------------------------------------------

    if not os.path.isfile(
        skill_path
    ):

        raise FileNotFoundError(

            f"""
❌ Skill d'analyse introuvable.

Chemin recherché :

{skill_path}

Vérifie que le fichier existe :

skills/
└── analysis_agent/
    └── skill.md
"""

        )


    # --------------------------------------------------------
    # Lecture
    # --------------------------------------------------------

    try:

        with open(

            skill_path,

            "r",

            encoding="utf-8"

        ) as file:

            skill = file.read()

    except Exception as e:

        raise RuntimeError(

            f"""
❌ Impossible de lire le Skill d'analyse.

Fichier :
{skill_path}

Erreur :
{e}
"""

        )


    # --------------------------------------------------------
    # Vérification contenu
    # --------------------------------------------------------

    if not skill.strip():

        raise RuntimeError(

            f"""
❌ Le Skill d'analyse est vide.

Fichier :
{skill_path}
"""

        )


    print(
        "📚 Analysis Skill chargé."
    )


    return skill


# ============================================================
# 6. ANALYSIS AGENT
# ============================================================

def classify_ticket(
    ticket_content: str
) -> Literal["SIMPLE", "COMPLEX"]:

    response = llm.invoke(f"""
Classify this Jira ticket as exactly SIMPLE or COMPLEX.
Use COMPLEX when it requires multiple independent components or subsystems.
Use SIMPLE for one narrow, well-scoped implementation task.
Return only JSON: {{"classification": "SIMPLE"}}

JIRA TICKET:
{ticket_content}
""")

    try:
        value = json.loads(str(response.content).strip()).get("classification")
        if value in ("SIMPLE", "COMPLEX"):
            print(f"📊 Ticket complexity: {value}")
            return value
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    fallback_terms = (
        "application", "platform", "system", "end-to-end",
        "architecture", "frontend", "backend", "database",
    )
    value = "COMPLEX" if sum(term in ticket_content.lower() for term in fallback_terms) >= 2 else "SIMPLE"
    print(f"📊 Ticket complexity (fallback): {value}")
    return value


def decompose_ticket(
    ticket_content: str
) -> list[dict]:

    print("🧩 Starting ticket decomposition with Ollama")
    response = llm.invoke(f"""
Decompose this Jira ticket into at least 3 independent implementation subtasks.
Return only a JSON array. Each item must contain title, description, and labels.
Descriptions must be actionable and independently implementable.

JIRA TICKET:
{ticket_content}
""")

    text = str(response.content).strip().removeprefix("```").removeprefix("json").removesuffix("```").strip()
    print(
        f"🧩 Ollama decomposition response: type={type(response.content).__name__}, "
        f"length={len(text)}, preview={text[:300]!r}"
    )
    try:
        drafts = json.loads(text)
    except json.JSONDecodeError as exc:
        print(
            f"❌ JSON parse failed in decompose_ticket: line={exc.lineno}, "
            f"column={exc.colno}, position={exc.pos}, message={exc.msg}"
        )
        raise RuntimeError(
            "❌ Ollama returned invalid JSON while decomposing the ticket."
        ) from exc
    if not isinstance(drafts, list) or len(drafts) < 3:
        raise RuntimeError("❌ La décomposition doit produire au moins 3 sous-tâches.")

    result = [
        {
            "title": str(item["title"]).strip(),
            "description": str(item["description"]).strip(),
            "labels": item.get("labels", []),
        }
        for item in drafts
    ]
    print(f"🧩 Subtasks generated: {len(result)}")
    return result

def analysis_agent(
    state: AgentState
) -> AgentState:

    """
    LangGraph Node 2.

    Entrée :

        state["ticket"]

    Traitement :

        Ticket
           +
        Analysis Skill
           ↓
        Ollama / Gemma
           ↓
        Markdown Analysis

    Sortie :

        {
            "analysis": "Markdown ..."
        }
    """

    # ========================================================
    # 6.1 RÉCUPÉRER LE TICKET
    # ========================================================

    ticket = state.get(
        "ticket"
    )


    if not ticket:

        raise ValueError(
            "❌ Aucun ticket Jira dans le State."
        )


    # ========================================================
    # 6.2 LOG
    # ========================================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "🧠 AGENT 2 — ANALYSIS"
    )

    print(
        "=" * 60
    )

    print(
        f"🎫 Ticket : "
        f"{ticket.get('key', 'UNKNOWN')}"
    )

    print(
        f"📝 Summary : "
        f"{ticket.get('summary', 'UNKNOWN')}"
    )


    # ========================================================
    # 6.3 CHARGER LE SKILL
    # ========================================================

    skill = load_analysis_skill()


    # ========================================================
    # 6.4 EXTRAIRE LES INFORMATIONS DU TICKET
    # ========================================================

    issue_key = ticket.get(
        "key",
        ""
    )

    summary = ticket.get(
        "summary",
        ""
    )

    description = ticket.get(
        "description",
        ""
    )

    status = ticket.get(
        "status",
        ""
    )

    issue_type = ticket.get(
        "issue_type",
        ""
    )

    priority = ticket.get(
        "priority",
        ""
    )

    project = ticket.get(
        "project",
        ""
    )

    project_key = ticket.get(
        "project_key",
        ""
    )

    reporter = ticket.get(
        "reporter",
        ""
    )

    assignee = ticket.get(
        "assignee",
        ""
    )

    created = ticket.get(
        "created",
        ""
    )

    updated = ticket.get(
        "updated",
        ""
    )


    # ========================================================
    # 6.5 CONSTRUIRE LE PROMPT
    # ========================================================

    prompt = f"""
You are a senior software engineer.

Analyze the Jira ticket using the Analysis Skill
provided below.

Your responsibility is ONLY to produce the
technical analysis of the Jira ticket.

Do not implement anything.

Do not write implementation code.

Do not modify project files.

Do not generate an OpenCode coding prompt.

The Analysis Skill defines the required analysis
structure and output format.

==================================================
ANALYSIS SKILL
==================================================

{skill}

==================================================
JIRA TICKET
==================================================

Key:
{issue_key}

Summary:
{summary}

Description:
{description}

Status:
{status}

Issue Type:
{issue_type}

Priority:
{priority}

Project:
{project}

Project Key:
{project_key}

Reporter:
{reporter}

Assignee:
{assignee}

Created:
{created}

Updated:
{updated}

==================================================
INSTRUCTIONS
==================================================

Analyze ONLY the information provided in the
Jira ticket.

Follow the Analysis Skill exactly.

If information required for the analysis is
missing, explicitly indicate that it is unknown.

Do not invent requirements.

Return ONLY the Markdown technical analysis.

Do not add an introduction.

Do not add a conclusion outside the required
analysis structure.
"""


    # ========================================================
    # 6.6 APPEL OLLAMA
    # ========================================================

    print(
        "\n🧠 Envoi du ticket + Skill à Ollama..."
    )


    try:

        response = llm.invoke(
            prompt
        )

    except Exception as e:

        raise RuntimeError(

            f"""
❌ Erreur Ollama pendant l'analyse.

Modèle :
{OLLAMA_MODEL}

Erreur :
{e}
"""

        )


    # ========================================================
    # 6.7 RÉCUPÉRER LA RÉPONSE
    # ========================================================

    analysis = str(
        response.content
    ).strip()


    # ========================================================
    # 6.8 VALIDATION
    # ========================================================

    if not analysis:

        raise RuntimeError(
            "❌ Ollama n'a retourné aucune analyse."
        )


    # ========================================================
    # 6.9 LOG RESULTAT
    # ========================================================

    print(
        "\n✅ Analyse Markdown générée."
    )


    print(
        "\n"
        + "-" * 60
    )

    print(
        analysis
    )

    print(
        "-" * 60
    )


    # ========================================================
    # 6.10 RETURN LANGGRAPH STATE
    # ========================================================

    return {

        "analysis":
            analysis

    }