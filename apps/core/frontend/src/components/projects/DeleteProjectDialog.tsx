"use client";

/**
 * DeleteProjectDialog Component
 *
 * Confirmation dialog for deleting a project.
 * Warns users about the irreversible action.
 */

import { useState, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useProjectsStore } from "@/store";
import type { ProjectSummary } from "@/types/project";

interface DeleteProjectDialogProps {
  project: ProjectSummary;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

/**
 * Confirmation dialog for deleting a project.
 */
export function DeleteProjectDialog({
  project,
  open,
  onOpenChange,
  onSuccess,
}: DeleteProjectDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { deleteProject } = useProjectsStore();

  // Handle delete confirmation
  const handleDelete = useCallback(async () => {
    setIsDeleting(true);
    setError(null);

    try {
      await deleteProject(project.id);
      onOpenChange(false);
      onSuccess?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete project";
      // Check for foreign key constraint error (sessions exist)
      if (message.includes("sessions") || message.includes("foreign key") || message.includes("409")) {
        setError("Cannot delete project: it has existing sessions. Delete all sessions first.");
      } else {
        setError(message);
      }
    } finally {
      setIsDeleting(false);
    }
  }, [project.id, deleteProject, onOpenChange, onSuccess]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="text-destructive">Delete Project</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete &ldquo;{project.name}&rdquo;? This action cannot be
            undone.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="rounded-md bg-destructive/10 border border-destructive/20 p-4">
            <div className="flex gap-3">
              <WarningIcon className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-destructive">Warning</p>
                <p className="text-muted-foreground mt-1">
                  This will permanently delete the project record and all associated metadata.
                  Your actual files on disk will not be affected.
                </p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 rounded-md bg-destructive/10 border border-destructive/20 p-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <LoadingSpinner className="w-4 h-4 mr-2" />
                Deleting...
              </>
            ) : (
              "Delete Project"
            )}
          </Button>
        </DialogFooter>
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

function WarningIcon({ className }: { className?: string }) {
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
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );
}
