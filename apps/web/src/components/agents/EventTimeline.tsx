"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { EventItem } from "./EventItem";
import { getAgentLogs } from "@/lib/agents-api";
import type { AgentLogSummary, EventCategory } from "@/types/agent";

interface EventTimelineProps {
  agentId: string;
  onViewLogDetails?: (logId: string) => void;
  className?: string;
}

const EVENTS_PER_PAGE = 50;

/**
 * Displays a chronological timeline of agent events.
 *
 * Features:
 * - Category filtering (hook/response/phase)
 * - Load more pagination
 * - Expandable event details
 * - Loading and error states
 */
export function EventTimeline({
  agentId,
  onViewLogDetails,
  className,
}: EventTimelineProps) {
  const [events, setEvents] = useState<AgentLogSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<EventCategory | null>(null);

  const fetchEvents = useCallback(
    async (offset = 0, reset = false) => {
      if (reset) {
        setIsLoading(true);
      }

      try {
        const newEvents = await getAgentLogs(agentId, {
          eventCategory: categoryFilter ?? undefined,
          limit: EVENTS_PER_PAGE,
          offset,
        });

        if (reset) {
          setEvents(newEvents);
        } else {
          setEvents((prev) => [...prev, ...newEvents]);
        }

        setHasMore(newEvents.length === EVENTS_PER_PAGE);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch events:", err);
        setError("Failed to load events. Please try again.");
      } finally {
        setIsLoading(false);
      }
    },
    [agentId, categoryFilter]
  );

  // Fetch events on mount and when filter changes
  useEffect(() => {
    fetchEvents(0, true);
  }, [fetchEvents]);

  const handleLoadMore = () => {
    fetchEvents(events.length);
  };

  const handleCategoryFilter = (category: EventCategory | null) => {
    setCategoryFilter(category);
  };

  // Loading state
  if (isLoading && events.length === 0) {
    return (
      <div className={cn("flex flex-col items-center justify-center py-12", className)}>
        <LoadingSpinner />
        <p className="mt-4 text-sm text-muted-foreground">Loading events...</p>
      </div>
    );
  }

  // Error state
  if (error && events.length === 0) {
    return (
      <div className={cn("flex flex-col items-center justify-center py-12", className)}>
        <p className="text-sm text-destructive">{error}</p>
        <Button
          variant="outline"
          size="sm"
          className="mt-4"
          onClick={() => fetchEvents(0, true)}
        >
          Retry
        </Button>
      </div>
    );
  }

  // Empty state
  if (!isLoading && events.length === 0) {
    return (
      <div className={cn("flex flex-col items-center justify-center py-12", className)}>
        <div className="rounded-full bg-muted p-4 mb-4">
          <EmptyIcon className="w-8 h-8 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground">
          {categoryFilter
            ? `No ${categoryFilter} events found.`
            : "No events recorded yet."}
        </p>
        {categoryFilter && (
          <Button
            variant="link"
            size="sm"
            className="mt-2"
            onClick={() => handleCategoryFilter(null)}
          >
            Clear filter
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Filter toolbar */}
      <div className="flex items-center gap-2 mb-4 pb-4 border-b">
        <span className="text-sm text-muted-foreground mr-2">Filter:</span>
        <FilterButton
          active={categoryFilter === null}
          onClick={() => handleCategoryFilter(null)}
        >
          All
        </FilterButton>
        <FilterButton
          active={categoryFilter === "hook"}
          onClick={() => handleCategoryFilter("hook")}
          color="bg-blue-100 text-blue-700"
        >
          Hooks
        </FilterButton>
        <FilterButton
          active={categoryFilter === "response"}
          onClick={() => handleCategoryFilter("response")}
          color="bg-purple-100 text-purple-700"
        >
          Responses
        </FilterButton>
        <FilterButton
          active={categoryFilter === "phase"}
          onClick={() => handleCategoryFilter("phase")}
          color="bg-green-100 text-green-700"
        >
          Phases
        </FilterButton>

        {/* Event count */}
        <span className="ml-auto text-xs text-muted-foreground">
          {events.length} events{hasMore ? "+" : ""}
        </span>
      </div>

      {/* Timeline */}
      <div className="space-y-3 relative">
        {events.map((event, index) => (
          <EventItem
            key={event.id}
            event={event}
            onViewDetails={onViewLogDetails ? () => onViewLogDetails(event.id) : undefined}
          />
        ))}
      </div>

      {/* Load more */}
      {hasMore && (
        <div className="flex justify-center mt-6">
          <Button
            variant="outline"
            size="sm"
            onClick={handleLoadMore}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <LoadingSpinner className="w-4 h-4 mr-2" />
                Loading...
              </>
            ) : (
              "Load More Events"
            )}
          </Button>
        </div>
      )}
    </div>
  );
}

function FilterButton({
  active,
  onClick,
  color,
  children,
}: {
  active: boolean;
  onClick: () => void;
  color?: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-3 py-1 text-xs rounded-full transition-colors",
        active
          ? color || "bg-primary text-primary-foreground"
          : "bg-muted text-muted-foreground hover:bg-muted/80"
      )}
    >
      {children}
    </button>
  );
}

function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("animate-spin text-muted-foreground", className || "w-6 h-6")}
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
  );
}

function EmptyIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}
