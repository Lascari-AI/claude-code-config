"use client";

/**
 * ProjectsList Component
 *
 * Fetches and displays a grid of project cards.
 * Handles loading, error, and empty states.
 */

import { useEffect } from "react";
import { useProjectsStore } from "@/store";
import { ProjectCard } from "./ProjectCard";

export function ProjectsList() {
  const { projects, isLoading, error, fetchProjects, clearError } =
    useProjectsStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Loading state
  if (isLoading && projects.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading projects...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
        <h3 className="font-semibold text-destructive mb-2">
          Error loading projects
        </h3>
        <p className="text-sm text-muted-foreground mb-4">{error}</p>
        <button
          onClick={() => {
            clearError();
            fetchProjects();
          }}
          className="text-sm text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  // Empty state
  if (projects.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-12 text-center">
        <h3 className="font-semibold mb-2">No projects yet</h3>
        <p className="text-sm text-muted-foreground">
          Create your first project to get started.
        </p>
      </div>
    );
  }

  // Projects grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          project={project}
          onClick={() => {
            // TODO: Navigate to project detail page
            console.log("Navigate to project:", project.slug);
          }}
        />
      ))}
    </div>
  );
}
