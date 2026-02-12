"use client";

import { SessionLane } from "./SessionLane";
import type { SessionSummary, SessionPhase } from "@/types/session";
import { cn } from "@/lib/utils";

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
      <div className={cn("flex justify-center py-12", className)}>
        <LoadingSpinner />
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className={cn("text-center py-12", className)}>
        <div className="text-muted-foreground">
          <p className="text-lg font-medium">No sessions yet</p>
          <p className="text-sm mt-1">
            Sessions will appear here when you start working on this project.
          </p>
        </div>
      </div>
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

function LoadingSpinner() {
  return (
    <div className="flex items-center gap-2 text-muted-foreground">
      <svg
        className="animate-spin h-5 w-5"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span>Loading sessions...</span>
    </div>
  );
}
