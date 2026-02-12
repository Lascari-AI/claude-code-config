"use client";

/**
 * Project Detail Page
 *
 * Shows project information and swimlane view of sessions.
 */

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Swimlane } from "@/components/sessions";
import { useProjectsStore, useSessionsStore, useProjectSessions } from "@/store";
import type { SessionPhase } from "@/types/session";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const { selectedProject, isLoading: projectLoading, fetchProject } = useProjectsStore();
  const { isLoading: sessionsLoading, fetchProjectSessions } = useSessionsStore();

  // Get sessions for this project
  const sessions = useProjectSessions(selectedProject?.id ?? "");

  // Fetch project by slug
  useEffect(() => {
    if (slug) {
      // For now, we need to fetch the project to get its ID
      // In the future, we could add a fetchProjectBySlug action
      fetchProjectBySlug(slug);
    }
  }, [slug]);

  // Fetch sessions when we have the project
  useEffect(() => {
    if (selectedProject?.id) {
      fetchProjectSessions(selectedProject.id);
    }
  }, [selectedProject?.id, fetchProjectSessions]);

  // Temporary: fetch project by slug using the API directly
  async function fetchProjectBySlug(slug: string) {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/projects/slug/${slug}`);
      if (response.ok) {
        const project = await response.json();
        useProjectsStore.setState({ selectedProject: project, isLoading: false });
      }
    } catch (error) {
      console.error('Failed to fetch project:', error);
    }
  }

  // Handle phase click - navigate to session detail with phase tab
  const handlePhaseClick = (sessionSlug: string, phase: SessionPhase) => {
    router.push(`/projects/${slug}/sessions/${sessionSlug}?phase=${phase}`);
  };

  if (projectLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-1/3 mb-4" />
          <div className="h-4 bg-muted rounded w-1/2 mb-8" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!selectedProject) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold">Project not found</h2>
          <p className="text-muted-foreground mt-2">
            The project &quot;{slug}&quot; could not be found.
          </p>
          <Link href="/projects">
            <Button className="mt-4">Back to Projects</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <Link href="/projects" className="hover:underline">
            Projects
          </Link>
          <span>/</span>
          <span>{selectedProject.name}</span>
        </div>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">
                {selectedProject.name}
              </h1>
              <Badge variant={selectedProject.status === "active" ? "default" : "outline"}>
                {selectedProject.status}
              </Badge>
            </div>
            <p className="text-muted-foreground mt-1 font-mono text-sm">
              {selectedProject.path}
            </p>
          </div>
        </div>
      </div>

      {/* Sessions Swimlane */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Sessions</h2>
        <Swimlane
          sessions={sessions}
          projectSlug={slug}
          isLoading={sessionsLoading}
          onPhaseClick={handlePhaseClick}
        />
      </div>
    </div>
  );
}
