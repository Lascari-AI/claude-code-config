/**
 * Project by ID API Route
 *
 * Server-side project operations for a specific project.
 * GET: Fetch project by ID
 * PATCH: Update project
 * DELETE: Delete project
 */

import { NextRequest, NextResponse } from "next/server";
import { db, projects } from "@/db";
import { eq, and, ne } from "drizzle-orm";
import type { Project, ProjectUpdate } from "@/types/project";

interface RouteParams {
  params: Promise<{ id: string }>;
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
 * GET /api/projects/[id]
 *
 * Fetch a single project by UUID.
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
  const { id } = await params;

  try {
    const result = await db
      .select()
      .from(projects)
      .where(eq(projects.id, id))
      .limit(1);

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Project ${id} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json(mapToProject(result[0]));
  } catch (error) {
    console.error("Error fetching project:", error);
    return NextResponse.json(
      { error: "Failed to fetch project" },
      { status: 500 }
    );
  }
}

/**
 * PATCH /api/projects/[id]
 *
 * Update a project. Only provided fields are updated.
 */
export async function PATCH(request: NextRequest, { params }: RouteParams) {
  const { id } = await params;

  let body: ProjectUpdate;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid request body" },
      { status: 400 }
    );
  }

  try {
    // First check if project exists
    const existing = await db
      .select()
      .from(projects)
      .where(eq(projects.id, id))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json(
        { error: `Project ${id} not found` },
        { status: 404 }
      );
    }

    // If updating slug, check for conflicts
    if (body.slug) {
      const slugConflict = await db
        .select({ id: projects.id })
        .from(projects)
        .where(and(eq(projects.slug, body.slug), ne(projects.id, id)))
        .limit(1);

      if (slugConflict.length > 0) {
        return NextResponse.json(
          { error: `Project with slug '${body.slug}' already exists` },
          { status: 409 }
        );
      }
    }

    // Build update object (map snake_case to camelCase)
    const updateData: Partial<typeof projects.$inferInsert> = {
      updatedAt: new Date().toISOString(),
    };

    if (body.name !== undefined) updateData.name = body.name;
    if (body.slug !== undefined) updateData.slug = body.slug;
    if (body.path !== undefined) updateData.path = body.path;
    if (body.repo_url !== undefined) updateData.repoUrl = body.repo_url;
    if (body.status !== undefined) updateData.status = body.status;
    if (body.onboarding_status !== undefined) {
      // Merge with existing onboarding status
      updateData.onboardingStatus = {
        ...(existing[0].onboardingStatus as object || {}),
        ...body.onboarding_status,
      };
    }
    if (body.metadata_ !== undefined) updateData.metadata = body.metadata_;

    // Perform update
    const result = await db
      .update(projects)
      .set(updateData)
      .where(eq(projects.id, id))
      .returning();

    return NextResponse.json(mapToProject(result[0]));
  } catch (error) {
    console.error("Error updating project:", error);
    return NextResponse.json(
      { error: "Failed to update project" },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/projects/[id]
 *
 * Delete a project by ID.
 */
export async function DELETE(request: NextRequest, { params }: RouteParams) {
  const { id } = await params;

  try {
    const result = await db
      .delete(projects)
      .where(eq(projects.id, id))
      .returning({ id: projects.id });

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Project ${id} not found` },
        { status: 404 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Error deleting project:", error);
    // Check for foreign key constraint violation
    const errorMessage = error instanceof Error ? error.message : "";
    if (errorMessage.includes("foreign key") || errorMessage.includes("violates")) {
      return NextResponse.json(
        { error: "Cannot delete project with existing sessions" },
        { status: 409 }
      );
    }
    return NextResponse.json(
      { error: "Failed to delete project" },
      { status: 500 }
    );
  }
}
