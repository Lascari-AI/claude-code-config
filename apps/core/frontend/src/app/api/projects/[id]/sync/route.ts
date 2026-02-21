/**
 * Project Sync API Route
 *
 * POST: Sync all sessions in this project from filesystem to database.
 * Reads state.json from agents/sessions/{slug}/ and upserts to database.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, projects } from "@/db";
import { eq } from "drizzle-orm";
import { syncAllSessionsInProject } from "@/lib/session-sync";

interface RouteParams {
  params: Promise<{ id: string }>;
}

/**
 * POST /api/projects/[id]/sync
 *
 * Sync all sessions from filesystem to database.
 * Returns sync results with success/failure counts.
 */
export async function POST(request: NextRequest, { params }: RouteParams) {
  const { id } = await params;

  try {
    // Verify project exists and get path
    const result = await db
      .select({ id: projects.id, path: projects.path })
      .from(projects)
      .where(eq(projects.id, id))
      .limit(1);

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Project ${id} not found` },
        { status: 404 }
      );
    }

    const project = result[0];

    // Perform sync
    const syncResult = await syncAllSessionsInProject(project.path, project.id);

    return NextResponse.json({
      status: "completed",
      message: `Synced ${syncResult.synced.length} sessions`,
      project_id: project.id,
      ...syncResult,
    });
  } catch (error) {
    console.error("Error syncing project sessions:", error);
    return NextResponse.json(
      {
        error: "Failed to sync project sessions",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}
