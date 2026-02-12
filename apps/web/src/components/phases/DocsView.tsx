"use client";

import { useEffect, useState } from "react";
import { getSessionState } from "@/lib/sessions-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { SessionState, DocUpdate } from "@/types/session-state";

interface DocsViewProps {
  sessionSlug: string;
  className?: string;
}

/**
 * Displays documentation updates from a session.
 *
 * Shows a list of doc updates from state.json with file paths and actions.
 * Handles loading and error states.
 */
export function DocsView({ sessionSlug, className }: DocsViewProps) {
  const [state, setState] = useState<SessionState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchState() {
      setIsLoading(true);
      setError(null);

      try {
        const result = await getSessionState(sessionSlug);
        setState(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load state");
      } finally {
        setIsLoading(false);
      }
    }

    fetchState();
  }, [sessionSlug]);

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center py-12", className)}>
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <span className="text-sm text-muted-foreground">Loading documentation updates...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className={cn("border-red-200", className)}>
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Documentation</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const docUpdates = state?.doc_updates || [];

  if (!docUpdates.length) {
    return (
      <Card className={cn("border-dashed", className)}>
        <CardContent className="py-12 text-center">
          <DocIcon className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">
            No documentation updates for this session.
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Documentation updates will appear here after the docs phase completes.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Group by action type
  const created = docUpdates.filter((d) => d.action === "created");
  const updated = docUpdates.filter((d) => d.action === "updated");
  const deleted = docUpdates.filter((d) => d.action === "deleted");

  return (
    <div className={cn("space-y-6", className)}>
      {/* Summary */}
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">Documentation Updates</h2>
        <div className="flex items-center gap-2">
          {created.length > 0 && (
            <Badge variant="secondary" className="bg-green-100 text-green-700">
              {created.length} created
            </Badge>
          )}
          {updated.length > 0 && (
            <Badge variant="secondary" className="bg-blue-100 text-blue-700">
              {updated.length} updated
            </Badge>
          )}
          {deleted.length > 0 && (
            <Badge variant="secondary" className="bg-red-100 text-red-700">
              {deleted.length} deleted
            </Badge>
          )}
        </div>
      </div>

      {/* Doc updates list */}
      <div className="space-y-2">
        {docUpdates.map((doc, index) => (
          <DocUpdateItem key={`${doc.file}-${index}`} docUpdate={doc} />
        ))}
      </div>
    </div>
  );
}

interface DocUpdateItemProps {
  docUpdate: DocUpdate;
}

function DocUpdateItem({ docUpdate }: DocUpdateItemProps) {
  const actionColors: Record<string, string> = {
    created: "text-green-600",
    updated: "text-blue-600",
    deleted: "text-red-600",
  };

  const actionIcons: Record<string, React.ReactNode> = {
    created: <PlusIcon className="w-4 h-4" />,
    updated: <EditIcon className="w-4 h-4" />,
    deleted: <TrashIcon className="w-4 h-4" />,
  };

  return (
    <Card>
      <CardContent className="py-3">
        <div className="flex items-start gap-3">
          <div className={cn("mt-0.5", actionColors[docUpdate.action])}>
            {actionIcons[docUpdate.action]}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-mono text-sm truncate">{docUpdate.file}</div>
            {docUpdate.description && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {docUpdate.description}
              </p>
            )}
          </div>
          <Badge
            variant="outline"
            className={cn("text-xs", actionColors[docUpdate.action])}
          >
            {docUpdate.action}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function DocIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
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

function EditIcon({ className }: { className?: string }) {
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
        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
      />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
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
        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
      />
    </svg>
  );
}
