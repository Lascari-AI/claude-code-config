/**
 * Drizzle ORM Schema
 *
 * Generated from PostgreSQL database using drizzle-kit pull.
 * Schema ownership: Python/SQLModel in session_db/models.py
 *
 * When schema changes:
 * 1. Update Python models in session_db/models.py
 * 2. Run alembic migrations
 * 3. Run: DATABASE_URL="..." npx drizzle-kit pull
 * 4. Update this file with new schema
 */

import {
  pgTable,
  uniqueIndex,
  index,
  uuid,
  varchar,
  json,
  timestamp,
  foreignKey,
  text,
  boolean,
  integer,
  doublePrecision,
} from "drizzle-orm/pg-core";

// ═══════════════════════════════════════════════════════════════════════════════
// PROJECTS TABLE
// ═══════════════════════════════════════════════════════════════════════════════

export const projects = pgTable(
  "projects",
  {
    id: uuid().primaryKey().notNull(),
    name: varchar().notNull(),
    slug: varchar().notNull(),
    path: varchar().notNull(),
    repoUrl: varchar("repo_url"),
    status: varchar().notNull(),
    onboardingStatus: json("onboarding_status"),
    metadata: json(),
    createdAt: timestamp("created_at", { mode: "string" }).notNull(),
    updatedAt: timestamp("updated_at", { mode: "string" }).notNull(),
  },
  (table) => [
    uniqueIndex("ix_projects_slug").using(
      "btree",
      table.slug.asc().nullsLast().op("text_ops")
    ),
    index("ix_projects_status").using(
      "btree",
      table.status.asc().nullsLast().op("text_ops")
    ),
  ]
);

// ═══════════════════════════════════════════════════════════════════════════════
// SESSIONS TABLE
// ═══════════════════════════════════════════════════════════════════════════════

export const sessions = pgTable(
  "sessions",
  {
    id: uuid().primaryKey().notNull(),
    sessionSlug: varchar("session_slug").notNull(),
    title: varchar(),
    description: text(),
    projectId: uuid("project_id"),
    status: varchar().notNull(),
    sessionType: varchar("session_type").notNull(),
    workingDir: varchar("working_dir").notNull(),
    sessionDir: varchar("session_dir"),
    gitWorktree: varchar("git_worktree"),
    gitBranch: varchar("git_branch"),
    specExists: boolean("spec_exists").notNull(),
    planExists: boolean("plan_exists").notNull(),
    checkpointsTotal: integer("checkpoints_total").notNull(),
    checkpointsCompleted: integer("checkpoints_completed").notNull(),
    totalInputTokens: integer("total_input_tokens").notNull(),
    totalOutputTokens: integer("total_output_tokens").notNull(),
    totalCost: doublePrecision("total_cost").notNull(),
    errorMessage: text("error_message"),
    errorPhase: varchar("error_phase"),
    metadata: json(),
    createdAt: timestamp("created_at", { mode: "string" }).notNull(),
    updatedAt: timestamp("updated_at", { mode: "string" }).notNull(),
    startedAt: timestamp("started_at", { mode: "string" }),
    completedAt: timestamp("completed_at", { mode: "string" }),
  },
  (table) => [
    index("ix_sessions_project_id").using(
      "btree",
      table.projectId.asc().nullsLast().op("uuid_ops")
    ),
    uniqueIndex("ix_sessions_session_slug").using(
      "btree",
      table.sessionSlug.asc().nullsLast().op("text_ops")
    ),
    index("ix_sessions_status").using(
      "btree",
      table.status.asc().nullsLast().op("text_ops")
    ),
    foreignKey({
      columns: [table.projectId],
      foreignColumns: [projects.id],
      name: "sessions_project_id_fkey",
    }),
  ]
);

// ═══════════════════════════════════════════════════════════════════════════════
// AGENTS TABLE
// ═══════════════════════════════════════════════════════════════════════════════

export const agents = pgTable(
  "agents",
  {
    id: uuid().primaryKey().notNull(),
    sessionId: uuid("session_id").notNull(),
    agentType: varchar("agent_type").notNull(),
    name: varchar(),
    sdkSessionId: varchar("sdk_session_id"),
    model: varchar().notNull(),
    modelAlias: varchar("model_alias"),
    systemPrompt: text("system_prompt"),
    workingDir: varchar("working_dir"),
    status: varchar().notNull(),
    checkpointId: integer("checkpoint_id"),
    taskGroupId: varchar("task_group_id"),
    inputTokens: integer("input_tokens").notNull(),
    outputTokens: integer("output_tokens").notNull(),
    cost: doublePrecision().notNull(),
    errorMessage: text("error_message"),
    allowedTools: text("allowed_tools"),
    metadata: json(),
    createdAt: timestamp("created_at", { mode: "string" }).notNull(),
    updatedAt: timestamp("updated_at", { mode: "string" }).notNull(),
    startedAt: timestamp("started_at", { mode: "string" }),
    completedAt: timestamp("completed_at", { mode: "string" }),
  },
  (table) => [
    index("ix_agents_agent_type").using(
      "btree",
      table.agentType.asc().nullsLast().op("text_ops")
    ),
    index("ix_agents_sdk_session_id").using(
      "btree",
      table.sdkSessionId.asc().nullsLast().op("text_ops")
    ),
    index("ix_agents_session_id").using(
      "btree",
      table.sessionId.asc().nullsLast().op("uuid_ops")
    ),
    index("ix_agents_status").using(
      "btree",
      table.status.asc().nullsLast().op("text_ops")
    ),
    foreignKey({
      columns: [table.sessionId],
      foreignColumns: [sessions.id],
      name: "agents_session_id_fkey",
    }),
  ]
);

// ═══════════════════════════════════════════════════════════════════════════════
// AGENT LOGS TABLE
// ═══════════════════════════════════════════════════════════════════════════════

export const agentLogs = pgTable(
  "agent_logs",
  {
    id: uuid().primaryKey().notNull(),
    agentId: uuid("agent_id").notNull(),
    sessionId: uuid("session_id").notNull(),
    sdkSessionId: varchar("sdk_session_id"),
    eventCategory: varchar("event_category").notNull(),
    eventType: varchar("event_type").notNull(),
    content: text(),
    payload: json(),
    summary: text(),
    toolName: varchar("tool_name"),
    toolInput: text("tool_input"),
    toolOutput: text("tool_output"),
    entryIndex: integer("entry_index"),
    checkpointId: integer("checkpoint_id"),
    timestamp: timestamp({ mode: "string" }).notNull(),
    durationMs: integer("duration_ms"),
  },
  (table) => [
    index("ix_agent_logs_agent_id").using(
      "btree",
      table.agentId.asc().nullsLast().op("uuid_ops")
    ),
    index("ix_agent_logs_event_category").using(
      "btree",
      table.eventCategory.asc().nullsLast().op("text_ops")
    ),
    index("ix_agent_logs_event_type").using(
      "btree",
      table.eventType.asc().nullsLast().op("text_ops")
    ),
    index("ix_agent_logs_session_id").using(
      "btree",
      table.sessionId.asc().nullsLast().op("uuid_ops")
    ),
    index("ix_agent_logs_timestamp").using(
      "btree",
      table.timestamp.asc().nullsLast().op("timestamp_ops")
    ),
    index("ix_agent_logs_tool_name").using(
      "btree",
      table.toolName.asc().nullsLast().op("text_ops")
    ),
    foreignKey({
      columns: [table.agentId],
      foreignColumns: [agents.id],
      name: "agent_logs_agent_id_fkey",
    }),
    foreignKey({
      columns: [table.sessionId],
      foreignColumns: [sessions.id],
      name: "agent_logs_session_id_fkey",
    }),
  ]
);

// ═══════════════════════════════════════════════════════════════════════════════
// TYPE EXPORTS
// ═══════════════════════════════════════════════════════════════════════════════

export type Project = typeof projects.$inferSelect;
export type NewProject = typeof projects.$inferInsert;

export type Session = typeof sessions.$inferSelect;
export type NewSession = typeof sessions.$inferInsert;

export type Agent = typeof agents.$inferSelect;
export type NewAgent = typeof agents.$inferInsert;

export type AgentLog = typeof agentLogs.$inferSelect;
export type NewAgentLog = typeof agentLogs.$inferInsert;
