/**
 * Session State TypeScript Interfaces
 *
 * Type definitions matching the state.json structure from session files.
 */

/**
 * Phase status values.
 */
export type PhaseStatusValue = "draft" | "finalized" | "finalized_complete" | "in_progress" | "completed" | null;

/**
 * Phase tracking in session state.
 */
export interface PhaseState {
  status: PhaseStatusValue;
  started_at: string | null;
  finalized_at?: string | null;
  completed_at?: string | null;
}

/**
 * Phases container.
 */
export interface SessionPhases {
  spec: PhaseState;
  plan: PhaseState;
  build: PhaseState;
}

/**
 * Plan state tracking.
 */
export interface PlanState {
  status: "pending" | "in_progress" | "completed" | null;
  checkpoints_total: number;
  checkpoints_detailed: number;
  checkpoints_completed: number[];
  current_checkpoint: number | null;
  current_task_group: string | null;
  current_task: string | null;
  last_updated: string | null;
  summary: string;
}

/**
 * Key decision made during session.
 */
export interface KeyDecision {
  decision: string;
  rationale: string;
  date: string;
}

/**
 * Commit record.
 */
export interface SessionCommit {
  checkpoint_id: number;
  sha: string;
  message: string;
  created_at: string;
}

/**
 * Documentation update.
 */
export interface DocUpdate {
  file: string;
  action: "created" | "updated" | "deleted";
  description?: string;
}

/**
 * Research artifact.
 */
export interface ResearchArtifact {
  name: string;
  path: string;
  type: string;
  created_at: string;
}

/**
 * The full session state structure (state.json).
 */
export interface SessionState {
  $schema?: string;
  session_id: string;
  created_at: string;
  updated_at: string;
  topic: string;
  description: string;
  granularity: "feature" | "task" | "bug" | "research";
  parent_session: string | null;
  current_phase: "spec" | "plan" | "build" | "docs" | null;
  phases: SessionPhases;
  goals: {
    high_level: string[];
    mid_level: string[];
    low_level: string[];
  };
  open_questions: string[];
  key_decisions: KeyDecision[];
  plan_state: PlanState | null;
  commits: SessionCommit[];
  research_artifacts: ResearchArtifact[];
  doc_updates: DocUpdate[];
}

/**
 * Helper to get phase display status.
 */
export function getPhaseDisplayStatus(phase: PhaseState): string {
  if (!phase.status) return "Not Started";

  switch (phase.status) {
    case "draft":
      return "In Progress";
    case "finalized":
    case "finalized_complete":
      return "Complete";
    case "in_progress":
      return "In Progress";
    case "completed":
      return "Complete";
    default:
      return "Unknown";
  }
}

/**
 * Helper to check if a phase is complete.
 */
export function isPhaseComplete(phase: PhaseState): boolean {
  return phase.status === "finalized" || phase.status === "finalized_complete" || phase.status === "completed";
}
