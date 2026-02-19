"use client";

/**
 * Project Detail Page
 *
 * Shows project information and swimlane view of sessions.
 */

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PlusIcon, RefreshCwIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Swimlane } from "@/components/sessions";
import { Breadcrumbs, LoadingSpinner } from "@/components/shared";
import { useProjectsStore, useSessionsStore, useProjectSessions } from "@/store";
import { getProjectStatusColor } from "@/lib/utils";
import { createSession } from "@/lib/sessions-api";
import type { SessionPhase } from "@/types/session";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const { selectedProject, isLoading: projectLoading, fetchProjectBySlug } = useProjectsStore();
  const { isLoading: sessionsLoading, fetchProjectSessions } = useSessionsStore();
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<{ synced: number; failed: number } | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Get sessions for this project
  const sessions = useProjectSessions(selectedProject?.id ?? "");

  // Sync sessions from filesystem to database
  const handleSync = useCallback(async (projectId: string) => {
    setIsSyncing(true);
    setSyncResult(null);
    try {
      const response = await fetch(`/api/projects/${projectId}/sync`, {
        method: "POST",
      });
      if (response.ok) {
        const data = await response.json();
        setSyncResult({
          synced: data.synced?.length ?? 0,
          failed: data.failed?.length ?? 0,
        });
        // Refresh sessions after sync
        fetchProjectSessions(projectId);
      }
    } catch {
      // Silently handle errors
    } finally {
      setIsSyncing(false);
      // Clear result after 3 seconds
      setTimeout(() => setSyncResult(null), 3000);
    }
  }, [fetchProjectSessions]);

  // Create a new session and navigate to it
  const handleNewSession = useCallback(async () => {
    if (!selectedProject?.path) return;

    const topic = window.prompt("Session topic (optional):");
    // User cancelled the prompt
    if (topic === null) return;

    setIsCreating(true);
    try {
      const result = await createSession(selectedProject.path, topic || undefined);
      router.push(`/projects/${slug}/sessions/${result.session_slug}`);
    } catch (err) {
      alert(`Failed to create session: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsCreating(false);
    }
  }, [selectedProject?.path, slug, router]);

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

  // Trigger background sync when project loads
  useEffect(() => {
    if (selectedProject?.id) {
      handleSync(selectedProject.id);
    }
  }, [selectedProject?.id, handleSync]);

  // Handle phase click - navigate to session detail with phase tab
  const handlePhaseClick = (sessionSlug: string, phase: SessionPhase) => {
    router.push(`/projects/${slug}/sessions/${sessionSlug}?phase=${phase}`);
  };

  if (projectLoading) {
    return (
      <div className="py-8">
        <LoadingSpinner size="lg" centered text="Loading project..." />
      </div>
    );
  }

  if (!selectedProject) {
    return (
      <div className="py-8">
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
    <div className="space-y-8 py-2">
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={[
          { label: "Projects", href: "/projects" },
          { label: selectedProject.name },
        ]}
        className="-mb-3"
      />

      {/* Header */}
      <div>
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
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Sessions</h2>
          <div className="flex items-center gap-3">
            {syncResult && (
              <span className="text-sm text-muted-foreground">
                Synced {syncResult.synced} session{syncResult.synced !== 1 ? "s" : ""}
                {syncResult.failed > 0 && (
                  <span className="text-destructive">
                    {" "}({syncResult.failed} failed)
                  </span>
                )}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => selectedProject?.id && handleSync(selectedProject.id)}
              disabled={isSyncing}
            >
              <RefreshCwIcon className={`h-4 w-4 mr-2 ${isSyncing ? "animate-spin" : ""}`} />
              {isSyncing ? "Syncing..." : "Sync Sessions"}
            </Button>
            <Button
              size="sm"
              onClick={handleNewSession}
              disabled={isCreating}
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              {isCreating ? "Creating..." : "New Session"}
            </Button>
          </div>
        </div>
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
