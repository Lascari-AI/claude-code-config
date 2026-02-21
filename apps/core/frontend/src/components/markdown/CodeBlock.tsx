"use client";

import { useState, type ReactNode } from "react";
import { Check, Copy } from "lucide-react";
import { MermaidBlock } from "./MermaidBlock";
import { cn } from "@/lib/utils";

interface CodeBlockProps {
  className?: string;
  children?: ReactNode;
}

/**
 * Enhanced code block component for ReactMarkdown.
 *
 * Features:
 * - Routes mermaid code to MermaidBlock for diagram rendering
 * - Copy-to-clipboard button for code blocks
 * - Preserves ASCII art formatting (no highlighting for unlabeled blocks)
 * - Applies highlight.js classes for syntax highlighting
 */
export function CodeBlock({ className, children, ...props }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  // Extract language from className (e.g., "language-python" -> "python")
  const match = /language-(\w+)/.exec(className || "");
  const language = match ? match[1] : null;

  // Get the code content as string
  const codeContent = extractTextContent(children);

  // Check if this is an inline code element (no language class)
  const isInline = !className?.includes("language-");

  // Render inline code
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

  // Route mermaid blocks to MermaidBlock component
  if (language === "mermaid") {
    return <MermaidBlock code={codeContent} />;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="relative group my-4">
      {/* Language badge */}
      {language && (
        <div className="absolute top-0 left-4 -translate-y-1/2 px-2 py-0.5 bg-muted border border-border rounded text-xs text-muted-foreground font-mono">
          {language}
        </div>
      )}

      {/* Copy button */}
      <button
        onClick={handleCopy}
        className={cn(
          "absolute top-2 right-2 p-1.5 rounded-md",
          "opacity-0 group-hover:opacity-100 transition-opacity",
          "bg-muted hover:bg-muted/80 border border-border",
          "text-muted-foreground hover:text-foreground"
        )}
        aria-label={copied ? "Copied!" : "Copy code"}
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-500" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </button>

      {/* Code content */}
      <code
        className={cn(
          "block p-4 pt-5 rounded-lg bg-muted overflow-x-auto font-mono text-sm",
          "border border-border",
          className
        )}
        {...props}
      >
        {children}
      </code>
    </div>
  );
}

/**
 * Recursively extracts text content from React children.
 */
function extractTextContent(children: ReactNode): string {
  if (typeof children === "string") {
    return children;
  }
  if (typeof children === "number") {
    return String(children);
  }
  if (Array.isArray(children)) {
    return children.map(extractTextContent).join("");
  }
  if (children && typeof children === "object" && "props" in children) {
    return extractTextContent((children as { props: { children?: ReactNode } }).props.children);
  }
  return "";
}
