/**
 * Project Onboarding API Route
 *
 * Onboard a new project with path validation.
 * Validates path exists, checks for .claude directory,
 * and creates project with appropriate status.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, projects } from "@/db";
import { eq } from "drizzle-orm";
import { randomUUID } from "crypto";
import { stat } from "fs/promises";
import { join, normalize } from "path";
import { homedir } from "os";
import type { Project, OnboardingStatus } from "@/types/project";

interface OnboardRequest {
  name: string;
  path: string;
}

/**
 * Expand ~ to home directory
 */
function expandPath(path: string): string {
  if (path.startsWith("~")) {
    return join(homedir(), path.slice(1));
  }
  return path;
}

/**
 * Check if a path exists and is a directory
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
 * Check if path exists at all
 */
async function pathExists(path: string): Promise<boolean> {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

/**
 * Generate URL-safe slug from name
 */
function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/_/g, "-")
    .replace(/[^a-z0-9-]/g, "");
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
 * POST /api/projects/onboard
 *
 * Onboard a new project with path validation.
 */
export async function POST(request: NextRequest) {
  let body: OnboardRequest;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid request body" },
      { status: 400 }
    );
  }

  const { name, path: rawPath } = body;

  if (!name || !rawPath) {
    return NextResponse.json(
      { error: "name and path are required" },
      { status: 400 }
    );
  }

  // Expand and normalize path
  const expandedPath = normalize(expandPath(rawPath));

  // Validate path
  const exists = await pathExists(expandedPath);
  const pathValidated = exists && (await isDirectory(expandedPath));
  let pathError: string | null = null;

  if (!exists) {
    pathError = "Path does not exist";
  } else if (!pathValidated) {
    pathError = "Path is not a directory";
  }

  // Check for .claude directory
  const claudeDirPath = join(expandedPath, ".claude");
  const claudeDirExists = pathValidated ? await isDirectory(claudeDirPath) : false;

  // Build onboarding status
  const onboardingStatus: OnboardingStatus = {
    path_validated: pathValidated,
    claude_dir_exists: claudeDirExists,
    settings_configured: false,
    skills_linked: false,
    agents_linked: false,
    docs_foundation: false,
  };

  // Determine project status based on validation
  let projectStatus: Project["status"];
  if (pathValidated && claudeDirExists) {
    projectStatus = "active";
  } else if (pathValidated) {
    projectStatus = "onboarding";
  } else {
    projectStatus = "pending";
  }

  // Generate slug from name
  const slug = generateSlug(name);

  try {
    // Check if slug already exists
    const existing = await db
      .select({ id: projects.id })
      .from(projects)
      .where(eq(projects.slug, slug))
      .limit(1);

    if (existing.length > 0) {
      return NextResponse.json(
        { error: `Project with slug '${slug}' already exists` },
        { status: 409 }
      );
    }

    const now = new Date().toISOString();
    const newProject = {
      id: randomUUID(),
      name,
      slug,
      path: expandedPath,
      repoUrl: null,
      status: projectStatus,
      onboardingStatus,
      metadata: {},
      createdAt: now,
      updatedAt: now,
    };

    const result = await db.insert(projects).values(newProject).returning();

    return NextResponse.json(mapToProject(result[0]), { status: 201 });
  } catch (error) {
    console.error("Error onboarding project:", error);
    return NextResponse.json(
      { error: "Failed to onboard project" },
      { status: 500 }
    );
  }
}
