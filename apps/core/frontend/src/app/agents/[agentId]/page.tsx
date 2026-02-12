"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, getAgentStatusColorUtil } from "@/lib/utils";
import { Breadcrumbs, LoadingSpinner, ErrorMessage } from "@/components/shared";
import { EventTimeline } from "@/components/agents/EventTimeline";
import { getAgent } from "@/lib/agents-api";
import type { Agent } from "@/types/agent";
import { getAgentTypeLabel, getAgentStatusColor } from "@/types/agent";

/**
 * Agent detail page showing agent info and event timeline.
 *
 * Route: /agents/[agentId]
 */
export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.agentId as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAgent() {
      try {
        const data = await getAgent(agentId);
        setAgent(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch agent:", err);
        setError("Failed to load agent details.");
      } finally {
        setIsLoading(false);
      }
    }

    fetchAgent();
  }, [agentId]);

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <LoadingSpinner size="lg" centered text="Loading agent..." />
      </div>
    );
  }

  // Error state
  if (error || !agent) {
    return (
      <div className="container mx-auto py-8">
        <ErrorMessage
          title="Error"
          message={error || "Agent not found"}
          onRetry={() => router.back()}
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={[
          { label: "Session", href: "#" }, // Will go back
          { label: agent.name || getAgentTypeLabel(agent.agent_type) },
        ]}
        className="mb-4"
      />

      {/* Back navigation */}
      <Button
        variant="ghost"
        size="sm"
        className="mb-4"
        onClick={() => router.back()}
      >
        ← Back to Session
      </Button>

      {/* Agent header card */}
      <Card className="mb-8">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {agent.name || getAgentTypeLabel(agent.agent_type)}
                <Badge
                  variant="outline"
                  className={cn("ml-2", getAgentStatusColor(agent.status))}
                >
                  {agent.status}
                </Badge>
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {getAgentTypeLabel(agent.agent_type)}
                {agent.checkpoint_id && ` • Checkpoint ${agent.checkpoint_id}`}
                {agent.task_group_id && ` • Task Group ${agent.task_group_id}`}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Model */}
            <MetricCard
              label="Model"
              value={agent.model_alias || agent.model}
            />

            {/* Tokens */}
            <MetricCard
              label="Tokens"
              value={formatNumber(agent.input_tokens + agent.output_tokens)}
              subtext={`${formatNumber(agent.input_tokens)} in / ${formatNumber(agent.output_tokens)} out`}
            />

            {/* Cost */}
            <MetricCard
              label="Cost"
              value={`$${agent.cost.toFixed(4)}`}
            />

            {/* Duration */}
            {agent.started_at && agent.completed_at && (
              <MetricCard
                label="Duration"
                value={formatDuration(agent.started_at, agent.completed_at)}
              />
            )}
          </div>

          {/* Error message if failed */}
          {agent.error_message && (
            <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive font-medium">Error</p>
              <p className="text-sm text-destructive/80 mt-1">
                {agent.error_message}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Event timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Event Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <EventTimeline
            agentId={agentId}
            onViewLogDetails={(logId) => {
              // Could open a modal or navigate to log detail
              console.log("View log details:", logId);
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({
  label,
  value,
  subtext,
}: {
  label: string;
  value: string;
  subtext?: string;
}) {
  return (
    <div className="bg-muted/50 rounded-lg p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {subtext && (
        <p className="text-xs text-muted-foreground mt-0.5">{subtext}</p>
      )}
    </div>
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

// Note: LoadingSpinner, ErrorMessage, Breadcrumbs imported from shared components
