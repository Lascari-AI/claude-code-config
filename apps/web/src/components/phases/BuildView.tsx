"use client";

import { useEffect, useState } from "react";
import { getSessionAgents } from "@/lib/sessions-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AgentCard } from "./AgentCard";
import { cn } from "@/lib/utils";
import type { AgentSummary } from "@/types/agent";

interface BuildViewProps {
  sessionId: string;
  className?: string;
}

/**
 * Displays build phase agents for a session.
 *
 * Shows a grid of agent cards with status, metrics, and timing.
 * Handles loading and error states.
 */
export function BuildView({ sessionId, className }: BuildViewProps) {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAgents() {
      setIsLoading(true);
      setError(null);

      try {
        const result = await getSessionAgents(sessionId);
        setAgents(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load agents");
      } finally {
        setIsLoading(false);
      }
    }

    fetchAgents();
  }, [sessionId]);

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center py-12", className)}>
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <span className="text-sm text-muted-foreground">Loading agents...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className={cn("border-red-200", className)}>
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Agents</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!agents.length) {
    return (
      <Card className={cn("border-dashed", className)}>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">
            No build agents found for this session.
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Agents will appear here when the build phase starts.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Calculate summary stats
  const totalTokens = agents.reduce(
    (sum, a) => sum + a.input_tokens + a.output_tokens,
    0
  );
  const totalCost = agents.reduce((sum, a) => sum + a.cost, 0);
  const completedAgents = agents.filter((a) => a.status === "complete").length;
  const failedAgents = agents.filter((a) => a.status === "failed").length;

  // Group agents by checkpoint
  const agentsByCheckpoint = agents.reduce(
    (acc, agent) => {
      const key = agent.checkpoint_id ?? "other";
      if (!acc[key]) acc[key] = [];
      acc[key].push(agent);
      return acc;
    },
    {} as Record<string | number, AgentSummary[]>
  );

  return (
    <div className={cn("space-y-6", className)}>
      {/* Summary header */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard
          label="Total Agents"
          value={agents.length.toString()}
          subtext={`${completedAgents} complete, ${failedAgents} failed`}
        />
        <SummaryCard
          label="Total Tokens"
          value={formatNumber(totalTokens)}
          subtext="input + output"
        />
        <SummaryCard
          label="Total Cost"
          value={`$${totalCost.toFixed(2)}`}
          subtext="USD"
        />
        <SummaryCard
          label="Status"
          value={
            failedAgents > 0
              ? "Has Failures"
              : completedAgents === agents.length
                ? "All Complete"
                : "In Progress"
          }
          subtext={
            agents.filter((a) => a.status === "executing").length +
            " currently running"
          }
        />
      </div>

      {/* Agents by checkpoint */}
      {Object.entries(agentsByCheckpoint)
        .sort(([a], [b]) => {
          if (a === "other") return 1;
          if (b === "other") return -1;
          return Number(a) - Number(b);
        })
        .map(([checkpointId, checkpointAgents]) => (
          <div key={checkpointId}>
            <h3 className="text-sm font-medium text-muted-foreground mb-3">
              {checkpointId === "other"
                ? "Other Agents"
                : `Checkpoint ${checkpointId}`}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {checkpointAgents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}

interface SummaryCardProps {
  label: string;
  value: string;
  subtext: string;
}

function SummaryCard({ label, value, subtext }: SummaryCardProps) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-xs text-muted-foreground">{subtext}</div>
      </CardContent>
    </Card>
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
