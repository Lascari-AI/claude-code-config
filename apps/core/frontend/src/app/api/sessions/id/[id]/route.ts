/**
 * Session by ID API Route
 *
 * Server-side session operations for a specific session.
 * GET: Fetch session by ID
 * DELETE: Delete session and all dependent records + filesystem
 */

import { NextRequest, NextResponse } from "next/server";
import { db, sessions, agents, agentLogs, interactiveMessages } from "@/db";
import { eq } from "drizzle-orm";
import { rm } from "fs/promises";
import type { Session } from "@/types/session";

/**
 * Map database row to Session type with snake_case keys
 */
function mapToSession(row: typeof sessions.$inferSelect): Session {
  return {
    id: row.id,
    session_slug: row.sessionSlug,
    title: row.title,
    description: row.description,
    project_id: row.projectId,
    status: row.status as Session["status"],
    session_type: row.sessionType as Session["session_type"],
    working_dir: row.workingDir,
    session_dir: row.sessionDir,
    git_worktree: row.gitWorktree,
    git_branch: row.gitBranch,
    spec_exists: row.specExists,
    plan_exists: row.planExists,
    checkpoints_total: row.checkpointsTotal,
    checkpoints_completed: row.checkpointsCompleted,
    total_input_tokens: row.totalInputTokens,
    total_output_tokens: row.totalOutputTokens,
    total_cost: row.totalCost,
    error_message: row.errorMessage,
    error_phase: row.errorPhase,
    metadata_: (row.metadata as Record<string, unknown>) ?? {},
    created_at: row.createdAt,
    updated_at: row.updatedAt,
    started_at: row.startedAt,
    completed_at: row.completedAt,
  };
}

/**
 * GET /api/sessions/id/[id]
 *
 * Get a single session by UUID.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const result = await db
      .select()
      .from(sessions)
      .where(eq(sessions.id, id))
      .limit(1);

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Session ${id} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json(mapToSession(result[0]));
  } catch (error) {
    console.error("Error fetching session:", error);
    return NextResponse.json(
      { error: "Failed to fetch session" },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/sessions/id/[id]
 *
 * Delete a session and all dependent records (cascade) + filesystem folder.
 * Deletes: interactiveMessages → agentLogs → agents → session
 * Then removes the session directory from disk.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    // Fetch session to get sessionDir for filesystem cleanup
    const existing = await db
      .select({ id: sessions.id, sessionDir: sessions.sessionDir })
      .from(sessions)
      .where(eq(sessions.id, id))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json(
        { error: `Session ${id} not found` },
        { status: 404 }
      );
    }

    const sessionDir = existing[0].sessionDir;

    // Cascade delete dependent records in FK order
    await db.delete(interactiveMessages).where(eq(interactiveMessages.sessionId, id));
    await db.delete(agentLogs).where(eq(agentLogs.sessionId, id));
    await db.delete(agents).where(eq(agents.sessionId, id));
    await db.delete(sessions).where(eq(sessions.id, id));

    // Delete filesystem folder (best-effort — DB is already clean)
    if (sessionDir) {
      try {
        await rm(sessionDir, { recursive: true, force: true });
      } catch (fsError) {
        console.warn("Failed to delete session directory:", sessionDir, fsError);
      }
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Error deleting session:", error);
    return NextResponse.json(
      { error: "Failed to delete session" },
      { status: 500 }
    );
  }
}
