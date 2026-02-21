"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

interface MermaidBlockProps {
  code: string;
}

// Initialize mermaid with default config
mermaid.initialize({
  startOnLoad: false,
  theme: "neutral",
  securityLevel: "loose",
  fontFamily: "inherit",
});

let mermaidId = 0;

/**
 * Renders a Mermaid diagram from code.
 *
 * Uses mermaid.render() to generate SVG from mermaid syntax.
 * Handles loading and error states gracefully.
 */
export function MermaidBlock({ code }: MermaidBlockProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!code.trim()) {
        setError("Empty diagram");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Generate unique ID for this diagram
        const id = `mermaid-${++mermaidId}`;

        // Render the diagram
        const { svg: renderedSvg } = await mermaid.render(id, code.trim());
        setSvg(renderedSvg);
      } catch (err) {
        console.error("Mermaid render error:", err);
        setError(err instanceof Error ? err.message : "Failed to render diagram");
        setSvg(null);
      } finally {
        setIsLoading(false);
      }
    };

    renderDiagram();
  }, [code]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 bg-muted/50 rounded-lg border border-border">
        <div className="flex flex-col items-center gap-2">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-primary" />
          <span className="text-xs text-muted-foreground">Rendering diagram...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20 p-4">
        <div className="flex items-start gap-2">
          <span className="text-red-500 text-sm font-medium">Diagram Error</span>
        </div>
        <p className="mt-1 text-xs text-red-600 dark:text-red-400">{error}</p>
        <details className="mt-2">
          <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
            View source
          </summary>
          <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
            <code>{code}</code>
          </pre>
        </details>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="mermaid-container my-4 flex justify-center overflow-x-auto bg-background rounded-lg border border-border p-4"
      dangerouslySetInnerHTML={{ __html: svg || "" }}
    />
  );
}
