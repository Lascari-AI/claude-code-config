/**
 * Projects API Client
 *
 * Typed API functions for project CRUD operations.
 */

import { fetchApi } from "./api";
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectSummary,
} from "@/types/project";

/**
 * Fetch all projects.
 *
 * Uses local Next.js API route with direct Drizzle database access.
 *
 * @param status - Optional status filter
 * @param limit - Maximum results (default 100)
 * @param offset - Number of results to skip (default 0)
 */
export async function getProjects(
  status?: string,
  limit = 100,
  offset = 0
): Promise<ProjectSummary[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  // Use local Next.js API route (runs on Node.js server with Drizzle)
  const response = await fetch(`/api/projects?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch projects: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single project by ID.
 */
export async function getProject(id: string): Promise<Project> {
  return fetchApi<Project>(`/projects/${id}`);
}

/**
 * Fetch a single project by slug.
 */
export async function getProjectBySlug(slug: string): Promise<Project> {
  return fetchApi<Project>(`/projects/slug/${slug}`);
}

/**
 * Create a new project.
 */
export async function createProject(data: ProjectCreate): Promise<Project> {
  return fetchApi<Project>("/projects/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update an existing project.
 */
export async function updateProject(
  id: string,
  data: ProjectUpdate
): Promise<Project> {
  return fetchApi<Project>(`/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a project.
 */
export async function deleteProject(id: string): Promise<void> {
  return fetchApi<void>(`/projects/${id}`, {
    method: "DELETE",
  });
}

/**
 * Onboarding validation result.
 */
export interface OnboardingValidation {
  path_validated: boolean;
  claude_dir_exists: boolean;
  path_error: string | null;
}

/**
 * Onboard a new project with path validation.
 */
export async function onboardProject(data: {
  name: string;
  path: string;
}): Promise<Project> {
  return fetchApi<Project>("/projects/onboard", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Validate a project path without creating a project.
 *
 * Uses the local Next.js API route for filesystem validation,
 * avoiding the need for the Python backend for this operation.
 */
export async function validateProjectPath(data: {
  name: string;
  path: string;
}): Promise<OnboardingValidation> {
  // Use local Next.js API route (runs on Node.js server)
  const response = await fetch("/api/validate-path", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to validate path: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Directory entry for browsing.
 */
export interface DirectoryEntry {
  name: string;
  path: string;
  is_directory: boolean;
  has_claude_dir: boolean;
}

/**
 * Browse response with directory listing.
 */
export interface BrowseResponse {
  current_path: string;
  parent_path: string | null;
  entries: DirectoryEntry[];
  error: string | null;
}

/**
 * Browse directories for project selection.
 *
 * Uses the local Next.js API route for filesystem access,
 * avoiding the need for the Python backend for this operation.
 */
export async function browseDirectories(
  path: string = "~"
): Promise<BrowseResponse> {
  const params = new URLSearchParams();
  params.set("path", path);

  // Use local Next.js API route (runs on Node.js server)
  const response = await fetch(`/api/browse?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to browse directories: ${response.statusText}`);
  }

  return response.json();
}
