"use client";

import { PhaseIndicator } from "./PhaseIndicator";
import { Card, CardContent } from "@/components/ui/card";
import type { SessionSummary, SessionPhase, SessionStatus } from "@/types/session";
import { getPhaseStatus } from "@/types/session";
import { cn, getSessionStatusColor, getPhaseStatusColor } from "@/lib/utils";

interface SessionLaneProps {
  session: SessionSummary;
  projectSlug: string;
  onPhaseClick?: (phase: SessionPhase) => void;
  className?: string;
}

const phases: SessionPhase[] = ["spec", "plan", "build", "docs"];

/**
 * Horizontal lane showing a session's progress through phases.
 *
 * Displays:
 * - Session title/slug
 * - Four phase indicators: SPEC → PLAN → BUILD → DOCS
 * - Progress line connecting phases
 */
export function SessionLane({
  session,
  projectSlug,
  onPhaseClick,
  className,
}: SessionLaneProps) {
  const displayTitle = session.title || session.session_slug;

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardContent className="py-4">
        <div className="flex items-center gap-4">
          {/* Session info */}
          <div className="min-w-[200px] flex-shrink-0">
            <h3 className="font-medium text-sm truncate" title={displayTitle}>
              {displayTitle}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <StatusBadge status={session.status} />
              {session.checkpoints_total > 0 && (
                <span className="text-xs text-muted-foreground">
                  {session.checkpoints_completed}/{session.checkpoints_total} checkpoints
                </span>
              )}
            </div>
          </div>

          {/* Phase progress */}
          <div className="flex items-center flex-1 justify-center gap-1">
            {phases.map((phase, index) => (
              <div key={phase} className="flex items-center">
                <PhaseIndicator
                  phase={phase}
                  status={getPhaseStatus(phase, session.status)}
                  href={`/projects/${projectSlug}/sessions/${session.session_slug}?phase=${phase}`}
                  onClick={onPhaseClick ? () => onPhaseClick(phase) : undefined}
                />
                {index < phases.length - 1 && (
                  <Arrow status={getPhaseStatus(phase, session.status)} />
                )}
              </div>
            ))}
          </div>

          {/* Cost (optional) */}
          {session.total_cost > 0 && (
            <div className="text-right text-xs text-muted-foreground flex-shrink-0 w-20">
              ${session.total_cost.toFixed(2)}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: SessionStatus }) {
  return (
    <span
      className={cn(
        "px-2 py-0.5 rounded-full text-xs font-medium",
        getSessionStatusColor(status)
      )}
    >
      {status.replace("_", " ")}
    </span>
  );
}

function Arrow({ status }: { status: "complete" | "in_progress" | "pending" }) {
  return (
    <div
      className={cn(
        "w-6 h-0.5 mx-1 transition-colors",
        status === "complete" && "bg-green-400",
        status === "in_progress" && "bg-blue-400",
        status === "pending" && "bg-gray-200 dark:bg-gray-600"
      )}
    />
  );
}
