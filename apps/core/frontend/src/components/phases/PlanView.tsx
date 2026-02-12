"use client";

import { useEffect, useState } from "react";
import { getSessionPlan } from "@/lib/sessions-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckpointCard } from "./CheckpointCard";
import { cn } from "@/lib/utils";
import type { Plan } from "@/types/plan";

interface PlanViewProps {
  sessionSlug: string;
  className?: string;
}

/**
 * Renders the plan.json content as a visual hierarchy.
 *
 * Displays checkpoints as cards with expandable task groups.
 * Handles loading and error states.
 */
export function PlanView({ sessionSlug, className }: PlanViewProps) {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPlan() {
      setIsLoading(true);
      setError(null);

      try {
        const result = await getSessionPlan(sessionSlug);
        setPlan(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load plan");
      } finally {
        setIsLoading(false);
      }
    }

    fetchPlan();
  }, [sessionSlug]);

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center py-12", className)}>
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <span className="text-sm text-muted-foreground">Loading plan...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className={cn("border-red-200", className)}>
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!plan || !plan.checkpoints?.length) {
    return (
      <Card className={cn("border-dashed", className)}>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">No plan found for this session.</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate overall progress
  const totalTasks = plan.checkpoints.reduce((sum, cp) => {
    return sum + cp.task_groups.reduce((tgSum, tg) => tgSum + tg.tasks.length, 0);
  }, 0);
  const completedTasks = plan.checkpoints.reduce((sum, cp) => {
    return sum + cp.task_groups.reduce((tgSum, tg) => {
      return tgSum + tg.tasks.filter((t) => t.status === "completed").length;
    }, 0);
  }, 0);
  const completedCheckpoints = plan.checkpoints.filter(
    (cp) => cp.status === "completed"
  ).length;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Summary header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Implementation Plan</h2>
          <p className="text-sm text-muted-foreground">
            {plan.checkpoints.length} checkpoints, {totalTasks} tasks total
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">
            {completedCheckpoints}/{plan.checkpoints.length}
          </div>
          <div className="text-xs text-muted-foreground">
            checkpoints complete
          </div>
        </div>
      </div>

      {/* Overall progress bar */}
      <div>
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
          <span>Overall Progress</span>
          <span>
            {completedTasks}/{totalTasks} tasks (
            {totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0}
            %)
          </span>
        </div>
        <div className="h-3 bg-muted rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full transition-all",
              completedTasks === totalTasks ? "bg-green-500" : "bg-blue-500"
            )}
            style={{
              width: `${totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0}%`,
            }}
          />
        </div>
      </div>

      {/* Checkpoint cards */}
      <div className="space-y-4">
        {plan.checkpoints.map((checkpoint) => (
          <CheckpointCard key={checkpoint.id} checkpoint={checkpoint} />
        ))}
      </div>
    </div>
  );
}
