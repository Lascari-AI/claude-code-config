/**
 * Session TypeScript Interfaces
 *
 * Type definitions matching the backend API models.
 */

/**
 * Session lifecycle status.
 */
export type SessionStatus =
  | "created"
  | "spec"
  | "spec_done"
  | "plan"
  | "plan_done"
  | "build"
  | "docs"
  | "complete"
  | "failed"
  | "paused";

/**
 * Session type (workflow variant).
 */
export type SessionType = "full" | "quick" | "research";

/**
 * Workflow phase for UI display.
 */
export type SessionPhase = "spec" | "plan" | "build" | "docs";

/**
 * Phase status for swimlane visualization.
 */
export type PhaseStatus = "pending" | "in_progress" | "complete";

/**
 * Full session entity with all fields.
 */
export interface Session {
  id: string;
  session_slug: string;
  title: string | null;
  description: string | null;
  project_id: string | null;
  status: SessionStatus;
  session_type: SessionType;
  working_dir: string;
  session_dir: string | null;
  git_worktree: string | null;
  git_branch: string | null;
  spec_exists: boolean;
  plan_exists: boolean;
  checkpoints_total: number;
  checkpoints_completed: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost: number;
  error_message: string | null;
  error_phase: string | null;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Lightweight session info for list views.
 */
export interface SessionSummary {
  id: string;
  session_slug: string;
  title: string | null;
  status: SessionStatus;
  session_type: SessionType;
  project_id: string | null;
  checkpoints_completed: number;
  checkpoints_total: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

/**
 * Helper to determine current phase from session status.
 */
export function getCurrentPhase(status: SessionStatus): SessionPhase | null {
  switch (status) {
    case "created":
    case "spec":
    case "spec_done":
      return "spec";
    case "plan":
    case "plan_done":
      return "plan";
    case "build":
      return "build";
    case "docs":
      return "docs";
    case "complete":
    case "failed":
    case "paused":
      return null;
    default:
      return null;
  }
}

/**
 * Helper to get phase status for swimlane display.
 */
export function getPhaseStatus(
  phase: SessionPhase,
  sessionStatus: SessionStatus
): PhaseStatus {
  const phaseOrder: SessionPhase[] = ["spec", "plan", "build", "docs"];
  const currentPhase = getCurrentPhase(sessionStatus);

  if (!currentPhase) {
    // Session is complete, failed, or paused
    if (sessionStatus === "complete") return "complete";
    return "pending";
  }

  const phaseIndex = phaseOrder.indexOf(phase);
  const currentIndex = phaseOrder.indexOf(currentPhase);

  if (phaseIndex < currentIndex) return "complete";
  if (phaseIndex === currentIndex) return "in_progress";
  return "pending";
}
