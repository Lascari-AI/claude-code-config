"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { EventItem } from "./EventItem";
import { getAgentLogs } from "@/lib/agents-api";
import { LoadingSpinner, ErrorMessage, EmptyState, ClockIcon } from "@/components/shared";
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
      <div className={cn("py-12", className)}>
        <LoadingSpinner size="lg" centered text="Loading events..." />
      </div>
    );
  }

  // Error state
  if (error && events.length === 0) {
    return (
      <ErrorMessage
        title="Error Loading Events"
        message={error}
        onRetry={() => fetchEvents(0, true)}
        className={className}
      />
    );
  }

  // Empty state
  if (!isLoading && events.length === 0) {
    return (
      <div className={className}>
        <EmptyState
          icon={<ClockIcon />}
          title={categoryFilter ? `No ${categoryFilter} events` : "No events yet"}
          description={
            categoryFilter
              ? `No ${categoryFilter} events found. Try a different filter.`
              : "Events will appear here as the agent executes."
          }
          actionLabel={categoryFilter ? "Clear filter" : undefined}
          onAction={categoryFilter ? () => handleCategoryFilter(null) : undefined}
        />
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
                <LoadingSpinner size="sm" className="mr-2" />
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

// Note: LoadingSpinner, ErrorMessage, EmptyState, and ClockIcon are imported from shared components
