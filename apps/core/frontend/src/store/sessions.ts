/**
 * Sessions Store
 *
 * Zustand store for managing session state and API interactions.
 */

import { create } from "zustand";
import type { Session, SessionSummary } from "@/types/session";
import * as sessionsApi from "@/lib/sessions-api";

interface SessionsState {
  // State
  sessionsByProject: Map<string, SessionSummary[]>;
  currentSession: Session | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchProjectSessions: (projectId: string) => Promise<void>;
  fetchSession: (id: string) => Promise<void>;
  fetchSessionBySlug: (slug: string) => Promise<void>;
  setCurrentSession: (session: Session | null) => void;
  clearError: () => void;
}

export const useSessionsStore = create<SessionsState>((set, get) => ({
  // Initial state
  sessionsByProject: new Map(),
  currentSession: null,
  isLoading: false,
  error: null,

  // Actions
  fetchProjectSessions: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const sessions = await sessionsApi.getProjectSessions(projectId);
      set((state) => {
        const newMap = new Map(state.sessionsByProject);
        newMap.set(projectId, sessions);
        return { sessionsByProject: newMap, isLoading: false };
      });
    } catch (error) {
      set({
        error:
          error instanceof Error
            ? error.message
            : "Failed to fetch project sessions",
        isLoading: false,
      });
    }
  },

  fetchSession: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const session = await sessionsApi.getSession(id);
      set({ currentSession: session, isLoading: false });
    } catch (error) {
      set({
        error:
          error instanceof Error ? error.message : "Failed to fetch session",
        isLoading: false,
      });
    }
  },

  fetchSessionBySlug: async (slug: string) => {
    set({ isLoading: true, error: null });
    try {
      const session = await sessionsApi.getSessionBySlug(slug);
      set({ currentSession: session, isLoading: false });
    } catch (error) {
      set({
        error:
          error instanceof Error ? error.message : "Failed to fetch session",
        isLoading: false,
      });
    }
  },

  setCurrentSession: (session: Session | null) => {
    set({ currentSession: session });
  },

  clearError: () => set({ error: null }),
}));

/**
 * Stable empty array to avoid creating new references on every render.
 */
const EMPTY_SESSIONS: SessionSummary[] = [];

/**
 * Selector to get sessions for a specific project.
 */
export function useProjectSessions(projectId: string): SessionSummary[] {
  return useSessionsStore((state) => state.sessionsByProject.get(projectId) ?? EMPTY_SESSIONS);
}
