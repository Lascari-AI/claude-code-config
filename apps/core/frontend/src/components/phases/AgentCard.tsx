"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AgentSummary } from "@/types/agent";
import { getAgentTypeLabel, getAgentStatusColor } from "@/types/agent";

interface AgentCardProps {
  agent: AgentSummary;
  onClick?: () => void;
  /** When true, wraps the card in a Link to /agents/[id] */
  linkToDetail?: boolean;
  className?: string;
}

/**
 * Displays an agent summary with type, status, and metrics.
 *
 * Shows:
 * - Agent type badge
 * - Status indicator
 * - Checkpoint context
 * - Token counts and cost
 * - Timing info
 */
export function AgentCard({ agent, onClick, linkToDetail = true, className }: AgentCardProps) {
  const isClickable = !!onClick || linkToDetail;

  const cardElement = (
    <Card
      className={cn(
        "transition-all",
        isClickable && "cursor-pointer hover:shadow-md hover:border-primary/50",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Agent type and name */}
            <div className="flex items-center gap-2 mb-1">
              <AgentTypeBadge type={agent.agent_type} />
              {agent.checkpoint_id && (
                <span className="text-xs text-muted-foreground">
                  Checkpoint {agent.checkpoint_id}
                </span>
              )}
            </div>

            {/* Agent name or default */}
            <h3 className="font-medium truncate">
              {agent.name || getAgentTypeLabel(agent.agent_type)}
            </h3>

            {/* Model info */}
            {agent.model_alias && (
              <span className="text-xs text-muted-foreground">
                {agent.model_alias}
              </span>
            )}
          </div>

          {/* Status badge */}
          <StatusBadge status={agent.status} />
        </div>

        {/* Metrics */}
        <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
          {/* Tokens */}
          <div className="flex items-center gap-1">
            <TokenIcon className="w-3 h-3" />
            <span>
              {formatNumber(agent.input_tokens + agent.output_tokens)} tokens
            </span>
          </div>

          {/* Cost */}
          {agent.cost > 0 && (
            <div className="flex items-center gap-1">
              <DollarIcon className="w-3 h-3" />
              <span>${agent.cost.toFixed(4)}</span>
            </div>
          )}

          {/* Duration */}
          {agent.started_at && agent.completed_at && (
            <div className="flex items-center gap-1">
              <ClockIcon className="w-3 h-3" />
              <span>{formatDuration(agent.started_at, agent.completed_at)}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  // Wrap in Link if linkToDetail is true and no custom onClick
  if (linkToDetail && !onClick) {
    return (
      <Link href={`/agents/${agent.id}`} className="block">
        {cardElement}
      </Link>
    );
  }

  return cardElement;
}

function AgentTypeBadge({ type }: { type: string }) {
  const colorMap: Record<string, string> = {
    spec: "bg-purple-100 text-purple-700",
    plan: "bg-blue-100 text-blue-700",
    "quick-plan": "bg-blue-100 text-blue-700",
    build: "bg-orange-100 text-orange-700",
    research: "bg-cyan-100 text-cyan-700",
    docs: "bg-green-100 text-green-700",
    debug: "bg-red-100 text-red-700",
  };

  return (
    <Badge
      variant="secondary"
      className={cn("text-xs", colorMap[type] || "bg-gray-100 text-gray-700")}
    >
      {type}
    </Badge>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colorClass = getAgentStatusColor(status as any);

  return (
    <span
      className={cn(
        "px-2 py-0.5 rounded-full text-xs font-medium",
        colorClass
      )}
    >
      {status}
    </span>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

function formatDuration(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const diffMs = endDate.getTime() - startDate.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) {
    return `${diffSec}s`;
  }
  const diffMin = Math.floor(diffSec / 60);
  const remainingSec = diffSec % 60;
  if (diffMin < 60) {
    return `${diffMin}m ${remainingSec}s`;
  }
  const diffHour = Math.floor(diffMin / 60);
  const remainingMin = diffMin % 60;
  return `${diffHour}h ${remainingMin}m`;
}

function TokenIcon({ className }: { className?: string }) {
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
        d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
      />
    </svg>
  );
}

function DollarIcon({ className }: { className?: string }) {
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
        d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
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
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}
