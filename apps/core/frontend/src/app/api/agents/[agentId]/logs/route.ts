/**
 * Agent Logs API Route
 *
 * Server-side agent log listing using Drizzle ORM.
 * Replaces backend /agents/{agent_id}/logs endpoint.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, agents, agentLogs } from "@/db";
import { eq, and, asc, SQL } from "drizzle-orm";
import type { AgentLogSummary } from "@/types/agent";

/**
 * Map database row to AgentLogSummary type with snake_case keys
 */
function mapToAgentLogSummary(
  row: typeof agentLogs.$inferSelect
): AgentLogSummary {
  return {
    id: row.id,
    agent_id: row.agentId,
    session_id: row.sessionId,
    event_category: row.eventCategory as AgentLogSummary["event_category"],
    event_type: row.eventType,
    tool_name: row.toolName,
    content: row.content,
    summary: row.summary,
    timestamp: row.timestamp,
    duration_ms: row.durationMs,
  };
}

/**
 * GET /api/agents/[agentId]/logs
 *
 * List logs for an agent with optional filters and pagination.
 *
 * Query params:
 * - event_category: Filter by event category (hook, response, phase)
 * - event_type: Filter by specific event type
 * - limit: Maximum results (default 100)
 * - offset: Number to skip (default 0)
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ agentId: string }> }
) {
  const { agentId } = await params;
  const searchParams = request.nextUrl.searchParams;
  const eventCategory = searchParams.get("event_category");
  const eventType = searchParams.get("event_type");
  const limit = parseInt(searchParams.get("limit") || "100");
  const offset = parseInt(searchParams.get("offset") || "0");

  try {
    // Verify agent exists
    const agentResult = await db
      .select({ id: agents.id })
      .from(agents)
      .where(eq(agents.id, agentId))
      .limit(1);

    if (agentResult.length === 0) {
      return NextResponse.json(
        { error: `Agent ${agentId} not found` },
        { status: 404 }
      );
    }

    // Build where conditions
    const conditions: SQL[] = [eq(agentLogs.agentId, agentId)];

    if (eventCategory) {
      conditions.push(eq(agentLogs.eventCategory, eventCategory));
    }
    if (eventType) {
      conditions.push(eq(agentLogs.eventType, eventType));
    }

    // Execute query - ordered chronologically (oldest first)
    const result = await db
      .select()
      .from(agentLogs)
      .where(and(...conditions))
      .orderBy(asc(agentLogs.timestamp))
      .limit(limit)
      .offset(offset);

    const summaries: AgentLogSummary[] = result.map(mapToAgentLogSummary);

    return NextResponse.json(summaries);
  } catch (error) {
    console.error("Error fetching agent logs:", error);
    return NextResponse.json(
      { error: "Failed to fetch agent logs" },
      { status: 500 }
    );
  }
}
