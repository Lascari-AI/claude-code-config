/**
 * Agent Log Detail API Route
 *
 * Server-side agent log lookup by UUID using Drizzle ORM.
 * Replaces backend /agents/{agent_id}/logs/{log_id} endpoint.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, agents, agentLogs } from "@/db";
import { eq, and } from "drizzle-orm";
import type { AgentLog } from "@/types/agent";

/**
 * Map database row to AgentLog type with snake_case keys
 */
function mapToAgentLog(row: typeof agentLogs.$inferSelect): AgentLog {
  return {
    id: row.id,
    agent_id: row.agentId,
    session_id: row.sessionId,
    sdk_session_id: row.sdkSessionId,
    event_category: row.eventCategory as AgentLog["event_category"],
    event_type: row.eventType,
    tool_name: row.toolName,
    content: row.content,
    summary: row.summary,
    payload: (row.payload as Record<string, unknown>) ?? {},
    tool_input: row.toolInput,
    tool_output: row.toolOutput,
    entry_index: row.entryIndex,
    checkpoint_id: row.checkpointId,
    timestamp: row.timestamp,
    duration_ms: row.durationMs,
  };
}

/**
 * GET /api/agents/[agentId]/logs/[logId]
 *
 * Get a single log entry with full payload.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ agentId: string; logId: string }> }
) {
  const { agentId, logId } = await params;

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

    // Get log entry - verify it belongs to the agent
    const result = await db
      .select()
      .from(agentLogs)
      .where(and(eq(agentLogs.id, logId), eq(agentLogs.agentId, agentId)))
      .limit(1);

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Log ${logId} not found for agent ${agentId}` },
        { status: 404 }
      );
    }

    return NextResponse.json(mapToAgentLog(result[0]));
  } catch (error) {
    console.error("Error fetching agent log:", error);
    return NextResponse.json(
      { error: "Failed to fetch agent log" },
      { status: 500 }
    );
  }
}
