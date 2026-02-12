/**
 * Plan TypeScript Interfaces
 *
 * Type definitions matching the plan.json structure.
 */

/**
 * Status for checkpoints, task groups, and tasks.
 */
export type PlanItemStatus = "pending" | "in_progress" | "completed";

/**
 * Individual action within a task.
 */
export interface Action {
  id: string;
  command: string;
  file: string;
  status: PlanItemStatus;
}

/**
 * Context for reading files before executing a task.
 */
export interface TaskContext {
  read_before: Array<{
    file: string;
    lines?: string;
    purpose: string;
  }>;
  related_files: string[];
}

/**
 * A single task within a task group.
 */
export interface Task {
  id: string;
  title: string;
  file_path: string;
  description: string;
  status: PlanItemStatus;
  context: TaskContext;
  depends_on: string[];
  actions: Action[];
}

/**
 * A group of related tasks within a checkpoint.
 */
export interface TaskGroup {
  id: string;
  title: string;
  objective: string;
  status: PlanItemStatus;
  tasks: Task[];
}

/**
 * File context showing beginning and ending state.
 */
export interface FileContext {
  beginning: {
    files: string[];
    tree: string;
  };
  ending: {
    files: string[];
    tree: string;
  };
}

/**
 * Testing strategy for a checkpoint.
 */
export interface TestingStrategy {
  approach: string;
  verification_steps: string[];
}

/**
 * A checkpoint in the plan (major milestone).
 */
export interface Checkpoint {
  id: number;
  title: string;
  goal: string;
  prerequisites: number[];
  status: PlanItemStatus;
  file_context: FileContext;
  testing_strategy: TestingStrategy;
  task_groups: TaskGroup[];
}

/**
 * The complete plan structure.
 */
export interface Plan {
  $schema?: string;
  session_id: string;
  spec_reference: string;
  created_at: string;
  updated_at: string;
  status: "draft" | "complete";
  checkpoints: Checkpoint[];
}

/**
 * Helper to calculate checkpoint progress.
 */
export function getCheckpointProgress(checkpoint: Checkpoint): {
  completed: number;
  total: number;
  percentage: number;
} {
  let completed = 0;
  let total = 0;

  for (const tg of checkpoint.task_groups) {
    for (const task of tg.tasks) {
      total++;
      if (task.status === "completed") {
        completed++;
      }
    }
  }

  return {
    completed,
    total,
    percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
  };
}

/**
 * Helper to get task group progress.
 */
export function getTaskGroupProgress(taskGroup: TaskGroup): {
  completed: number;
  total: number;
  percentage: number;
} {
  const total = taskGroup.tasks.length;
  const completed = taskGroup.tasks.filter((t) => t.status === "completed").length;

  return {
    completed,
    total,
    percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
  };
}
