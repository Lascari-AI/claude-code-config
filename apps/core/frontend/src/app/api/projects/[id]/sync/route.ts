/**
 * Project Sync API Route
 *
 * POST: Trigger background sync for all sessions in this project.
 * Returns 202 Accepted immediately - sync runs asynchronously.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, projects } from "@/db";
import { eq } from "drizzle-orm";

interface RouteParams {
  params: Promise<{ id: string }>;
}

/**
 * POST /api/projects/[id]/sync
 *
 * Trigger background batch sync for all sessions in the project.
 * Returns 202 Accepted immediately - actual sync happens asynchronously.
 */
export async function POST(request: NextRequest, { params }: RouteParams) {
  const { id } = await params;

  try {
    // Verify project exists
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

    // TODO: Call Python backend's batch sync function
    // For now, return 202 to establish the endpoint contract
    // Integration with session_db.async_sync.queue_batch_sync_task
    // will be added in Task 2.1.2

    return NextResponse.json(
      {
        status: "accepted",
        message: "Session sync triggered",
        project_id: project.id
      },
      { status: 202 }
    );
  } catch (error) {
    console.error("Error triggering project sync:", error);
    return NextResponse.json(
      { error: "Failed to trigger project sync" },
      { status: 500 }
    );
  }
}
