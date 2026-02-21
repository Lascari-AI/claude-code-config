"use client";

import { useEffect, useRef, useState } from "react";
import {
  startChat,
  sendMessage,
  sendAnswer,
  getChatHistory,
  type ChatBlock,
  type ChatHistoryMessage,
  type PendingQuestion,
} from "@/lib/chat-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { MessageBubble } from "./MessageBubble";
import { ToolActivity } from "./ToolActivity";
import { AskUserQuestion } from "./AskUserQuestion";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  block_type: "text" | "tool_use" | "tool_result" | "thinking";
  tool_name: string | null;
}

interface ChatPanelProps {
  sessionSlug: string;
  className?: string;
  /** Current session phase — shows "Continue to Plan" when spec is done */
  currentPhase?: string;
  /** Callback when user clicks "Continue to Plan" */
  onContinueToPlan?: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Map history messages to renderable ChatMessages.
 * Includes all block types for block-type-aware rendering.
 */
function historyToMessages(history: ChatHistoryMessage[]): ChatMessage[] {
  return history
    .filter((msg) => msg.content) // skip empty blocks
    .map((msg) => ({
      role: (msg.role === "user" ? "user" : "assistant") as
        | "user"
        | "assistant",
      content: msg.content!,
      timestamp: msg.timestamp,
      block_type: (msg.block_type as ChatMessage["block_type"]) || "text",
      tool_name: msg.tool_name ?? null,
    }));
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Chat panel for spec interview conversations.
 *
 * Loads persisted chat history on mount and supports multi-turn
 * conversation with auto-scroll to bottom on new messages.
 */
export function ChatPanel({
  sessionSlug,
  className,
  currentPhase,
  onContinueToPlan,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isAutoStarting, setIsAutoStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [turnIndex, setTurnIndex] = useState(0);
  const [pendingQuestion, setPendingQuestion] = useState<PendingQuestion | null>(null);
  const scrollEndRef = useRef<HTMLDivElement>(null);
  const hasAutoStarted = useRef(false);

  // ─── Load chat history on mount ──────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      try {
        const response = await getChatHistory(sessionSlug);
        if (cancelled) return;

        const loadedMessages = historyToMessages(response.messages);
        setMessages(loadedMessages);

        // Derive turnIndex from max turn_index in history
        if (response.messages.length > 0) {
          const maxTurn = Math.max(
            ...response.messages.map((m) => m.turn_index)
          );
          setTurnIndex(maxTurn + 1);
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to load chat history:", err);
          // Non-fatal: empty chat is fine for new sessions
        }
      } finally {
        if (!cancelled) {
          setIsLoadingHistory(false);
        }
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [sessionSlug]);

  // ─── Auto-start: agent speaks first on empty session ─────────────────────
  useEffect(() => {
    if (isLoadingHistory || messages.length > 0 || isLoading || hasAutoStarted.current) return;
    hasAutoStarted.current = true;

    async function autoStart() {
      setIsAutoStarting(true);
      setIsLoading(true);
      try {
        const response = await startChat(sessionSlug);

        // If idempotency check returned empty, nothing to add
        if (response.blocks.length === 0) return;

        const assistantMessages: ChatMessage[] = response.blocks
          .filter((block: ChatBlock) => block.content)
          .map((block: ChatBlock) => ({
            role: "assistant" as const,
            content: block.content!,
            timestamp: new Date().toISOString(),
            block_type: (block.block_type as ChatMessage["block_type"]) || "text",
            tool_name: block.tool_name ?? null,
          }));

        setMessages((prev) => [...prev, ...assistantMessages]);
        setTurnIndex(1);

        if (response.pending_question) {
          setPendingQuestion(response.pending_question);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to start interview");
      } finally {
        setIsLoading(false);
        setIsAutoStarting(false);
      }
    }

    autoStart();
  }, [isLoadingHistory, messages.length, isLoading, sessionSlug]);

  // ─── Auto-scroll to bottom on new messages ───────────────────────────────
  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ─── Send handler ────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;

    // Add user message optimistically
    const userMessage: ChatMessage = {
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString(),
      block_type: "text",
      tool_name: null,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendMessage(sessionSlug, trimmed);

      // Map all response blocks for block-type-aware rendering
      const assistantMessages: ChatMessage[] = response.blocks
        .filter((block: ChatBlock) => block.content)
        .map((block: ChatBlock) => ({
          role: "assistant" as const,
          content: block.content!,
          timestamp: new Date().toISOString(),
          block_type: (block.block_type as ChatMessage["block_type"]) || "text",
          tool_name: block.tool_name ?? null,
        }));

      setMessages((prev) => [...prev, ...assistantMessages]);
      setTurnIndex((prev) => prev + 1);

      // Check for pending AskUserQuestion
      if (response.pending_question) {
        setPendingQuestion(response.pending_question);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  // ─── AskUserQuestion answer handler ─────────────────────────────────────
  const handleAnswer = async (questionText: string, answer: string) => {
    if (!pendingQuestion || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await sendAnswer(
        sessionSlug,
        pendingQuestion.tool_use_id,
        { [questionText]: answer }
      );

      // Add response blocks to messages
      const assistantMessages: ChatMessage[] = result.blocks
        .filter((block: ChatBlock) => block.content)
        .map((block: ChatBlock) => ({
          role: "assistant" as const,
          content: block.content!,
          timestamp: new Date().toISOString(),
          block_type: (block.block_type as ChatMessage["block_type"]) || "text",
          tool_name: block.tool_name ?? null,
        }));

      setMessages((prev) => [...prev, ...assistantMessages]);
      setTurnIndex((prev) => prev + 1);
      setPendingQuestion(null);

      // Check for another pending question (chained questions)
      if (result.pending_question) {
        setPendingQuestion(result.pending_question);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send answer");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn("flex flex-col h-full border rounded-lg", className)}>
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* Loading history spinner */}
        {isLoadingHistory && (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
              Loading chat history...
            </div>
          </div>
        )}

        {/* Empty state / auto-start spinner */}
        {!isLoadingHistory && messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            {isAutoStarting ? (
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
                Starting interview...
              </div>
            ) : (
              !isLoading && "Waiting for agent..."
            )}
          </div>
        )}

        {messages.map((msg, i) => {
          // Hide thinking blocks
          if (msg.block_type === "thinking") return null;

          // Tool use/result blocks
          if (msg.block_type === "tool_use" || msg.block_type === "tool_result") {
            return (
              <ToolActivity
                key={i}
                toolName={msg.tool_name ?? "unknown"}
                content={msg.content}
                blockType={msg.block_type}
              />
            );
          }

          // Text blocks (default)
          return (
            <MessageBubble
              key={i}
              role={msg.role}
              content={msg.content}
            />
          );
        })}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
                Thinking...
              </div>
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="flex justify-center">
            <div className="bg-destructive/10 text-destructive rounded-lg px-4 py-2 text-sm">
              {error}
            </div>
          </div>
        )}

        <div ref={scrollEndRef} />
      </div>

      {/* Input area — switches between text input and AskUserQuestion */}
      {pendingQuestion ? (
        <div className="p-4 border-t bg-background space-y-4">
          {pendingQuestion.questions.map((q, idx) => (
            <AskUserQuestion
              key={`${pendingQuestion.tool_use_id}-${idx}`}
              question={q.question}
              header={q.header}
              options={q.options}
              multiSelect={q.multiSelect}
              onAnswer={(answer) => handleAnswer(q.question, answer)}
              disabled={isLoading}
            />
          ))}
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="flex gap-2 p-4 border-t bg-background"
        >
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type a message..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading || !inputValue.trim()}>
            Send
          </Button>
        </form>
      )}

      {/* Continue to Plan — shown when spec phase is finalized */}
      {currentPhase === "plan" && onContinueToPlan && (
        <div className="p-4 border-t bg-primary/5">
          <Button
            onClick={onContinueToPlan}
            className="w-full"
            size="lg"
          >
            Continue to Plan
          </Button>
        </div>
      )}
    </div>
  );
}
