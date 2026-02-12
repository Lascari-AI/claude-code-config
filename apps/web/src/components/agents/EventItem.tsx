"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AgentLogSummary } from "@/types/agent";
import {
  getEventCategoryColor,
  getEventTypeColor,
  getEventCategoryLabel,
} from "@/types/agent";

interface EventItemProps {
  event: AgentLogSummary;
  onViewDetails?: () => void;
  className?: string;
}

/**
 * Displays a single event in the timeline.
 *
 * Renders differently based on event category:
 * - hook: Tool use events with tool name and duration
 * - response: Text/thinking blocks with content preview
 * - phase: Phase transition markers
 */
export function EventItem({ event, onViewDetails, className }: EventItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasContent = !!event.content || !!event.summary;

  return (
    <div className={cn("relative", className)}>
      {/* Timeline connector line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

      {/* Timeline dot */}
      <div
        className={cn(
          "absolute left-2 top-3 w-5 h-5 rounded-full border-2 bg-background flex items-center justify-center",
          getEventCategoryBorderColor(event.event_category)
        )}
      >
        <EventIcon category={event.event_category} eventType={event.event_type} />
      </div>

      {/* Event card */}
      <Card
        className={cn(
          "ml-10 transition-all",
          hasContent && "cursor-pointer hover:shadow-sm",
          isExpanded && "ring-1 ring-primary/20"
        )}
        onClick={() => hasContent && setIsExpanded(!isExpanded)}
      >
        <CardContent className="py-3 px-4">
          {/* Header row */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              {/* Event type badge */}
              <Badge
                variant="outline"
                className={cn("text-xs shrink-0", getEventTypeColor(event.event_type))}
              >
                {event.event_type}
              </Badge>

              {/* Tool name if present */}
              {event.tool_name && (
                <span className="text-sm font-medium text-foreground truncate">
                  {event.tool_name}
                </span>
              )}

              {/* Summary preview */}
              {!event.tool_name && event.summary && (
                <span className="text-sm text-muted-foreground truncate">
                  {event.summary}
                </span>
              )}
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground shrink-0">
              {/* Duration */}
              {event.duration_ms !== null && (
                <span className="font-mono">
                  {formatDuration(event.duration_ms)}
                </span>
              )}

              {/* Timestamp */}
              <span>{formatTime(event.timestamp)}</span>

              {/* Expand indicator */}
              {hasContent && (
                <span className="text-muted-foreground/50">
                  {isExpanded ? "▼" : "▶"}
                </span>
              )}
            </div>
          </div>

          {/* Expanded content */}
          {isExpanded && hasContent && (
            <div className="mt-3 pt-3 border-t">
              {/* Summary */}
              {event.summary && (
                <p className="text-sm text-muted-foreground mb-2">
                  {event.summary}
                </p>
              )}

              {/* Content preview */}
              {event.content && (
                <div className="bg-muted/50 rounded p-2 max-h-48 overflow-y-auto">
                  <pre className="text-xs text-foreground whitespace-pre-wrap font-mono">
                    {truncateContent(event.content, 500)}
                  </pre>
                </div>
              )}

              {/* View full details link */}
              {onViewDetails && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewDetails();
                  }}
                  className="mt-2 text-xs text-primary hover:underline"
                >
                  View full details →
                </button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function EventIcon({
  category,
  eventType,
}: {
  category: string;
  eventType: string;
}) {
  // Tool events
  if (eventType === "PreToolUse" || eventType === "PostToolUse") {
    return <ToolIcon className="w-3 h-3 text-cyan-600" />;
  }
  if (eventType === "ToolError") {
    return <ErrorIcon className="w-3 h-3 text-red-600" />;
  }
  // Phase events
  if (category === "phase") {
    return <PhaseIcon className="w-3 h-3 text-green-600" />;
  }
  // Response events
  if (category === "response") {
    return <TextIcon className="w-3 h-3 text-purple-600" />;
  }
  // Default
  return <DotIcon className="w-2 h-2 text-gray-400" />;
}

function getEventCategoryBorderColor(category: string): string {
  const colors: Record<string, string> = {
    hook: "border-blue-300",
    response: "border-purple-300",
    phase: "border-green-300",
  };
  return colors[category] || "border-gray-300";
}

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  const seconds = ms / 1000;
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = (seconds % 60).toFixed(0);
  return `${minutes}m ${remainingSeconds}s`;
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function truncateContent(content: string, maxLength: number): string {
  if (content.length <= maxLength) {
    return content;
  }
  return content.slice(0, maxLength) + "...";
}

// Icons

function ToolIcon({ className }: { className?: string }) {
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
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  );
}

function ErrorIcon({ className }: { className?: string }) {
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
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );
}

function PhaseIcon({ className }: { className?: string }) {
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
        d="M9 5l7 7-7 7"
      />
    </svg>
  );
}

function TextIcon({ className }: { className?: string }) {
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
        d="M4 6h16M4 12h16M4 18h7"
      />
    </svg>
  );
}

function DotIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 8 8" fill="currentColor">
      <circle cx="4" cy="4" r="4" />
    </svg>
  );
}
