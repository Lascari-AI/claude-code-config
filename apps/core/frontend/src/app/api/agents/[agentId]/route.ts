/**
 * Agent by ID API Route
 *
 * Server-side agent lookup by UUID using Drizzle ORM.
 * Replaces backend /agents/{agent_id} endpoint.
 */

import { NextRequest, NextResponse } from "next/server";
import { db, agents } from "@/db";
import { eq } from "drizzle-orm";
import type { Agent } from "@/types/agent";

/**
 * Map database row to Agent type with snake_case keys
 */
function mapToAgent(row: typeof agents.$inferSelect): Agent {
  return {
    id: row.id,
    session_id: row.sessionId,
    agent_type: row.agentType as Agent["agent_type"],
    name: row.name,
    model: row.model,
    model_alias: row.modelAlias,
    sdk_session_id: row.sdkSessionId,
    system_prompt: row.systemPrompt,
    working_dir: row.workingDir,
    allowed_tools: row.allowedTools,
    status: row.status as Agent["status"],
    checkpoint_id: row.checkpointId,
    task_group_id: row.taskGroupId,
    input_tokens: row.inputTokens,
    output_tokens: row.outputTokens,
    cost: row.cost,
    error_message: row.errorMessage,
    metadata_: (row.metadata as Record<string, unknown>) ?? {},
    created_at: row.createdAt,
    updated_at: row.updatedAt,
    started_at: row.startedAt,
    completed_at: row.completedAt,
  };
}

/**
 * GET /api/agents/[agentId]
 *
 * Get a single agent by UUID.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ agentId: string }> }
) {
  const { agentId } = await params;

  try {
    const result = await db
      .select()
      .from(agents)
      .where(eq(agents.id, agentId))
      .limit(1);

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Agent ${agentId} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json(mapToAgent(result[0]));
  } catch (error) {
    console.error("Error fetching agent:", error);
    return NextResponse.json(
      { error: "Failed to fetch agent" },
      { status: 500 }
    );
  }
}
