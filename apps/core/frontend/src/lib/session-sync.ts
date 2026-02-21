/**
 * Session Sync Utilities
 *
 * Filesystem → Database sync for sessions.
 * Reads state.json from agents/sessions/{slug}/ and upserts to database.
 *
 * Filesystem is source of truth - database is a reconstructable index.
 */

import { readdir, readFile, stat } from "fs/promises";
import { join } from "path";
import { randomUUID } from "crypto";
import { db, sessions } from "@/db";
import { eq } from "drizzle-orm";
import type { NewSession } from "@/db/types";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface StateJson {
  topic?: string;
  description?: string;
  current_phase?: string;
  status?: string;
  session_type?: string;
  granularity?: string;
  phase_history?: Record<string, string | null>;
  build_progress?: {
    checkpoints_total?: number;
    checkpoints_completed?: number[];
    current_checkpoint?: number;
  };
  plan_state?: {
    checkpoints_total?: number;
    checkpoints_completed?: number[];
    current_checkpoint?: number;
  };
  phases?: Record<string, { started_at?: string; finalized_at?: string; completed_at?: string; status?: string }>;
  git?: {
    branch?: string;
    worktree?: string;
    base_branch?: string;
  };
  commits?: Array<{
    sha?: string;
    message?: string;
    checkpoint?: number;
    checkpoint_id?: number;
    created_at?: string;
  }>;
  artifacts?: Record<string, string>;
}

interface SyncResult {
  synced: Array<{
    session_slug: string;
    id: string;
    current_phase: string;
    status: string;
  }>;
  failed: Array<{
    session_slug: string;
    error: string;
    details?: string;
  }>;
  total: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// STATE MAPPING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Check if state.json is v2 format.
 */
function isV2Schema(state: StateJson): boolean {
  return "phase_history" in state || "build_progress" in state;
}

/**
 * Map state.json to session database record.
 */
function mapStateToSession(
  state: StateJson,
  sessionSlug: string,
  workingDir: string,
  sessionDir: string,
  projectId: string | null,
  specExists: boolean,
  planExists: boolean,
  existingId?: string
): NewSession {
  const isV2 = isV2Schema(state);
  const now = new Date().toISOString();

  // Current phase
  const currentPhase = state.current_phase || "spec";

  // Status
  let status = state.status || "active";
  if (!isV2) {
    const phases = state.phases || {};
    if (phases.build?.status === "in_progress") {
      status = "active";
    }
  }

  // Build progress
  let checkpointsTotal = 0;
  let checkpointsCompleted = 0;

  if (isV2) {
    const bp = state.build_progress || {};
    checkpointsTotal = bp.checkpoints_total || 0;
    checkpointsCompleted = (bp.checkpoints_completed || []).length;
  } else {
    const ps = state.plan_state || {};
    checkpointsTotal = ps.checkpoints_total || 0;
    checkpointsCompleted = (ps.checkpoints_completed || []).length;
  }

  // Build progress — checkpoint list
  const checkpointsCompletedList = isV2
    ? (state.build_progress?.checkpoints_completed || [])
    : (state.plan_state?.checkpoints_completed || []);

  const currentCheckpoint = isV2
    ? (state.build_progress?.current_checkpoint ?? null)
    : (state.plan_state?.current_checkpoint ?? null);

  // Git context
  const git = state.git || {};

  // Session type
  const sessionType = state.session_type || state.granularity || "full";

  // Overflow metadata — only fields without dedicated columns
  const metadata: Record<string, unknown> = {};
  if (state.phases) metadata.phases = state.phases;
  if (state.granularity) metadata.granularity = state.granularity;

  return {
    id: existingId || randomUUID(),
    sessionSlug,
    title: state.topic || null,
    description: state.description || null,
    projectId: projectId || null,
    status,
    currentPhase,
    sessionType,
    phaseHistory: state.phase_history || {},
    workingDir,
    sessionDir,
    gitWorktree: git.worktree || null,
    gitBranch: git.branch || null,
    gitBaseBranch: git.base_branch || null,
    specExists,
    planExists,
    checkpointsTotal,
    checkpointsCompleted,
    checkpointsCompletedList,
    currentCheckpoint,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    totalCost: 0,
    errorMessage: null,
    errorPhase: null,
    commitsList: state.commits || [],
    artifacts: state.artifacts || {},
    metadata: Object.keys(metadata).length > 0 ? metadata : null,
    createdAt: now,
    updatedAt: now,
    startedAt: null,
    completedAt: null,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// SYNC FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Check if a path exists and is a directory.
 */
async function isDirectory(path: string): Promise<boolean> {
  try {
    const stats = await stat(path);
    return stats.isDirectory();
  } catch {
    return false;
  }
}

/**
 * Check if a file exists.
 */
async function fileExists(path: string): Promise<boolean> {
  try {
    const stats = await stat(path);
    return stats.isFile();
  } catch {
    return false;
  }
}

/**
 * Sync a single session from filesystem to database.
 */
export async function syncSessionFromFilesystem(
  workingDir: string,
  sessionSlug: string,
  projectId: string | null
): Promise<{ id: string; current_phase: string; status: string }> {
  const sessionDir = join(workingDir, "agents/sessions", sessionSlug);
  const statePath = join(sessionDir, "state.json");

  // Read state.json
  const stateContent = await readFile(statePath, "utf-8");
  const state: StateJson = JSON.parse(stateContent);

  // Check artifact existence
  const specExists = await fileExists(join(sessionDir, "spec.md"));
  const planExists = await fileExists(join(sessionDir, "plan.json"));

  // Check if session already exists
  const existing = await db
    .select({ id: sessions.id })
    .from(sessions)
    .where(eq(sessions.sessionSlug, sessionSlug))
    .limit(1);

  const currentPhase = state.current_phase || "spec";
  const status = state.status || "active";

  if (existing.length > 0) {
    // Update existing session
    const sessionData = mapStateToSession(
      state,
      sessionSlug,
      workingDir,
      sessionDir,
      projectId,
      specExists,
      planExists,
      existing[0].id
    );

    await db
      .update(sessions)
      .set({
        title: sessionData.title,
        description: sessionData.description,
        projectId: sessionData.projectId,
        status: sessionData.status,
        currentPhase: sessionData.currentPhase,
        sessionType: sessionData.sessionType,
        phaseHistory: sessionData.phaseHistory,
        gitWorktree: sessionData.gitWorktree,
        gitBranch: sessionData.gitBranch,
        gitBaseBranch: sessionData.gitBaseBranch,
        specExists: sessionData.specExists,
        planExists: sessionData.planExists,
        checkpointsTotal: sessionData.checkpointsTotal,
        checkpointsCompleted: sessionData.checkpointsCompleted,
        checkpointsCompletedList: sessionData.checkpointsCompletedList,
        currentCheckpoint: sessionData.currentCheckpoint,
        commitsList: sessionData.commitsList,
        artifacts: sessionData.artifacts,
        metadata: sessionData.metadata,
        updatedAt: new Date().toISOString(),
      })
      .where(eq(sessions.id, existing[0].id));

    return { id: existing[0].id, current_phase: currentPhase, status };
  } else {
    // Create new session
    const sessionData = mapStateToSession(
      state,
      sessionSlug,
      workingDir,
      sessionDir,
      projectId,
      specExists,
      planExists
    );

    await db.insert(sessions).values(sessionData);

    return { id: sessionData.id, current_phase: currentPhase, status };
  }
}

/**
 * Sync all sessions in a project directory.
 *
 * Scans agents/sessions/ and syncs each session to the database.
 */
export async function syncAllSessionsInProject(
  workingDir: string,
  projectId: string
): Promise<SyncResult> {
  const sessionsDir = join(workingDir, "agents/sessions");

  // Check if sessions directory exists
  if (!(await isDirectory(sessionsDir))) {
    return { synced: [], failed: [], total: 0 };
  }

  const synced: SyncResult["synced"] = [];
  const failed: SyncResult["failed"] = [];

  // Read session directories
  const entries = await readdir(sessionsDir, { withFileTypes: true });

  for (const entry of entries) {
    if (!entry.isDirectory()) {
      continue;
    }

    const sessionSlug = entry.name;
    const sessionDir = join(sessionsDir, sessionSlug);
    const statePath = join(sessionDir, "state.json");

    // Check for state.json
    if (!(await fileExists(statePath))) {
      failed.push({
        session_slug: sessionSlug,
        error: "state.json not found",
      });
      continue;
    }

    try {
      const result = await syncSessionFromFilesystem(
        workingDir,
        sessionSlug,
        projectId
      );

      synced.push({
        session_slug: sessionSlug,
        id: result.id,
        current_phase: result.current_phase,
        status: result.status,
      });
    } catch (error) {
      if (error instanceof SyntaxError) {
        failed.push({
          session_slug: sessionSlug,
          error: "invalid state.json",
          details: error.message,
        });
      } else {
        failed.push({
          session_slug: sessionSlug,
          error: "unexpected error",
          details: error instanceof Error ? error.message : String(error),
        });
      }
    }
  }

  return {
    synced,
    failed,
    total: synced.length + failed.length,
  };
}
