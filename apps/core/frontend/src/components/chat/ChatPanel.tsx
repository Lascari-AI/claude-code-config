"use client";

import { useEffect, useRef, useState } from "react";
import {
  sendMessage,
  getChatHistory,
  type ChatBlock,
  type ChatHistoryMessage,
} from "@/lib/chat-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { MessageBubble } from "./MessageBubble";
import { ToolActivity } from "./ToolActivity";

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
export function ChatPanel({ sessionSlug, className }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [turnIndex, setTurnIndex] = useState(0);
  const scrollEndRef = useRef<HTMLDivElement>(null);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn("flex flex-col h-[500px] border rounded-lg", className)}>
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

        {/* Empty state */}
        {!isLoadingHistory && messages.length === 0 && !isLoading && (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            Start the spec interview by sending a message.
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

      {/* Input area */}
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
    </div>
  );
}
