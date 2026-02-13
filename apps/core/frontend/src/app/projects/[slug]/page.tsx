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
import { Breadcrumbs, LoadingSpinner } from "@/components/shared";
import { useProjectsStore, useSessionsStore, useProjectSessions } from "@/store";
import { getProjectStatusColor } from "@/lib/utils";
import type { SessionPhase } from "@/types/session";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const { selectedProject, isLoading: projectLoading, fetchProjectBySlug } = useProjectsStore();
  const { isLoading: sessionsLoading, fetchProjectSessions } = useSessionsStore();

  // Get sessions for this project
  const sessions = useProjectSessions(selectedProject?.id ?? "");

  // Fetch project by slug
  useEffect(() => {
    if (slug) {
      fetchProjectBySlug(slug);
    }
  }, [slug, fetchProjectBySlug]);

  // Fetch sessions when we have the project
  useEffect(() => {
    if (selectedProject?.id) {
      fetchProjectSessions(selectedProject.id);
    }
  }, [selectedProject?.id, fetchProjectSessions]);

  // Handle phase click - navigate to session detail with phase tab
  const handlePhaseClick = (sessionSlug: string, phase: SessionPhase) => {
    router.push(`/projects/${slug}/sessions/${sessionSlug}?phase=${phase}`);
  };

  if (projectLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <LoadingSpinner size="lg" centered text="Loading project..." />
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
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={[
          { label: "Projects", href: "/projects" },
          { label: selectedProject.name },
        ]}
        className="mb-4"
      />

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">
                {selectedProject.name}
              </h1>
              <Badge
                variant="secondary"
                className={getProjectStatusColor(selectedProject.status)}
              >
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
