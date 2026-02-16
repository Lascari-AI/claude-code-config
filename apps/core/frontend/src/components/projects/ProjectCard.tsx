"use client";

/**
 * ProjectCard Component
 *
 * Displays a project summary in a card format with status badge.
 * Clicking navigates to the project detail page.
 * Includes action menu for rename and delete operations.
 */

import { useState } from "react";
import Link from "next/link";
import { MoreVerticalIcon, PencilIcon, TrashIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { RenameProjectDialog } from "./RenameProjectDialog";
import { DeleteProjectDialog } from "./DeleteProjectDialog";
import type { ProjectSummary } from "@/types/project";

interface ProjectCardProps {
  project: ProjectSummary;
  onUpdate?: () => void;
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

export function ProjectCard({ project, onUpdate }: ProjectCardProps) {
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <>
      <Card className="transition-shadow hover:shadow-md group relative">
        <Link href={`/projects/${project.slug}`} className="block cursor-pointer">
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between gap-2">
              <CardTitle className="text-lg pr-8">{project.name}</CardTitle>
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
        </Link>

        {/* Action Menu */}
        <div className="absolute top-3 right-3">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVerticalIcon className="h-4 w-4" />
                <span className="sr-only">Project actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  setRenameOpen(true);
                }}
              >
                <PencilIcon className="mr-2 h-4 w-4" />
                Rename
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                variant="destructive"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteOpen(true);
                }}
              >
                <TrashIcon className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </Card>

      {/* Dialogs */}
      <RenameProjectDialog
        project={project}
        open={renameOpen}
        onOpenChange={setRenameOpen}
        onSuccess={onUpdate}
      />
      <DeleteProjectDialog
        project={project}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onSuccess={onUpdate}
      />
    </>
  );
}
