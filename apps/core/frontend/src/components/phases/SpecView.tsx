"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { getSessionSpec } from "@/lib/sessions-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CodeBlock } from "@/components/markdown/CodeBlock";
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
  const lastHashRef = useRef<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchSpec() {
      try {
        const result = await getSessionSpec(sessionSlug);
        if (!isMounted) return;

        // Only update content if hash changed (or first load)
        if (result.content_hash && result.content_hash === lastHashRef.current) {
          return; // No change, skip re-render
        }

        lastHashRef.current = result.content_hash ?? null;
        setContent(result.content);
        setError(null);
      } catch (err) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load spec");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchSpec(); // Initial load
    const interval = setInterval(fetchSpec, 5000); // Poll every 5s

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
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
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
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
          // Enhanced code blocks with syntax highlighting and mermaid support
          code: CodeBlock,
          // Style lists
          ul: ({ children }) => (
            <ul className="list-disc pl-6 my-2 space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-6 my-2 space-y-1">{children}</ol>
          ),
          // Style task list items (GFM checkboxes)
          input: ({ type, checked, ...props }) => {
            if (type === "checkbox") {
              return (
                <input
                  type="checkbox"
                  checked={checked}
                  disabled
                  className="mr-2 h-4 w-4 rounded border-border accent-primary"
                  {...props}
                />
              );
            }
            return <input type={type} {...props} />;
          },
          // Style blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary/30 bg-muted/30 pl-4 py-2 italic my-4 rounded-r">
              {children}
            </blockquote>
          ),
          // Style tables (GFM)
          table: ({ children }) => (
            <div className="my-4 overflow-x-auto">
              <table className="min-w-full border-collapse border border-border rounded-lg">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-border bg-muted px-4 py-2 text-left font-semibold">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-4 py-2">{children}</td>
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
