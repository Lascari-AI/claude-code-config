/**
 * Projects API Route
 *
 * Server-side project operations using Drizzle ORM.
 * Replaces backend /projects/ endpoints.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, projects } from "@/db";
import { desc, eq } from "drizzle-orm";
import { randomUUID } from "crypto";
import type { Project, ProjectCreate, ProjectSummary } from "@/types/project";

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

/**
 * Map database row to Project type with snake_case keys
 */
function mapToProject(row: typeof projects.$inferSelect): Project {
  return {
    id: row.id,
    name: row.name,
    slug: row.slug,
    path: row.path,
    repo_url: row.repoUrl,
    status: row.status as Project["status"],
    onboarding_status: (row.onboardingStatus as Project["onboarding_status"]) ?? {
      path_validated: false,
      claude_dir_exists: false,
      settings_configured: false,
      skills_linked: false,
      agents_linked: false,
      docs_foundation: false,
    },
    metadata_: (row.metadata as Record<string, unknown>) ?? {},
    created_at: row.createdAt,
    updated_at: row.updatedAt,
  };
}

/**
 * POST /api/projects
 *
 * Create a new project.
 */
export async function POST(request: NextRequest) {
  let body: ProjectCreate;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid request body" },
      { status: 400 }
    );
  }

  // Validate required fields
  if (!body.name || !body.slug || !body.path) {
    return NextResponse.json(
      { error: "name, slug, and path are required" },
      { status: 400 }
    );
  }

  try {
    // Check if slug already exists
    const existing = await db
      .select({ id: projects.id })
      .from(projects)
      .where(eq(projects.slug, body.slug))
      .limit(1);

    if (existing.length > 0) {
      return NextResponse.json(
        { error: `Project with slug '${body.slug}' already exists` },
        { status: 409 }
      );
    }

    const now = new Date().toISOString();
    const newProject = {
      id: randomUUID(),
      name: body.name,
      slug: body.slug,
      path: body.path,
      repoUrl: body.repo_url ?? null,
      status: body.status ?? "pending",
      onboardingStatus: body.onboarding_status ?? {
        path_validated: false,
        claude_dir_exists: false,
        settings_configured: false,
        skills_linked: false,
        agents_linked: false,
        docs_foundation: false,
      },
      metadata: body.metadata_ ?? {},
      createdAt: now,
      updatedAt: now,
    };

    const result = await db.insert(projects).values(newProject).returning();

    return NextResponse.json(mapToProject(result[0]), { status: 201 });
  } catch (error) {
    console.error("Error creating project:", error);
    return NextResponse.json(
      { error: "Failed to create project" },
      { status: 500 }
    );
  }
}
