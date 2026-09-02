import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

""" from agents.jira_agent import (
    get_jira_issue,
    format_ticket,
  
) """
from agents.jira_agent_vf import jira_agent_vf
from agents.analysis_agent import (
    analysis_agent
)

from agents.prompt_agent import (
    prompt_agent
)

from graph.workflow import (
    build_prompt_graph,
    build_opencode_graph
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Jira AI Multi-Agent API",
    description="Jira AI Multi-Agent System",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:4200"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Jira AI Multi-Agent API",
        "status": "running"
    }


# ============================================================
# ============================================================
# MODE STEP BY STEP
# ============================================================
# ============================================================


# ============================================================
# STEP 1 — JIRA
#
# GET /api/jira/KAN-1
#
# Agent 1 uniquement
# ============================================================

@app.get("/api/jira/{issue_key}")
async def get_jira_ticket(issue_key: str):

    try:

        issue_key = (
            issue_key
            .strip()
            .upper()
        )

        print("\n" + "=" * 60)
        print("🔎 STEP 1 — JIRA MCP AGENT")
        print("=" * 60)

        print(f"Ticket : {issue_key}")

       # ====================================================
        # STATE
        # ====================================================

        state = {
            "issue_key": issue_key
        }

        # ====================================================
        # JIRA AGENT
        # ====================================================

        result = await jira_agent_vf(
            state
        )


        return result["ticket"]

    except Exception as e:

        print(
            f"\n❌ Erreur Jira : {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


""" 
@app.get("/api/jira/{issue_key}")
def get_jira_ticket(issue_key: str):

    try:

        issue_key = issue_key.strip().upper()

        print(
            "\n"
            + "=" * 60
        )

        print(
            "🔎 STEP 1 — JIRA AGENT"
        )

        print(
            "=" * 60
        )

        print(
            f"Ticket : {issue_key}"
        )

        # ----------------------------------------------------
        # Récupérer Jira
        # ----------------------------------------------------

        jira_data = get_jira_issue(
            issue_key
        )

        # ----------------------------------------------------
        # Formatter
        # ----------------------------------------------------

        ticket = format_ticket(
            jira_data
        )

        print(
            "\n✅ Ticket Jira récupéré."
        )

        return ticket

    except Exception as e:

        print(
            f"\n❌ Erreur Jira : {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

 """
# ============================================================
# REQUEST MODEL — ANALYSIS
# ============================================================

class AnalysisRequest(BaseModel):

    ticket: dict


# ============================================================
# STEP 2 — ANALYSIS
#
# POST /api/analysis
#
# Agent 2 uniquement
# ============================================================

@app.post("/api/analysis")
def analyze_ticket(
    request: AnalysisRequest
):

    try:

        print(
            "\n"
            + "=" * 60
        )

        print(
            "🧠 STEP 2 — ANALYSIS AGENT"
        )

        print(
            "=" * 60
        )

        ticket = request.ticket

        # ----------------------------------------------------
        # Vérification
        # ----------------------------------------------------

        if not ticket:

            raise ValueError(
                "❌ Ticket manquant."
            )

        # ----------------------------------------------------
        # State Agent 2
        # ----------------------------------------------------

        state = {

            "ticket": ticket

        }

        # ----------------------------------------------------
        # Exécuter Agent 2
        # ----------------------------------------------------

        result = analysis_agent(
            state
        )

        analysis = result.get(
            "analysis"
        )

        print(
            "\n✅ Analyse générée."
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {

            "ticket": ticket,

            "analysis": analysis

        }

    except Exception as e:

        print(
            f"\n❌ Erreur Analysis : {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# REQUEST MODEL — PROMPT
# ============================================================

class PromptRequest(BaseModel):

    ticket: dict

    analysis: str


# ============================================================
# STEP 3 — PROMPT
#
# POST /api/prompt
#
# Agent 3 uniquement
# ============================================================

@app.post("/api/prompt")
def generate_prompt(
    request: PromptRequest
):

    try:

        print(
            "\n"
            + "=" * 60
        )

        print(
            "📝 STEP 3 — PROMPT AGENT"
        )

        print(
            "=" * 60
        )

        ticket = request.ticket

        analysis = request.analysis

        # ----------------------------------------------------
        # Vérifications
        # ----------------------------------------------------

        if not ticket:

            raise ValueError(
                "❌ Ticket manquant."
            )

        if not analysis:

            raise ValueError(
                "❌ Analysis manquante."
            )

        # ----------------------------------------------------
        # State Agent 3
        # ----------------------------------------------------

        state = {

            "ticket": ticket,

            "analysis": analysis

        }

        # ----------------------------------------------------
        # Exécuter Agent 3
        # ----------------------------------------------------

        result = prompt_agent(
            state
        )

        prompt = result.get(
            "coding_instruction"
        )

        print(
            "\n✅ Prompt généré."
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {

            "ticket": ticket,

            "analysis": analysis,

            "prompt": prompt

        }

    except Exception as e:

        print(
            f"\n❌ Erreur Prompt : {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# REQUEST MODEL — OPENCODE
# ============================================================

class OpenCodeRequest(BaseModel):

    issue_key: str

    prompt: str


# ============================================================
# STEP 4 — OPENCODE
#
# POST /api/opencode/execute
#
# Agent 4 uniquement
# ============================================================

@app.post("/api/opencode/execute")
def execute_opencode(
    request: OpenCodeRequest
):

    try:

        print(
            "\n"
            + "=" * 60
        )

        print(
            "🚀 STEP 4 — OPENCODE AGENT"
        )

        print(
            "=" * 60
        )

        issue_key = (
            request.issue_key
            .strip()
            .upper()
        )

        prompt = request.prompt

        # ----------------------------------------------------
        # Vérification
        # ----------------------------------------------------

        if not issue_key:

            raise ValueError(
                "❌ Issue key manquante."
            )

        if not prompt:

            raise ValueError(
                "❌ Prompt manquant."
            )

        print(
            f"\n🎫 Ticket : {issue_key}"
        )

        print(
            "\n📝 Prompt reçu :"
        )

        print(
            prompt
        )

        # ----------------------------------------------------
        # Build Agent 4
        # ----------------------------------------------------

        workflow = build_opencode_graph()

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        state = {

            "issue_key":
                issue_key,

            "coding_instruction":
                prompt

        }

        # ----------------------------------------------------
        # Execute
        # ----------------------------------------------------

        result = workflow.invoke(
            state
        )

        return {

            "success":
                result.get(
                    "opencode_return_code"
                ) == 0,

            "issue_key":
                issue_key,

            "prompt":
                prompt,

            "opencode_result":
                result.get(
                    "opencode_result"
                ),

            "return_code":
                result.get(
                    "opencode_return_code"
                )

        }

    except Exception as e:

        print(
            f"\n❌ Erreur OpenCode : {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# ============================================================
# MODE ORCHESTRATEUR
# ============================================================
# ============================================================


# ============================================================
# ORCHESTRATOR
#
# GET /api/agents/KAN-1
#
# Agent 1 → Agent 2 → Agent 3
#
# OpenCode NON exécuté
# ============================================================
@app.get("/api/agents/{issue_key}")
async def run_agents(issue_key: str):

    try:

        issue_key = (
            issue_key
            .strip()
            .upper()
        )

        print(
            "\n"
            + "=" * 60
        )

        print("🤖 ORCHESTRATOR")

        print(
            "=" * 60
        )

        print(
            f"Ticket : {issue_key}"
        )

        # ----------------------------------------------------
        # Build workflow
        # ----------------------------------------------------

        workflow = build_prompt_graph()

        # ----------------------------------------------------
        # Initial state
        # ----------------------------------------------------

        initial_state = {
            "issue_key": issue_key
        }

        # ----------------------------------------------------
        # Execute async workflow
        # ----------------------------------------------------

        result = await workflow.ainvoke(
            initial_state
        )

        # ----------------------------------------------------
        # Get result
        # ----------------------------------------------------

        prompt = result.get(
            "coding_instruction"
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "✅ ORCHESTRATOR TERMINÉ"
        )

        print(
            "=" * 60
        )

        return {

            "mode":
                "orchestrator",

            "issue_key":
                result.get(
                    "issue_key"
                ),

            "ticket":
                result.get(
                    "ticket"
                ),

            "analysis":
                result.get(
                    "analysis"
                ),

            "prompt":
                prompt,

            "complexity":
                result.get("complexity"),

            "subtasks":
                result.get("subtasks")
        }

    except Exception as e:

        print(
            f"\n❌ Erreur Orchestrateur : {e}"
        )
        traceback.print_exc()

        status_code = 503 if str(e).startswith(
            "MCP_WRITE_TOOLS_UNAVAILABLE:"
        ) else 500

        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )