"use client";

import { SessionLane } from "./SessionLane";
import type { SessionSummary, SessionPhase } from "@/types/session";
import { cn } from "@/lib/utils";
import { LoadingSpinner, EmptyState, InboxIcon } from "@/components/shared";

interface SwimlaneProps {
  sessions: SessionSummary[];
  projectSlug: string;
  isLoading?: boolean;
  onPhaseClick?: (sessionSlug: string, phase: SessionPhase) => void;
  className?: string;
}

/**
 * Swimlane view showing multiple session lanes stacked vertically.
 *
 * Displays:
 * - Loading spinner when fetching
 * - Empty state when no sessions
 * - Vertical list of SessionLane components
 */
export function Swimlane({
  sessions,
  projectSlug,
  isLoading = false,
  onPhaseClick,
  className,
}: SwimlaneProps) {
  if (isLoading) {
    return (
      <div className={cn("py-12", className)}>
        <LoadingSpinner centered text="Loading sessions..." />
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <EmptyState
        icon={<InboxIcon />}
        title="No sessions yet"
        description="Sessions will appear here when you start working on this project."
        className={className}
      />
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {sessions.map((session) => (
        <SessionLane
          key={session.id}
          session={session}
          projectSlug={projectSlug}
          onPhaseClick={
            onPhaseClick
              ? (phase) => onPhaseClick(session.session_slug, phase)
              : undefined
          }
        />
      ))}
    </div>
  );
}
