"use client";

/**
 * ProjectCard Component
 *
 * Displays a project summary in a card format with status badge.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ProjectSummary } from "@/types/project";

interface ProjectCardProps {
  project: ProjectSummary;
  onClick?: () => void;
}

/**
 * Map project status to badge variant.
 */
function getStatusVariant(
  status: string
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "active":
      return "default";
    case "onboarding":
      return "secondary";
    case "paused":
      return "outline";
    case "archived":
      return "destructive";
    case "pending":
    default:
      return "outline";
  }
}

/**
 * Format date for display.
 */
function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function ProjectCard({ project, onClick }: ProjectCardProps) {
  return (
    <Card
      className={`transition-shadow ${onClick ? "cursor-pointer hover:shadow-md" : ""}`}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg">{project.name}</CardTitle>
          <Badge variant={getStatusVariant(project.status)}>{project.status}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p className="font-mono text-xs truncate" title={project.path}>
            {project.path}
          </p>
          <p>Created {formatDate(project.created_at)}</p>
        </div>
      </CardContent>
    </Card>
  );
}
