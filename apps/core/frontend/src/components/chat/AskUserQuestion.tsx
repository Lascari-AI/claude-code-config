"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface QuestionOption {
  label: string;
  description: string;
}

interface AskUserQuestionProps {
  question: string;
  header: string;
  options: QuestionOption[];
  multiSelect: boolean;
  onAnswer: (answer: string) => void;
  disabled?: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Renders an AskUserQuestion tool call as structured UI.
 *
 * Single-select: clickable chips — one active at a time.
 * Multi-select: toggle chips — multiple can be active.
 * Always includes an "Other" free-text option.
 *
 * On submit, formats the selection as a string and calls onAnswer.
 */
export function AskUserQuestion({
  question,
  header,
  options,
  multiSelect,
  onAnswer,
  disabled = false,
}: AskUserQuestionProps) {
  const [selected, setSelected] = useState<string[]>([]);
  const [showOther, setShowOther] = useState(false);
  const [otherText, setOtherText] = useState("");

  const handleOptionClick = (label: string) => {
    if (disabled) return;

    if (multiSelect) {
      setSelected((prev) =>
        prev.includes(label)
          ? prev.filter((s) => s !== label)
          : [...prev, label]
      );
      // Deselect "Other" when picking a regular option
      if (showOther && !selected.includes(label)) {
        setShowOther(false);
        setOtherText("");
      }
    } else {
      setSelected([label]);
      setShowOther(false);
      setOtherText("");
    }
  };

  const handleOtherClick = () => {
    if (disabled) return;

    if (multiSelect) {
      setShowOther((prev) => !prev);
      if (showOther) setOtherText("");
    } else {
      setSelected([]);
      setShowOther(true);
    }
  };

  const handleSubmit = () => {
    if (disabled) return;

    let answer: string;

    if (showOther && otherText.trim()) {
      if (multiSelect && selected.length > 0) {
        answer = [...selected, otherText.trim()].join(", ");
      } else {
        answer = otherText.trim();
      }
    } else {
      answer = selected.join(", ");
    }

    if (answer) {
      onAnswer(answer);
    }
  };

  const hasSelection = selected.length > 0 || (showOther && otherText.trim());

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {header}
        </span>
      </div>

      {/* Question */}
      <p className="text-sm text-foreground">{question}</p>

      {/* Options */}
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const isSelected = selected.includes(option.label);
          return (
            <button
              key={option.label}
              type="button"
              disabled={disabled}
              onClick={() => handleOptionClick(option.label)}
              className={cn(
                "group relative rounded-lg border px-3 py-2 text-left text-sm transition-all",
                "hover:border-primary/50 hover:bg-primary/5",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                isSelected
                  ? "border-primary bg-primary/10 text-primary ring-1 ring-primary/20"
                  : "border-border bg-background text-foreground"
              )}
            >
              <span className="font-medium">{option.label}</span>
              {option.description && (
                <span className="block text-xs text-muted-foreground mt-0.5">
                  {option.description}
                </span>
              )}
            </button>
          );
        })}

        {/* Other option */}
        <button
          type="button"
          disabled={disabled}
          onClick={handleOtherClick}
          className={cn(
            "rounded-lg border px-3 py-2 text-left text-sm transition-all",
            "hover:border-primary/50 hover:bg-primary/5",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            showOther
              ? "border-primary bg-primary/10 text-primary ring-1 ring-primary/20"
              : "border-dashed border-border bg-background text-muted-foreground"
          )}
        >
          <span className="font-medium">Other</span>
        </button>
      </div>

      {/* Other text input */}
      {showOther && (
        <input
          type="text"
          value={otherText}
          onChange={(e) => setOtherText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && otherText.trim()) {
              handleSubmit();
            }
          }}
          placeholder="Type your answer..."
          disabled={disabled}
          autoFocus
          className={cn(
            "w-full rounded-md border border-border bg-background px-3 py-2 text-sm",
            "placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary",
            "disabled:opacity-50"
          )}
        />
      )}

      {/* Submit */}
      <Button
        size="sm"
        onClick={handleSubmit}
        disabled={disabled || !hasSelection}
        className="w-full"
      >
        Submit
      </Button>
    </div>
  );
}
