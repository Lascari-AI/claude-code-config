/**
 * Projects API Route
 *
 * Server-side project operations using Drizzle ORM.
 * Replaces backend /projects/ endpoints.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, projects } from "@/db";
import { desc, eq } from "drizzle-orm";
import type { ProjectSummary } from "@/types/project";

/**
 * GET /api/projects
 *
 * List projects with optional status filter and pagination.
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const status = searchParams.get("status");
  const limit = parseInt(searchParams.get("limit") || "100");
  const offset = parseInt(searchParams.get("offset") || "0");

  try {
    // Build query with optional status filter
    let query = db
      .select({
        id: projects.id,
        name: projects.name,
        slug: projects.slug,
        status: projects.status,
        path: projects.path,
        created_at: projects.createdAt,
        updated_at: projects.updatedAt,
      })
      .from(projects)
      .orderBy(desc(projects.updatedAt))
      .limit(limit)
      .offset(offset);

    // Apply status filter if provided
    if (status) {
      query = query.where(eq(projects.status, status)) as typeof query;
    }

    const result = await query;

    // Map to ProjectSummary format (snake_case for API compatibility)
    const summaries: ProjectSummary[] = result.map((row) => ({
      id: row.id,
      name: row.name,
      slug: row.slug,
      status: row.status,
      path: row.path,
      created_at: row.created_at,
      updated_at: row.updated_at,
    }));

    return NextResponse.json(summaries);
  } catch (error) {
    console.error("Error fetching projects:", error);
    return NextResponse.json(
      { error: "Failed to fetch projects" },
      { status: 500 }
    );
  }
}
