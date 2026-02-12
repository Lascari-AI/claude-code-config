"use client";

/**
 * OnboardingDialog Component
 *
 * Dialog for onboarding a new project with path validation.
 * Validates the project path and checks for .claude directory.
 */

import { useState, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  onboardProject,
  validateProjectPath,
  type OnboardingValidation,
} from "@/lib/projects-api";
import { useProjectsStore } from "@/store";
import { DirectoryBrowser } from "./DirectoryBrowser";

interface OnboardingDialogProps {
  trigger?: React.ReactNode;
  onSuccess?: () => void;
}

/**
 * Dialog for onboarding a new project.
 *
 * Workflow:
 * 1. User enters project name and path
 * 2. Path is validated (exists + .claude directory check)
 * 3. Validation status is shown
 * 4. User can proceed to create project
 */
export function OnboardingDialog({ trigger, onSuccess }: OnboardingDialogProps) {
  const [open, setOpen] = useState(false);
  const [browserOpen, setBrowserOpen] = useState(false);
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validation, setValidation] = useState<OnboardingValidation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { fetchProjects } = useProjectsStore();

  // Handle path selection from browser
  const handlePathSelect = useCallback((selectedPath: string) => {
    setPath(selectedPath);
    setValidation(null);
    // Auto-validate after selection
    setTimeout(() => {
      validateProjectPath({ name: name || "temp", path: selectedPath }).then(
        (result) => {
          setValidation(result);
          if (result.path_error) {
            setError(result.path_error);
          }
        }
      );
    }, 100);
  }, [name]);

  // Reset form when dialog closes
  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
    if (!newOpen) {
      setName("");
      setPath("");
      setValidation(null);
      setError(null);
      setIsValidating(false);
      setIsSubmitting(false);
    }
  };

  // Validate path
  const handleValidate = useCallback(async () => {
    if (!path.trim()) {
      setError("Path is required");
      return;
    }

    setIsValidating(true);
    setError(null);

    try {
      const result = await validateProjectPath({ name: name || "temp", path });
      setValidation(result);

      if (result.path_error) {
        setError(result.path_error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setIsValidating(false);
    }
  }, [name, path]);

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError("Project name is required");
      return;
    }
    if (!path.trim()) {
      setError("Path is required");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onboardProject({ name, path });
      await fetchProjects();
      handleOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Project
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Onboard New Project</DialogTitle>
            <DialogDescription>
              Add a codebase to manage with the session workflow system.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Project Name */}
            <div className="grid gap-2">
              <Label htmlFor="name">Project Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Awesome Project"
                disabled={isSubmitting}
              />
            </div>

            {/* Project Path */}
            <div className="grid gap-2">
              <Label htmlFor="path">Project Path</Label>
              <div className="flex gap-2">
                <Input
                  id="path"
                  value={path}
                  onChange={(e) => {
                    setPath(e.target.value);
                    setValidation(null);
                  }}
                  placeholder="/path/to/your/project"
                  className="font-mono text-sm flex-1"
                  disabled={isSubmitting}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setBrowserOpen(true)}
                  disabled={isSubmitting}
                >
                  <FolderSearchIcon className="w-4 h-4" />
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleValidate}
                  disabled={isValidating || isSubmitting || !path.trim()}
                >
                  {isValidating ? (
                    <LoadingSpinner className="w-4 h-4" />
                  ) : (
                    "Validate"
                  )}
                </Button>
              </div>
            </div>

            {/* Directory Browser Dialog */}
            <DirectoryBrowser
              open={browserOpen}
              onOpenChange={setBrowserOpen}
              onSelect={handlePathSelect}
              initialPath={path || "~"}
            />

            {/* Validation Results */}
            {validation && (
              <div className="rounded-lg border p-4 space-y-3">
                <h4 className="text-sm font-medium">Validation Results</h4>
                <div className="space-y-2">
                  <ValidationItem
                    label="Path exists"
                    valid={validation.path_validated}
                  />
                  <ValidationItem
                    label=".claude directory"
                    valid={validation.claude_dir_exists}
                    warning={!validation.claude_dir_exists && validation.path_validated}
                    warningText="Optional - project will be marked as 'onboarding'"
                  />
                </div>
              </div>
            )}

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
              onClick={() => handleOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !name.trim() || !path.trim()}>
              {isSubmitting ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Creating...
                </>
              ) : (
                "Create Project"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Validation result item with icon
 */
function ValidationItem({
  label,
  valid,
  warning = false,
  warningText,
}: {
  label: string;
  valid: boolean;
  warning?: boolean;
  warningText?: string;
}) {
  return (
    <div className="flex items-start gap-2">
      <div className="flex-shrink-0 mt-0.5">
        {valid ? (
          <CheckIcon className="w-4 h-4 text-green-600" />
        ) : warning ? (
          <WarningIcon className="w-4 h-4 text-yellow-600" />
        ) : (
          <XIcon className="w-4 h-4 text-red-600" />
        )}
      </div>
      <div>
        <span className={cn("text-sm", valid ? "text-foreground" : "text-muted-foreground")}>
          {label}
        </span>
        {warning && warningText && (
          <p className="text-xs text-muted-foreground mt-0.5">{warningText}</p>
        )}
      </div>
    </div>
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

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
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
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
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

function FolderSearchIcon({ className }: { className?: string }) {
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
        d="M3 7v10a2 2 0 002 2h6m4 0h4a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
      />
      <circle cx="17" cy="17" r="3" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-1.5-1.5" />
    </svg>
  );
}
