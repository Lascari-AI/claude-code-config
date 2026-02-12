/**
 * Sessions API Client
 *
 * Typed API functions for session operations.
 */

import { fetchApi } from "./api";
import type { Session, SessionSummary, SessionStatus, SessionType } from "@/types/session";

/**
 * Filter options for listing sessions.
 */
export interface SessionFilters {
  status?: SessionStatus;
  sessionType?: SessionType;
  projectId?: string;
  limit?: number;
  offset?: number;
}

/**
 * Fetch all sessions with optional filters.
 *
 * @param filters - Optional filter parameters
 */
export async function getSessions(
  filters: SessionFilters = {}
): Promise<SessionSummary[]> {
  const params = new URLSearchParams();

  if (filters.status) params.set("status_filter", filters.status);
  if (filters.sessionType) params.set("session_type", filters.sessionType);
  if (filters.projectId) params.set("project_id", filters.projectId);
  params.set("limit", String(filters.limit ?? 100));
  params.set("offset", String(filters.offset ?? 0));

  const query = params.toString();
  return fetchApi<SessionSummary[]>(`/sessions/?${query}`);
}

/**
 * Fetch a single session by ID.
 */
export async function getSession(id: string): Promise<Session> {
  return fetchApi<Session>(`/sessions/${id}`);
}

/**
 * Fetch a single session by slug.
 */
export async function getSessionBySlug(slug: string): Promise<Session> {
  return fetchApi<Session>(`/sessions/slug/${slug}`);
}

/**
 * Fetch sessions for a specific project.
 *
 * @param projectId - Project UUID
 * @param filters - Optional filter parameters
 */
export async function getProjectSessions(
  projectId: string,
  filters: Omit<SessionFilters, "projectId"> = {}
): Promise<SessionSummary[]> {
  const params = new URLSearchParams();

  if (filters.status) params.set("status_filter", filters.status);
  if (filters.sessionType) params.set("session_type", filters.sessionType);
  params.set("limit", String(filters.limit ?? 100));
  params.set("offset", String(filters.offset ?? 0));

  const query = params.toString();
  return fetchApi<SessionSummary[]>(`/projects/${projectId}/sessions?${query}`);
}
