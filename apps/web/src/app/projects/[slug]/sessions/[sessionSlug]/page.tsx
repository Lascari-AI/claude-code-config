"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { SpecView, PlanView, BuildView, DocsView } from "@/components/phases";
import { getSessionBySlug } from "@/lib/sessions-api";
import { cn } from "@/lib/utils";
import type { Session, SessionPhase } from "@/types/session";
import { getCurrentPhase, getPhaseStatus } from "@/types/session";

/**
 * Session detail page with phase tabs.
 *
 * Route: /projects/[slug]/sessions/[sessionSlug]
 * Query params: ?phase=spec|plan|build|docs
 */
export default function SessionDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const projectSlug = params.slug as string;
  const sessionSlug = params.sessionSlug as string;

  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get active tab from URL or default to current phase
  const urlPhase = searchParams.get("phase") as SessionPhase | null;
  const [activeTab, setActiveTab] = useState<SessionPhase>(urlPhase || "spec");

  useEffect(() => {
    async function fetchSession() {
      setIsLoading(true);
      setError(null);

      try {
        const result = await getSessionBySlug(sessionSlug);
        setSession(result);

        // Default to current phase if no phase specified in URL
        if (!urlPhase) {
          const currentPhase = getCurrentPhase(result.status);
          if (currentPhase) {
            setActiveTab(currentPhase);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load session");
      } finally {
        setIsLoading(false);
      }
    }

    fetchSession();
  }, [sessionSlug, urlPhase]);

  // Update URL when tab changes
  const handleTabChange = (value: string) => {
    const phase = value as SessionPhase;
    setActiveTab(phase);
    router.push(`/projects/${projectSlug}/sessions/${sessionSlug}?phase=${phase}`, {
      scroll: false,
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <span className="text-sm text-muted-foreground">Loading session...</span>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="py-12 text-center">
        <h2 className="text-xl font-semibold text-red-600 mb-2">Error</h2>
        <p className="text-muted-foreground">{error || "Session not found"}</p>
        <Link
          href={`/projects/${projectSlug}`}
          className="text-primary hover:underline mt-4 inline-block"
        >
          ← Back to project
        </Link>
      </div>
    );
  }

  const phases: SessionPhase[] = ["spec", "plan", "build", "docs"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <Link href="/projects" className="hover:text-foreground">
            Projects
          </Link>
          <span>/</span>
          <Link href={`/projects/${projectSlug}`} className="hover:text-foreground">
            {projectSlug}
          </Link>
          <span>/</span>
          <span className="text-foreground">{session.session_slug}</span>
        </div>

        {/* Title and status */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">
              {session.title || session.session_slug}
            </h1>
            {session.description && (
              <p className="text-muted-foreground mt-1">{session.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={session.status} />
            <Badge variant="outline">{session.session_type}</Badge>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 mt-4 text-sm text-muted-foreground">
          {session.checkpoints_total > 0 && (
            <span>
              {session.checkpoints_completed}/{session.checkpoints_total} checkpoints
            </span>
          )}
          {session.total_cost > 0 && <span>${session.total_cost.toFixed(2)} cost</span>}
          <span>
            Created {new Date(session.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Phase tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          {phases.map((phase) => {
            const status = getPhaseStatus(phase, session.status);
            return (
              <TabsTrigger
                key={phase}
                value={phase}
                className="flex items-center gap-2"
              >
                <PhaseStatusDot status={status} />
                <span className="uppercase">{phase}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        <div className="mt-6">
          <TabsContent value="spec" className="mt-0">
            <SpecView sessionSlug={sessionSlug} />
          </TabsContent>

          <TabsContent value="plan" className="mt-0">
            <PlanView sessionSlug={sessionSlug} />
          </TabsContent>

          <TabsContent value="build" className="mt-0">
            <BuildView sessionId={session.id} />
          </TabsContent>

          <TabsContent value="docs" className="mt-0">
            <DocsView sessionSlug={sessionSlug} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    created: "bg-gray-100 text-gray-700",
    spec: "bg-blue-100 text-blue-700",
    spec_done: "bg-blue-100 text-blue-700",
    plan: "bg-purple-100 text-purple-700",
    plan_done: "bg-purple-100 text-purple-700",
    build: "bg-orange-100 text-orange-700",
    docs: "bg-green-100 text-green-700",
    complete: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    paused: "bg-yellow-100 text-yellow-700",
  };

  return (
    <Badge
      variant="secondary"
      className={cn(colors[status] || "bg-gray-100 text-gray-700")}
    >
      {status.replace("_", " ")}
    </Badge>
  );
}

function PhaseStatusDot({ status }: { status: "pending" | "in_progress" | "complete" }) {
  return (
    <div
      className={cn(
        "w-2 h-2 rounded-full",
        status === "complete" && "bg-green-500",
        status === "in_progress" && "bg-blue-500 animate-pulse",
        status === "pending" && "bg-gray-300"
      )}
    />
  );
}
