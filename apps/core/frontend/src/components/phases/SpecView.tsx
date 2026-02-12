"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { getSessionSpec } from "@/lib/sessions-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface SpecViewProps {
  sessionSlug: string;
  className?: string;
}

/**
 * Renders the spec.md content for a session.
 *
 * Fetches the spec markdown and renders it with proper styling.
 * Handles loading and error states.
 */
export function SpecView({ sessionSlug, className }: SpecViewProps) {
  const [content, setContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSpec() {
      setIsLoading(true);
      setError(null);

      try {
        const result = await getSessionSpec(sessionSlug);
        setContent(result.content);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load spec");
      } finally {
        setIsLoading(false);
      }
    }

    fetchSpec();
  }, [sessionSlug]);

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center py-12", className)}>
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <span className="text-sm text-muted-foreground">Loading spec...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className={cn("border-red-200", className)}>
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Spec</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!content) {
    return (
      <Card className={cn("border-dashed", className)}>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">No spec found for this session.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("prose prose-sm max-w-none dark:prose-invert", className)}>
      <ReactMarkdown
        components={{
          // Style headings
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold mt-8 mb-4 first:mt-0">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-semibold mt-6 mb-3">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-medium mt-4 mb-2">{children}</h3>
          ),
          // Style code blocks
          code: ({ className, children, ...props }) => {
            const isInline = !className?.includes("language-");
            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-muted text-sm font-mono"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={cn("block p-4 rounded-lg bg-muted overflow-x-auto", className)} {...props}>
                {children}
              </code>
            );
          },
          // Style lists
          ul: ({ children }) => (
            <ul className="list-disc pl-6 my-2 space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-6 my-2 space-y-1">{children}</ol>
          ),
          // Style blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-muted pl-4 italic my-4">
              {children}
            </blockquote>
          ),
          // Style horizontal rules
          hr: () => <hr className="my-6 border-muted" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
