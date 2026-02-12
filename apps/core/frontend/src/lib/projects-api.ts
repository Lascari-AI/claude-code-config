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

  const query = params.toString();
  return fetchApi<ProjectSummary[]>(`/projects/?${query}`);
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
 */
export async function validateProjectPath(data: {
  name: string;
  path: string;
}): Promise<OnboardingValidation> {
  return fetchApi<OnboardingValidation>("/projects/validate-path", {
    method: "POST",
    body: JSON.stringify(data),
  });
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
 */
export async function browseDirectories(
  path: string = "~"
): Promise<BrowseResponse> {
  const params = new URLSearchParams();
  params.set("path", path);
  return fetchApi<BrowseResponse>(`/projects/browse?${params.toString()}`);
}
