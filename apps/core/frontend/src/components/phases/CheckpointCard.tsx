"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Checkpoint, TaskGroup, Task } from "@/types/plan";
import { getCheckpointProgress, getTaskGroupProgress } from "@/types/plan";

interface CheckpointCardProps {
  checkpoint: Checkpoint;
  className?: string;
}

/**
 * Displays a checkpoint with expandable task groups.
 *
 * Shows:
 * - Checkpoint title and goal
 * - Progress bar
 * - Expandable task groups with tasks
 */
export function CheckpointCard({ checkpoint, className }: CheckpointCardProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const progress = getCheckpointProgress(checkpoint);

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className="text-xs">
                Checkpoint {checkpoint.id}
              </Badge>
              <StatusBadge status={checkpoint.status} />
            </div>
            <CardTitle className="text-lg">{checkpoint.title}</CardTitle>
            <CardDescription className="mt-1">{checkpoint.goal}</CardDescription>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>Progress</span>
            <span>{progress.completed}/{progress.total} tasks ({progress.percentage}%)</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full transition-all",
                progress.percentage === 100 ? "bg-green-500" : "bg-blue-500"
              )}
              style={{ width: `${progress.percentage}%` }}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-2">
          {checkpoint.task_groups.map((taskGroup) => (
            <TaskGroupItem
              key={taskGroup.id}
              taskGroup={taskGroup}
              isExpanded={expandedGroups.has(taskGroup.id)}
              onToggle={() => toggleGroup(taskGroup.id)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface TaskGroupItemProps {
  taskGroup: TaskGroup;
  isExpanded: boolean;
  onToggle: () => void;
}

function TaskGroupItem({ taskGroup, isExpanded, onToggle }: TaskGroupItemProps) {
  const progress = getTaskGroupProgress(taskGroup);

  return (
    <div className="border rounded-lg">
      <button
        type="button"
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/50 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-3 text-left">
          <ChevronIcon className={cn("w-4 h-4 transition-transform", isExpanded && "rotate-90")} />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">{taskGroup.id}</span>
              <span className="text-sm">{taskGroup.title}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {progress.completed}/{progress.total} tasks
            </span>
          </div>
        </div>
        <StatusBadge status={taskGroup.status} size="sm" />
      </button>

      {isExpanded && (
        <div className="border-t px-4 py-2 space-y-1">
          {taskGroup.tasks.map((task) => (
            <TaskItem key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}

interface TaskItemProps {
  task: Task;
}

function TaskItem({ task }: TaskItemProps) {
  return (
    <div className="flex items-start gap-3 py-2 pl-7">
      <TaskStatusIcon status={task.status} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{task.id}</span>
          <span className="text-sm truncate">{task.title}</span>
        </div>
        <span className="text-xs text-muted-foreground truncate block">
          {task.file_path}
        </span>
      </div>
    </div>
  );
}

function StatusBadge({
  status,
  size = "default",
}: {
  status: string;
  size?: "default" | "sm";
}) {
  const colorMap: Record<string, string> = {
    pending: "bg-gray-100 text-gray-700",
    in_progress: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
  };

  return (
    <span
      className={cn(
        "rounded-full font-medium",
        colorMap[status] || "bg-gray-100 text-gray-700",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs"
      )}
    >
      {status.replace("_", " ")}
    </span>
  );
}

function TaskStatusIcon({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <div className="w-4 h-4 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
        <CheckIcon className="w-2.5 h-2.5 text-green-600" />
      </div>
    );
  }
  if (status === "in_progress") {
    return (
      <div className="w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
      </div>
    );
  }
  return (
    <div className="w-4 h-4 rounded-full border-2 border-gray-300 flex-shrink-0 mt-0.5" />
  );
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
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
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}
