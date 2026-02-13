/**
 * Sessions API Route
 *
 * Server-side session operations using Drizzle ORM.
 * Replaces backend /sessions/ endpoints.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, sessions } from "@/db";
import { desc, eq, and, SQL } from "drizzle-orm";
import type { SessionSummary } from "@/types/session";

/**
 * GET /api/sessions
 *
 * List sessions with optional filters and pagination.
 *
 * Query params:
 * - status_filter: Filter by session status
 * - session_type: Filter by session type (full, quick, research)
 * - project_id: Filter by parent project
 * - limit: Maximum results (default 100)
 * - offset: Number to skip (default 0)
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const statusFilter = searchParams.get("status_filter");
  const sessionType = searchParams.get("session_type");
  const projectId = searchParams.get("project_id");
  const limit = parseInt(searchParams.get("limit") || "100");
  const offset = parseInt(searchParams.get("offset") || "0");

  try {
    // Build where conditions
    const conditions: SQL[] = [];

    if (statusFilter) {
      conditions.push(eq(sessions.status, statusFilter));
    }
    if (sessionType) {
      conditions.push(eq(sessions.sessionType, sessionType));
    }
    if (projectId) {
      conditions.push(eq(sessions.projectId, projectId));
    }

    // Execute query with conditions
    const result = await db
      .select({
        id: sessions.id,
        session_slug: sessions.sessionSlug,
        title: sessions.title,
        status: sessions.status,
        session_type: sessions.sessionType,
        project_id: sessions.projectId,
        checkpoints_completed: sessions.checkpointsCompleted,
        checkpoints_total: sessions.checkpointsTotal,
        total_cost: sessions.totalCost,
        created_at: sessions.createdAt,
        updated_at: sessions.updatedAt,
      })
      .from(sessions)
      .where(conditions.length > 0 ? and(...conditions) : undefined)
      .orderBy(desc(sessions.updatedAt))
      .limit(limit)
      .offset(offset);

    // Map to SessionSummary format
    const summaries: SessionSummary[] = result.map((row) => ({
      id: row.id,
      session_slug: row.session_slug,
      title: row.title,
      status: row.status as SessionSummary["status"],
      session_type: row.session_type as SessionSummary["session_type"],
      project_id: row.project_id,
      checkpoints_completed: row.checkpoints_completed,
      checkpoints_total: row.checkpoints_total,
      total_cost: row.total_cost,
      created_at: row.created_at,
      updated_at: row.updated_at,
    }));

    return NextResponse.json(summaries);
  } catch (error) {
    console.error("Error fetching sessions:", error);
    return NextResponse.json(
      { error: "Failed to fetch sessions" },
      { status: 500 }
    );
  }
}
