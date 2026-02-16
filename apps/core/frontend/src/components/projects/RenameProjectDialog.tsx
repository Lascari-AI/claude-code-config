"use client";

/**
 * RenameProjectDialog Component
 *
 * Dialog for renaming an existing project.
 * Updates both name and slug on submit.
 */

import { useState, useCallback, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useProjectsStore } from "@/store";
import type { ProjectSummary } from "@/types/project";

interface RenameProjectDialogProps {
  project: ProjectSummary;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

/**
 * Generate a URL-safe slug from a project name.
 */
function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

/**
 * Dialog for renaming a project.
 */
export function RenameProjectDialog({
  project,
  open,
  onOpenChange,
  onSuccess,
}: RenameProjectDialogProps) {
  const [name, setName] = useState(project.name);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { updateProject, fetchProjects } = useProjectsStore();

  // Reset form when dialog opens with new project
  useEffect(() => {
    if (open) {
      setName(project.name);
      setError(null);
      setIsSubmitting(false);
    }
  }, [open, project.name]);

  // Handle form submission
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      const trimmedName = name.trim();
      if (!trimmedName) {
        setError("Project name is required");
        return;
      }

      if (trimmedName === project.name) {
        onOpenChange(false);
        return;
      }

      setIsSubmitting(true);
      setError(null);

      try {
        const newSlug = generateSlug(trimmedName);
        await updateProject(project.id, {
          name: trimmedName,
          slug: newSlug,
        });
        await fetchProjects();
        onOpenChange(false);
        onSuccess?.();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to rename project"
        );
      } finally {
        setIsSubmitting(false);
      }
    },
    [name, project.id, project.name, updateProject, fetchProjects, onOpenChange, onSuccess]
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Rename Project</DialogTitle>
            <DialogDescription>
              Enter a new name for &ldquo;{project.name}&rdquo;.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="rename-name">Project Name</Label>
              <Input
                id="rename-name"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setError(null);
                }}
                placeholder="Enter new project name"
                disabled={isSubmitting}
                autoFocus
              />
              {name.trim() && name.trim() !== project.name && (
                <p className="text-xs text-muted-foreground">
                  New URL: /projects/{generateSlug(name.trim())}
                </p>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !name.trim() || name.trim() === project.name}
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Renaming...
                </>
              ) : (
                "Rename"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("animate-spin", className)}
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
