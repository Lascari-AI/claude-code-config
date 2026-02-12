"use client";

/**
 * ProjectsList Component
 *
 * Fetches and displays a grid of project cards.
 * Handles loading, error, and empty states using shared components.
 */

import { useEffect } from "react";
import { useProjectsStore } from "@/store";
import { ProjectCard } from "./ProjectCard";
import { LoadingSpinner, ErrorMessage, EmptyState, FolderIcon } from "@/components/shared";

export function ProjectsList() {
  const { projects, isLoading, error, fetchProjects, clearError } =
    useProjectsStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Loading state
  if (isLoading && projects.length === 0) {
    return <LoadingSpinner size="lg" centered text="Loading projects..." />;
  }

  // Error state
  if (error) {
    return (
      <ErrorMessage
        title="Error loading projects"
        message={error}
        onRetry={() => {
          clearError();
          fetchProjects();
        }}
      />
    );
  }

  // Empty state
  if (projects.length === 0) {
    return (
      <EmptyState
        icon={<FolderIcon />}
        title="No projects yet"
        description="Create your first project to get started with session workflows."
      />
    );
  }

  // Projects grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
