/**
 * Projects Store
 *
 * Zustand store for managing project state and API interactions.
 */

import { create } from "zustand";
import type { Project, ProjectCreate, ProjectUpdate, ProjectSummary } from "@/types/project";
import * as projectsApi from "@/lib/projects-api";

interface ProjectsState {
  // State
  projects: ProjectSummary[];
  selectedProject: Project | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchProjects: (status?: string) => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  fetchProjectBySlug: (slug: string) => Promise<void>;
  createProject: (data: ProjectCreate) => Promise<Project>;
  updateProject: (id: string, data: ProjectUpdate) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
  clearError: () => void;
  clearSelectedProject: () => void;
}

export const useProjectsStore = create<ProjectsState>((set, get) => ({
  // Initial state
  projects: [],
  selectedProject: null,
  isLoading: false,
  error: null,

  // Actions
  fetchProjects: async (status?: string) => {
    set({ isLoading: true, error: null });
    try {
      const projects = await projectsApi.getProjects(status);
      set({ projects, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch projects",
        isLoading: false,
      });
    }
  },

  fetchProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.getProject(id);
      set({ selectedProject: project, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch project",
        isLoading: false,
      });
    }
  },

  fetchProjectBySlug: async (slug: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.getProjectBySlug(slug);
      set({ selectedProject: project, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch project",
        isLoading: false,
      });
    }
  },

  createProject: async (data: ProjectCreate) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.createProject(data);
      // Refresh the list after creating
      const { fetchProjects } = get();
      await fetchProjects();
      return project;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to create project";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  updateProject: async (id: string, data: ProjectUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.updateProject(id, data);
      // Update in list if present
      set((state) => ({
        projects: state.projects.map((p) =>
          p.id === id ? { ...p, ...data } : p
        ),
        selectedProject:
          state.selectedProject?.id === id ? project : state.selectedProject,
        isLoading: false,
      }));
      return project;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to update project";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  deleteProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await projectsApi.deleteProject(id);
      // Remove from list
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== id),
        selectedProject:
          state.selectedProject?.id === id ? null : state.selectedProject,
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to delete project";
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
  clearSelectedProject: () => set({ selectedProject: null }),
}));
