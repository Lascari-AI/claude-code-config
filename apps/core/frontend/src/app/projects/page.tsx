"use client";

/**
 * Projects Page
 *
 * Main entry point for the projects UI.
 * Displays the list of all projects with onboarding capability.
 */

import { ProjectsList, OnboardingDialog } from "@/components/projects";

export default function ProjectsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground mt-2">
            Manage your codebases and track session workflows.
          </p>
        </div>
        <OnboardingDialog />
      </div>
      <ProjectsList />
    </div>
  );
}
