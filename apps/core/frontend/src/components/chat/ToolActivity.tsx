"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface ToolActivityProps {
  toolName: string;
  content: string | null;
  blockType: "tool_use" | "tool_result";
}

// ═══════════════════════════════════════════════════════════════════════════════
// ICONS
// ═══════════════════════════════════════════════════════════════════════════════

function WrenchIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 16"
      fill="currentColor"
      className={cn("h-3 w-3", className)}
    >
      <path
        fillRule="evenodd"
        d="M11.5 1a.5.5 0 0 0-.42.23l-1.5 2.25a.5.5 0 0 0 .08.63l1.5 1.5a.5.5 0 0 0 .63.08l2.25-1.5A.5.5 0 0 0 14 3.77V2.5A1.5 1.5 0 0 0 12.5 1h-1ZM4.27 4.03a3.25 3.25 0 0 1 4.17.68l.08.1 2.7 2.7a3.25 3.25 0 0 1-3.92 5.08l-.18-.12-2.7-2.7a3.25 3.25 0 0 1-.15-4.44Z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 16"
      fill="currentColor"
      className={cn("h-3 w-3", className)}
    >
      <path
        fillRule="evenodd"
        d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
        clipRule="evenodd"
      />
    </svg>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Renders a tool_use or tool_result block as a collapsible activity indicator.
 *
 * Shows tool name with an icon, initially collapsed.
 * Click to expand and show content/details.
 */
export function ToolActivity({ toolName, content, blockType }: ToolActivityProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasContent = !!content;
  const isResult = blockType === "tool_result";

  return (
    <div
      className={cn(
        "border-l-2 border-muted pl-3 py-1",
        hasContent && "cursor-pointer"
      )}
      onClick={() => hasContent && setIsExpanded(!isExpanded)}
    >
      {/* Header row */}
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {isResult ? (
          <CheckIcon className="text-green-500" />
        ) : (
          <WrenchIcon />
        )}
        <span className="font-mono">
          {toolName}
        </span>
        {isResult && (
          <span className="text-green-600 dark:text-green-400">done</span>
        )}
        {hasContent && (
          <span className="ml-auto text-[10px]">
            {isExpanded ? "collapse" : "expand"}
          </span>
        )}
      </div>

      {/* Expandable content */}
      {isExpanded && content && (
        <pre className="mt-1 text-[11px] text-muted-foreground bg-muted/50 rounded px-2 py-1.5 overflow-x-auto max-h-48 whitespace-pre-wrap break-words">
          <code>{content}</code>
        </pre>
      )}
    </div>
  );
}
