"use client";

/**
 * ErrorMessage Component
 *
 * Reusable error message display with optional retry button.
 */

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ErrorMessageProps {
  /** Error message to display */
  message: string;
  /** Optional error title */
  title?: string;
  /** Retry callback */
  onRetry?: () => void;
  /** Additional class names */
  className?: string;
}

/**
 * Styled error message with optional retry action.
 *
 * @example
 * <ErrorMessage message="Failed to load data" onRetry={() => refetch()} />
 */
export function ErrorMessage({
  message,
  title = "Error",
  onRetry,
  className,
}: ErrorMessageProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-destructive/50 bg-destructive/10 p-6",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <ErrorIcon className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-destructive">{title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{message}</p>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={onRetry}
            >
              Try Again
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function ErrorIcon({ className }: { className?: string }) {
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
        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}
