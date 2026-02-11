"use client";

/**
 * Projects Page
 *
 * Main entry point for the projects UI.
 * Displays the list of all projects.
 */

import { ProjectsList } from "@/components/projects";

export default function ProjectsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
        <p className="text-muted-foreground mt-2">
          Manage your codebases and track session workflows.
        </p>
      </div>
      <ProjectsList />
    </div>
  );
}
