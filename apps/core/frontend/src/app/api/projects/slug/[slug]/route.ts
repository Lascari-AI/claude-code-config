/**
 * Project by Slug API Route
 *
 * Fetch a single project by its URL-safe slug.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, projects } from "@/db";
import { eq } from "drizzle-orm";
import type { Project } from "@/types/project";

interface RouteParams {
  params: Promise<{ slug: string }>;
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
 * GET /api/projects/slug/[slug]
 *
 * Fetch a single project by its slug.
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
  const { slug } = await params;

  try {
    const result = await db
      .select()
      .from(projects)
      .where(eq(projects.slug, slug))
      .limit(1);

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Project with slug '${slug}' not found` },
        { status: 404 }
      );
    }

    return NextResponse.json(mapToProject(result[0]));
  } catch (error) {
    console.error("Error fetching project by slug:", error);
    return NextResponse.json(
      { error: "Failed to fetch project" },
      { status: 500 }
    );
  }
}
