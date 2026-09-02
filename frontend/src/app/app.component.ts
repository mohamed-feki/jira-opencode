import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { marked } from 'marked';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {

  // ============================================================
  // API
  // ============================================================

  private apiUrl = 'http://localhost:8000';


  // ============================================================
  // GLOBAL
  // ============================================================

  errorMessage: string = '';


  renderMarkdown(markdown: string): string {

    if (!markdown) {
      return '';
    }

    return marked.parse(markdown) as string;
  }


  // ============================================================
  // WORKFLOW STATES
  // ============================================================

  /*
   * 0 = aucun workflow démarré
   * 1 = Jira / Ticket
   * 2 = Analysis
   * 3 = Prompt
   * 4 = OpenCode
   */

  readonly workflowSteps = [
    {
      id: 1,
      title: 'Jira Agent',
      shortTitle: 'Ticket',
      icon: '🔎'
    },
    {
      id: 2,
      title: 'Analysis Agent',
      shortTitle: 'Analyse',
      icon: '🧠'
    },
    {
      id: 3,
      title: 'Prompt Agent',
      shortTitle: 'Prompt',
      icon: '📝'
    },
    {
      id: 4,
      title: 'OpenCode',
      shortTitle: 'Execution',
      icon: '🚀'
    }
  ];


  // ============================================================
  // ORCHESTRATOR
  // ============================================================

  orchestratorIssueKey: string = '';

  orchestrating: boolean = false;

  orchestratorStarted: boolean = false;

  orchestratorStep: number = 0;

  orchestratorTicket: any = null;

  orchestratorSubtasks: any[] = [];

  orchestratorComplexity: string = '';

  orchestratorAnalysis: string = '';

  orchestratorPrompt: string = '';

  orchestratorEditing: boolean = false;

  orchestratorResult: string = '';

  orchestratorSuccess: boolean = false;

  /*
   * Permet d'afficher un état FAILED dans la map
   * sans modifier la logique métier existante.
   */
  orchestratorFailed: boolean = false;

  orchestratorFailedStep: number = 0;


  // ============================================================
  // STEP BY STEP
  // ============================================================

  stepIssueKey: string = '';

  stepLoading: boolean = false;

  stepTicket: any = null;

  stepAnalysis: string = '';

  stepPrompt: string = '';

  stepResult: string = '';

  stepSuccess: boolean = false;

  stepFailed: boolean = false;

  stepFailedStep: number = 0;


  // ============================================================
  // EDIT MODES
  // ============================================================

  stepTicketEditing: boolean = false;

  stepAnalysisEditing: boolean = false;

  stepPromptEditing: boolean = false;


  // ============================================================
  // BACKUP AVANT MODIFICATION
  // ============================================================

  private stepTicketBackup: any = null;

  private stepAnalysisBackup: string = '';

  private stepPromptBackup: string = '';


  // ============================================================
  // CONSTRUCTOR
  // ============================================================

  constructor(
    private http: HttpClient
  ) {}


  // ============================================================
  // ERROR
  // ============================================================

  clearError(): void {

    this.errorMessage = '';

  }


  // ============================================================
  // ORCHESTRATOR MAP
  // ============================================================

  getOrchestratorStepStatus(stepId: number): string {

    if (this.orchestratorFailed && this.orchestratorFailedStep === stepId) {
      return 'failed';
    }

    if (this.orchestratorStep > stepId) {
      return 'completed';
    }

    if (this.orchestratorStep === stepId && this.orchestrating) {
      return 'running';
    }

    /*
     * Lorsque le workflow est terminé et que l'étape 4 est atteinte.
     */
    if (
      stepId === 4 &&
      this.orchestratorStep === 4 &&
      this.orchestratorSuccess
    ) {
      return 'completed';
    }

    if (
      this.orchestratorStep === stepId &&
      !this.orchestrating
    ) {
      return 'completed';
    }

    return 'idle';
  }


  getOrchestratorStatusLabel(stepId: number): string {

    const status = this.getOrchestratorStepStatus(stepId);

    switch (status) {

      case 'running':
        return 'En cours';

      case 'completed':
        return 'Terminé';

      case 'failed':
        return 'Échec';

      default:
        return 'En attente';
    }
  }


  isOrchestratorStepCompleted(stepId: number): boolean {

    return (
      this.getOrchestratorStepStatus(stepId) === 'completed'
    );
  }


  isOrchestratorStepRunning(stepId: number): boolean {

    return (
      this.getOrchestratorStepStatus(stepId) === 'running'
    );
  }


  isOrchestratorStepFailed(stepId: number): boolean {

    return (
      this.getOrchestratorStepStatus(stepId) === 'failed'
    );
  }


  // ============================================================
  // STEP BY STEP MAP
  // ============================================================

  getStepByStepStatus(stepId: number): string {

    if (
      this.stepFailed &&
      this.stepFailedStep === stepId
    ) {
      return 'failed';
    }


    if (stepId === 1) {

      if (this.stepTicket) {
        return 'completed';
      }

      if (
        this.stepLoading &&
        !this.stepTicket
      ) {
        return 'running';
      }

      return 'idle';
    }


    if (stepId === 2) {

      if (this.stepAnalysis) {
        return 'completed';
      }

      if (
        this.stepLoading &&
        this.stepTicket &&
        !this.stepAnalysis
      ) {
        return 'running';
      }

      return 'idle';
    }


    if (stepId === 3) {

      if (this.stepPrompt) {
        return 'completed';
      }

      if (
        this.stepLoading &&
        this.stepAnalysis &&
        !this.stepPrompt
      ) {
        return 'running';
      }

      return 'idle';
    }


    if (stepId === 4) {

      if (this.stepSuccess) {
        return 'completed';
      }

      if (
        this.stepLoading &&
        this.stepPrompt &&
        !this.stepResult
      ) {
        return 'running';
      }

      return 'idle';
    }


    return 'idle';
  }


  getStepByStepStatusLabel(stepId: number): string {

    const status = this.getStepByStepStatus(stepId);

    switch (status) {

      case 'running':
        return 'En cours';

      case 'completed':
        return 'Terminé';

      case 'failed':
        return 'Échec';

      default:
        return 'En attente';
    }
  }


  isStepCompleted(stepId: number): boolean {

    return (
      this.getStepByStepStatus(stepId) === 'completed'
    );
  }


  isStepRunning(stepId: number): boolean {

    return (
      this.getStepByStepStatus(stepId) === 'running'
    );
  }


  isStepFailed(stepId: number): boolean {

    return (
      this.getStepByStepStatus(stepId) === 'failed'
    );
  }


  // ============================================================
  // ORCHESTRATOR
  // ============================================================

  runOrchestrator(): void {

    const key =
      this.orchestratorIssueKey
        .trim()
        .toUpperCase();


    if (!key) {

      this.errorMessage =
        'Veuillez entrer une clé Jira pour l’orchestrateur.';

      return;
    }


    this.orchestrating = true;

    this.orchestratorStarted = true;

    this.orchestratorStep = 1;

    this.orchestratorTicket = null;

    this.orchestratorSubtasks = [];

    this.orchestratorComplexity = '';

    this.orchestratorAnalysis = '';

    this.orchestratorPrompt = '';

    this.orchestratorEditing = false;

    this.orchestratorResult = '';

    this.orchestratorSuccess = false;

    this.orchestratorFailed = false;

    this.orchestratorFailedStep = 0;

    this.errorMessage = '';


    const url =
      `${this.apiUrl}/api/agents/${key}`;


    console.log(
      '🚀 ORCHESTRATOR:',
      url
    );


    this.http.get<any>(url).subscribe({

      next: (response) => {

        console.log(
          '✅ Orchestrateur terminé:',
          response
        );


        // ======================================================
        // STEP 1
        // ======================================================

        this.orchestratorStep = 1;

        this.orchestratorTicket =
          response.ticket;

        this.orchestratorSubtasks =
          response.subtasks || [];

        this.orchestratorComplexity =
          response.complexity || '';


        /*
         * Petit délai visuel pour laisser la map
         * montrer la progression étape par étape.
         */
        setTimeout(() => {

          // ====================================================
          // STEP 2
          // ====================================================

          this.orchestratorStep = 2;

          this.orchestratorAnalysis =
            response.analysis;


          setTimeout(() => {

            // ==================================================
            // STEP 3
            // ==================================================

            this.orchestratorStep = 3;

            this.orchestratorPrompt =
              response.prompt;


            this.orchestrating = false;

          }, 350);

        }, 350);

      },


      error: (error) => {

        console.error(
          '❌ Erreur Orchestrateur:',
          error
        );


        this.orchestrating = false;

        /*
         * On conserve la map visible pour afficher
         * l'état FAILED.
         */
        this.orchestratorStarted = true;

        this.orchestratorFailed = true;

        this.orchestratorFailedStep =
          this.orchestratorStep || 1;

        this.orchestratorTicket = null;

        this.orchestratorAnalysis = '';

        this.orchestratorPrompt = '';

        this.orchestratorResult = '';


        this.errorMessage =
          error?.error?.detail ||
          'Impossible d’exécuter l’orchestrateur.';

      }

    });

  }


  // ============================================================
  // EDIT ORCHESTRATOR PROMPT
  // ============================================================

  editOrchestratorPrompt(): void {

    if (!this.orchestratorPrompt) {

      this.errorMessage =
        'Aucun prompt disponible à modifier.';

      return;
    }


    this.errorMessage = '';

    this.orchestratorEditing = true;

  }


  // ============================================================
  // IGNORE ORCHESTRATOR MODIFICATION
  // ============================================================

  ignoreOrchestratorPrompt(): void {

    this.orchestratorEditing = false;

    this.errorMessage = '';

    console.log(
      '↩️ Modification du prompt orchestrateur ignorée.'
    );

  }


  // ============================================================
  // EXECUTE ORCHESTRATOR
  // ============================================================

  executeOrchestratorPrompt(): void {

    const key =
      this.orchestratorIssueKey
        .trim()
        .toUpperCase();


    if (!key) {

      this.errorMessage =
        'Veuillez entrer une clé Jira.';

      return;
    }


    if (!this.orchestratorPrompt.trim()) {

      this.errorMessage =
        'Le prompt est vide.';

      return;
    }


    this.orchestrating = true;

    this.errorMessage = '';

    this.orchestratorResult = '';

    this.orchestratorSuccess = false;

    this.orchestratorFailed = false;

    this.orchestratorFailedStep = 0;

    this.orchestratorStep = 4;


    const body = {

      issue_key: key,

      prompt: this.orchestratorPrompt

    };


    this.http.post<any>(

      `${this.apiUrl}/api/opencode/execute`,

      body

    ).subscribe({

      next: (response) => {

        console.log(
          '✅ OpenCode terminé:',
          response
        );


        this.orchestratorResult =
          response.opencode_result || '';


        this.orchestratorSuccess =
          response.success === true;


        this.orchestratorEditing = false;

        this.orchestratorStep = 4;

        this.orchestrating = false;


        if (!this.orchestratorSuccess) {

          this.orchestratorFailed = true;

          this.orchestratorFailedStep = 4;

        }

      },


      error: (error) => {

        console.error(
          '❌ Erreur OpenCode:',
          error
        );


        this.orchestrating = false;

        this.orchestratorSuccess = false;

        this.orchestratorResult = '';

        this.orchestratorFailed = true;

        this.orchestratorFailedStep = 4;


        this.errorMessage =
          error?.error?.detail ||
          'Erreur pendant l’exécution de OpenCode.';

      }

    });

  }


  // ============================================================
  // SAVE + EXECUTE ORCHESTRATOR
  // ============================================================

  saveAndExecuteOrchestrator(): void {

    this.executeOrchestratorPrompt();

  }


  // ============================================================
  // COPY ORCHESTRATOR PROMPT
  // ============================================================

  copyOrchestratorPrompt(): void {

    if (!this.orchestratorPrompt) {

      return;
    }


    navigator.clipboard
      .writeText(this.orchestratorPrompt)

      .then(() => {

        console.log(
          '✅ Prompt orchestrateur copié'
        );

      })

      .catch((error) => {

        console.error(
          '❌ Erreur copie:',
          error
        );

      });

  }


  // ============================================================
  // STEP 1
  // GET JIRA TICKET
  // ============================================================

  getTicket(): void {

    const key =
      this.stepIssueKey
        .trim()
        .toUpperCase();


    if (!key) {

      this.errorMessage =
        'Veuillez entrer une clé Jira.';

      return;
    }


    this.stepIssueKey = key;


    this.stepLoading = true;

    this.errorMessage = '';

    this.stepTicket = null;

    this.stepAnalysis = '';

    this.stepPrompt = '';

    this.stepResult = '';

    this.stepSuccess = false;

    this.stepFailed = false;

    this.stepFailedStep = 0;


    this.stepTicketEditing = false;

    this.stepAnalysisEditing = false;

    this.stepPromptEditing = false;


    this.stepTicketBackup = null;

    this.stepAnalysisBackup = '';

    this.stepPromptBackup = '';


    const url =
      `${this.apiUrl}/api/jira/${key}`;


    console.log(
      '🔎 STEP 1 - GET JIRA:',
      url
    );


    this.http.get<any>(url).subscribe({

      next: (response) => {

        console.log(
          '✅ Ticket récupéré:',
          response
        );


        this.stepTicket = response;

        this.stepLoading = false;

      },


      error: (error) => {

        console.error(
          '❌ Erreur Jira:',
          error
        );


        this.stepLoading = false;

        this.stepTicket = null;

        this.stepFailed = true;

        this.stepFailedStep = 1;


        this.errorMessage =
          error?.error?.detail ||
          'Impossible de récupérer le ticket Jira.';

      }

    });

  }


  // ============================================================
  // STEP 1 - EDIT TICKET
  // ============================================================

  editStepTicket(): void {

    if (!this.stepTicket) {

      return;
    }


    this.stepTicketBackup =
      JSON.parse(
        JSON.stringify(this.stepTicket)
      );


    this.stepTicketEditing = true;

    this.errorMessage = '';


    console.log(
      '✏️ Modification du ticket activée.'
    );

  }


  // ============================================================
  // STEP 1 - SAVE TICKET
  // ============================================================

  saveStepTicket(): void {

    this.stepTicketEditing = false;

    this.stepTicketBackup = null;

    this.errorMessage = '';


    console.log(
      '💾 Ticket modifié et conservé:',
      this.stepTicket
    );

  }


  // ============================================================
  // STEP 1 - IGNORE TICKET
  // ============================================================

  ignoreStepTicket(): void {

    if (this.stepTicketBackup) {

      this.stepTicket =
        JSON.parse(
          JSON.stringify(this.stepTicketBackup)
        );

    }


    this.stepTicketEditing = false;

    this.stepTicketBackup = null;

    this.errorMessage = '';


    console.log(
      '↩️ Modification du ticket ignorée.'
    );

  }


  // ============================================================
  // STEP 2
  // ANALYSIS
  // ============================================================

  analyzeTicket(): void {

    if (!this.stepTicket) {

      this.errorMessage =
        'Veuillez d’abord récupérer le ticket Jira.';

      return;
    }


    this.stepLoading = true;

    this.errorMessage = '';

    this.stepAnalysis = '';

    this.stepPrompt = '';

    this.stepResult = '';

    this.stepFailed = false;

    this.stepFailedStep = 0;


    this.stepPromptEditing = false;


    const body = {

      ticket: this.stepTicket

    };


    console.log(
      '🧠 STEP 2 - POST ANALYSIS'
    );


    console.log(
      '📦 Body:',
      body
    );


    this.http.post<any>(

      `${this.apiUrl}/api/analysis`,

      body

    ).subscribe({

      next: (response) => {

        console.log(
          '✅ Analysis reçue:',
          response
        );


        this.stepAnalysis =
          response.analysis;


        this.stepAnalysisEditing = false;

        this.stepLoading = false;

      },


      error: (error) => {

        console.error(
          '❌ Erreur Analysis:',
          error
        );


        this.stepLoading = false;

        this.stepFailed = true;

        this.stepFailedStep = 2;


        this.errorMessage =
          error?.error?.detail ||
          'Impossible de générer l’analyse.';

      }

    });

  }


  // ============================================================
  // STEP 2 - EDIT ANALYSIS
  // ============================================================

  editStepAnalysis(): void {

    if (!this.stepAnalysis) {

      return;
    }


    this.stepAnalysisBackup =
      this.stepAnalysis;


    this.stepAnalysisEditing = true;

    this.errorMessage = '';


    console.log(
      '✏️ Modification de l’analyse activée.'
    );

  }


  // ============================================================
  // STEP 2 - SAVE ANALYSIS
  // ============================================================

  saveStepAnalysis(): void {

    this.stepAnalysisEditing = false;

    this.stepAnalysisBackup = '';

    this.errorMessage = '';


    console.log(
      '💾 Analyse modifiée et conservée:',
      this.stepAnalysis
    );

  }


  // ============================================================
  // STEP 2 - IGNORE ANALYSIS
  // ============================================================

  ignoreStepAnalysis(): void {

    this.stepAnalysis =
      this.stepAnalysisBackup;


    this.stepAnalysisEditing = false;

    this.stepAnalysisBackup = '';

    this.errorMessage = '';


    console.log(
      '↩️ Modification de l’analyse ignorée.'
    );

  }


  // ============================================================
  // STEP 3
  // GENERATE PROMPT
  // ============================================================

  generateStepPrompt(): void {

    if (!this.stepTicket) {

      this.errorMessage =
        'Veuillez d’abord récupérer le ticket Jira.';

      return;
    }


    if (!this.stepAnalysis) {

      this.errorMessage =
        'Veuillez d’abord analyser le ticket.';

      return;
    }


    this.stepLoading = true;

    this.errorMessage = '';

    this.stepPrompt = '';

    this.stepResult = '';

    this.stepFailed = false;

    this.stepFailedStep = 0;


    this.stepPromptEditing = false;


    const body = {

      ticket: this.stepTicket,

      analysis: this.stepAnalysis

    };


    console.log(
      '📝 STEP 3 - POST PROMPT'
    );


    console.log(
      '📦 Body:',
      body
    );


    this.http.post<any>(

      `${this.apiUrl}/api/prompt`,

      body

    ).subscribe({

      next: (response) => {

        console.log(
          '✅ Prompt généré:',
          response
        );


        this.stepPrompt =
          response.prompt;


        this.stepPromptEditing = false;

        this.stepLoading = false;

      },


      error: (error) => {

        console.error(
          '❌ Erreur Prompt:',
          error
        );


        this.stepLoading = false;

        this.stepFailed = true;

        this.stepFailedStep = 3;


        this.errorMessage =
          error?.error?.detail ||
          'Impossible de générer le prompt.';

      }

    });

  }


  // ============================================================
  // STEP 3 - EDIT PROMPT
  // ============================================================

  editStepPrompt(): void {

    if (!this.stepPrompt) {

      return;
    }


    this.stepPromptBackup =
      this.stepPrompt;


    this.stepPromptEditing = true;

    this.errorMessage = '';


    console.log(
      '✏️ Modification du prompt activée.'
    );

  }


  // ============================================================
  // STEP 3 - SAVE PROMPT
  // ============================================================

  saveStepPrompt(): void {

    this.stepPromptEditing = false;

    this.stepPromptBackup = '';

    this.errorMessage = '';


    console.log(
      '💾 Prompt modifié et conservé:',
      this.stepPrompt
    );

  }


  // ============================================================
  // STEP 3 - IGNORE PROMPT
  // ============================================================

  ignoreStepPrompt(): void {

    this.stepPrompt =
      this.stepPromptBackup;


    this.stepPromptEditing = false;

    this.stepPromptBackup = '';

    this.errorMessage = '';


    console.log(
      '↩️ Modification du prompt ignorée.'
    );

  }


  // ============================================================
  // STEP 4
  // EXECUTE OPENCODE
  // ============================================================

  executeStepPrompt(): void {

    const key =
      this.stepIssueKey
        .trim()
        .toUpperCase();


    if (!key) {

      this.errorMessage =
        'Veuillez entrer une clé Jira.';

      return;
    }


    if (!this.stepPrompt.trim()) {

      this.errorMessage =
        'Le prompt est vide.';

      return;
    }


    if (this.stepPromptEditing) {

      this.errorMessage =
        'Veuillez enregistrer ou ignorer la modification du prompt avant l’exécution.';

      return;
    }


    this.stepLoading = true;

    this.errorMessage = '';

    this.stepResult = '';

    this.stepSuccess = false;

    this.stepFailed = false;

    this.stepFailedStep = 0;


    const body = {

      issue_key: key,

      prompt: this.stepPrompt

    };


    console.log(
      '▶️ STEP 4 - EXECUTE OPENCODE'
    );


    console.log(
      '📦 Body:',
      body
    );


    this.http.post<any>(

      `${this.apiUrl}/api/opencode/execute`,

      body

    ).subscribe({

      next: (response) => {

        console.log(
          '✅ OpenCode terminé:',
          response
        );


        this.stepResult =
          response.opencode_result || '';


        this.stepSuccess =
          response.success === true;


        this.stepLoading = false;


        if (!this.stepSuccess) {

          this.stepFailed = true;

          this.stepFailedStep = 4;

        }

      },


      error: (error) => {

        console.error(
          '❌ Erreur OpenCode:',
          error
        );


        this.stepLoading = false;

        this.stepSuccess = false;

        this.stepResult = '';

        this.stepFailed = true;

        this.stepFailedStep = 4;


        this.errorMessage =
          error?.error?.detail ||
          'Erreur pendant l’exécution de OpenCode.';

      }

    });

  }


  // ============================================================
  // COPY STEP PROMPT
  // ============================================================

  copyStepPrompt(): void {

    if (!this.stepPrompt) {

      return;
    }


    navigator.clipboard
      .writeText(this.stepPrompt)

      .then(() => {

        console.log(
          '✅ Prompt copié'
        );

      })

      .catch((error) => {

        console.error(
          '❌ Erreur copie:',
          error
        );

      });

  }

}