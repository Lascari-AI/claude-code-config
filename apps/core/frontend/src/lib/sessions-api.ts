/**
 * Sessions API Client
 *
 * Typed API functions for session operations.
 * Uses local Next.js API routes with direct Drizzle database access.
 */

import type { Session, SessionSummary, SessionStatus, SessionType } from "@/types/session";
import type { Plan } from "@/types/plan";
import type { SessionState } from "@/types/session-state";
import type { AgentSummary } from "@/types/agent";

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
 * Uses local Next.js API route with direct Drizzle database access.
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

  // Use local Next.js API route (runs on Node.js server with Drizzle)
  const response = await fetch(`/api/sessions?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single session by ID.
 *
 * Uses local Next.js API route with direct Drizzle database access.
 */
export async function getSession(id: string): Promise<Session> {
  const response = await fetch(`/api/sessions/${id}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Session ${id} not found`);
    }
    throw new Error(`Failed to fetch session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single session by slug.
 *
 * Uses local Next.js API route with direct Drizzle database access.
 */
export async function getSessionBySlug(slug: string): Promise<Session> {
  const response = await fetch(`/api/sessions/slug/${slug}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Session with slug '${slug}' not found`);
    }
    throw new Error(`Failed to fetch session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch sessions for a specific project.
 *
 * Uses local Next.js API route with direct Drizzle database access.
 * Calls the sessions endpoint with a project_id filter.
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
  params.set("project_id", projectId);
  params.set("limit", String(filters.limit ?? 100));
  params.set("offset", String(filters.offset ?? 0));

  // Use local Next.js API route (runs on Node.js server with Drizzle)
  const response = await fetch(`/api/sessions?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch project sessions: ${response.statusText}`);
  }

  return response.json();
}


// ═══════════════════════════════════════════════════════════════════════════════
// SESSION ARTIFACTS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Response type for spec content.
 */
export interface SpecContent {
  content: string;
  exists: boolean;
}

/**
 * Fetch the spec.md content for a session.
 *
 * Uses local Next.js API route to read spec.md from filesystem.
 *
 * @param slug - Session slug
 * @returns Spec markdown content
 */
export async function getSessionSpec(slug: string): Promise<SpecContent> {
  const response = await fetch(`/api/sessions/${slug}/spec`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Spec not found for session '${slug}'`);
    }
    throw new Error(`Failed to fetch session spec: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch the plan.json content for a session.
 *
 * Uses local Next.js API route to read plan.json from filesystem.
 *
 * @param slug - Session slug
 * @returns Full plan object
 */
export async function getSessionPlan(slug: string): Promise<Plan> {
  const response = await fetch(`/api/sessions/${slug}/plan`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Plan not found for session '${slug}'`);
    }
    throw new Error(`Failed to fetch session plan: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch the state.json content for a session.
 *
 * Uses local Next.js API route to read state.json from filesystem.
 *
 * @param slug - Session slug
 * @returns Session state object
 */
export async function getSessionState(slug: string): Promise<SessionState> {
  const response = await fetch(`/api/sessions/${slug}/state`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`State not found for session '${slug}'`);
    }
    throw new Error(`Failed to fetch session state: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch agents for a session.
 *
 * Uses local Next.js API route with direct Drizzle database access.
 *
 * @param sessionId - Session UUID
 * @returns List of agent summaries
 */
export async function getSessionAgents(sessionId: string): Promise<AgentSummary[]> {
  const response = await fetch(`/api/agents/session/${sessionId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Session ${sessionId} not found`);
    }
    throw new Error(`Failed to fetch session agents: ${response.statusText}`);
  }

  return response.json();
}


