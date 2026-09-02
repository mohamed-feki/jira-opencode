import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

from graph.state import AgentState


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY"
)


if not OLLAMA_API_KEY:

    raise ValueError(
        "❌ OLLAMA_API_KEY manquante."
    )


llm = ChatOllama(

    model="gemma4:31b-cloud",

    base_url="https://ollama.com",

    client_kwargs={

        "headers": {

            "Authorization":
                f"Bearer {OLLAMA_API_KEY}"

        }

    },

    temperature=0,

)


# ============================================================
# LOAD SKILL
# ============================================================

def load_skill() -> str:

    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )


    skill_path = os.path.join(

        base_dir,

        "skills",

        "prompt_agent",

        "skill.md"

    )


    if not os.path.isfile(
        skill_path
    ):

        raise FileNotFoundError(
            f"""
❌ Skill introuvable :

{skill_path}
"""
        )


    with open(

        skill_path,

        "r",

        encoding="utf-8"

    ) as file:

        return file.read()


# ============================================================
# PROMPT AGENT
# ============================================================
def prompt_agent(state: AgentState) -> AgentState:

    ticket = state.get("ticket")
    analysis = state.get("analysis")

    if not ticket:
        raise ValueError("❌ Ticket manquant.")

    if not analysis:
        raise ValueError("❌ Analyse manquante.")

    skill = load_skill()

    prompt = f"""
Follow the Jira To Prompt Skill below.

==================================================
SKILL
==================================================

{skill}

==================================================
JIRA TICKET
==================================================

{ticket}

==================================================
TECHNICAL ANALYSIS
==================================================

{analysis}

==================================================
TASK
==================================================

Generate the final implementation instruction
according to the Skill.

If the ticket does not specify a language, framework,
or approach, use the most common and idiomatic choice
for this type of task. Default to Python for general
coding tasks.

Return only the final Markdown instruction.
"""

    response = llm.invoke(prompt)

    coding_instruction = str(
        response.content
    ).strip()

    if not coding_instruction:
        raise RuntimeError(
            "❌ Aucune coding instruction générée."
        )

    return {
        "coding_instruction": coding_instruction
    }