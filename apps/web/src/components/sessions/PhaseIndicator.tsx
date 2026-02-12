"use client";

import { cn } from "@/lib/utils";
import type { SessionPhase, PhaseStatus } from "@/types/session";

interface PhaseIndicatorProps {
  phase: SessionPhase;
  status: PhaseStatus;
  onClick?: () => void;
  className?: string;
}

const phaseLabels: Record<SessionPhase, string> = {
  spec: "SPEC",
  plan: "PLAN",
  build: "BUILD",
  docs: "DOCS",
};

/**
 * Visual indicator for a single phase in the swimlane.
 *
 * States:
 * - complete: Green checkmark
 * - in_progress: Blue pulsing dot
 * - pending: Gray empty circle
 */
export function PhaseIndicator({
  phase,
  status,
  onClick,
  className,
}: PhaseIndicatorProps) {
  const isClickable = !!onClick;

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!isClickable}
      className={cn(
        "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors",
        isClickable && "hover:bg-muted cursor-pointer",
        !isClickable && "cursor-default",
        className
      )}
    >
      {/* Status indicator */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center border-2",
          status === "complete" && "bg-green-100 border-green-500 text-green-600",
          status === "in_progress" && "bg-blue-100 border-blue-500 text-blue-600",
          status === "pending" && "bg-gray-100 border-gray-300 text-gray-400"
        )}
      >
        {status === "complete" && (
          <CheckIcon className="w-4 h-4" />
        )}
        {status === "in_progress" && (
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
        )}
        {status === "pending" && (
          <div className="w-3 h-3 rounded-full border-2 border-gray-300" />
        )}
      </div>

      {/* Phase label */}
      <span
        className={cn(
          "text-xs font-medium",
          status === "complete" && "text-green-600",
          status === "in_progress" && "text-blue-600",
          status === "pending" && "text-gray-400"
        )}
      >
        {phaseLabels[phase]}
      </span>
    </button>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={3}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}
