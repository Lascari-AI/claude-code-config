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
