"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SpecView, PlanView, BuildView, DocsView } from "@/components/phases";
import { ChatPanel } from "@/components/chat";
import { DeleteSessionDialog } from "@/components/sessions";
import { Breadcrumbs, LoadingSpinner, ErrorMessage } from "@/components/shared";
import { getSessionBySlug } from "@/lib/sessions-api";
import { cn, getSessionStatusColor, getPhaseStatusColor } from "@/lib/utils";
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
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

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
      <div className="py-24">
        <LoadingSpinner size="lg" centered text="Loading session..." />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="py-12">
        <ErrorMessage
          title="Error"
          message={error || "Session not found"}
          onRetry={() => window.location.reload()}
        />
        <div className="text-center mt-4">
          <Link
            href={`/projects/${projectSlug}`}
            className="text-primary hover:underline"
          >
            ← Back to project
          </Link>
        </div>
      </div>
    );
  }

  const phases: SessionPhase[] = ["spec", "plan", "build", "docs"];

  return (
    <div className="flex h-[calc(100vh-theme(spacing.6)*2)] flex-col">
      {/* Header bar */}
      <div className="shrink-0 space-y-2 pb-4">
        <Breadcrumbs
          items={[
            { label: "Projects", href: "/projects" },
            { label: projectSlug, href: `/projects/${projectSlug}` },
            { label: session.title || session.session_slug },
          ]}
        />

        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <h1 className="text-xl font-bold truncate">
              {session.title || session.session_slug}
            </h1>
            <StatusBadge status={session.status} />
            <Badge variant="outline">{session.session_type}</Badge>
          </div>
          <div className="flex items-center gap-4 shrink-0 text-sm text-muted-foreground">
            {session.checkpoints_total > 0 && (
              <span>
                {session.checkpoints_completed}/{session.checkpoints_total} checkpoints
              </span>
            )}
            {session.total_cost > 0 && <span>${session.total_cost.toFixed(2)}</span>}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-destructive"
              onClick={() => setShowDeleteDialog(true)}
              title="Delete session"
            >
              <TrashIcon className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Delete Session Dialog */}
      <DeleteSessionDialog
        session={session}
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onSuccess={() => router.push(`/projects/${projectSlug}`)}
      />

      {/* Main content: artifact panel + chat — fills remaining height */}
      <div className="flex min-h-0 flex-1 gap-6">
        {/* Artifact tabs — scrollable interior */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <Tabs value={activeTab} onValueChange={handleTabChange} className="flex min-h-0 flex-1 flex-col">
            <TabsList className="grid w-full shrink-0 grid-cols-4">
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

            <div className="mt-4 min-h-0 flex-1 overflow-y-auto rounded-lg border bg-card p-6">
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

        {/* Chat panel — wider, fills full height */}
        <div className="w-[480px] shrink-0 border-l border-border/50 pl-6">
          <ChatPanel sessionSlug={sessionSlug} className="h-full" />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <Badge
      variant="secondary"
      className={getSessionStatusColor(status)}
    >
      {status.replace("_", " ")}
    </Badge>
  );
}

function PhaseStatusDot({ status }: { status: "pending" | "in_progress" | "complete" }) {
  return (
    <div
      className={cn("w-2 h-2 rounded-full", getPhaseStatusColor(status))}
    />
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
      />
    </svg>
  );
}
