/**
 * Session Agents API Route
 *
 * Server-side agent listing by session ID using Drizzle ORM.
 * Replaces backend /agents/session/{session_id} endpoint.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, agents, sessions } from "@/db";
import { eq, asc } from "drizzle-orm";
import type { AgentSummary } from "@/types/agent";

/**
 * Map database row to AgentSummary type with snake_case keys
 */
function mapToAgentSummary(row: typeof agents.$inferSelect): AgentSummary {
  return {
    id: row.id,
    agent_type: row.agentType as AgentSummary["agent_type"],
    name: row.name,
    model_alias: row.modelAlias,
    status: row.status as AgentSummary["status"],
    checkpoint_id: row.checkpointId,
    input_tokens: row.inputTokens,
    output_tokens: row.outputTokens,
    cost: row.cost,
    started_at: row.startedAt,
    completed_at: row.completedAt,
  };
}

/**
 * GET /api/agents/session/[sessionId]
 *
 * List agents for a specific session.
 * Returns agent summaries ordered by creation time (chronological).
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await params;

  try {
    // Verify session exists
    const sessionResult = await db
      .select({ id: sessions.id })
      .from(sessions)
      .where(eq(sessions.id, sessionId))
      .limit(1);

    if (sessionResult.length === 0) {
      return NextResponse.json(
        { error: `Session ${sessionId} not found` },
        { status: 404 }
      );
    }

    // Get agents for the session
    const result = await db
      .select()
      .from(agents)
      .where(eq(agents.sessionId, sessionId))
      .orderBy(asc(agents.createdAt));

    const summaries: AgentSummary[] = result.map(mapToAgentSummary);

    return NextResponse.json(summaries);
  } catch (error) {
    console.error("Error fetching session agents:", error);
    return NextResponse.json(
      { error: "Failed to fetch session agents" },
      { status: 500 }
    );
  }
}
