/**
 * Drizzle Type Aliases
 *
 * This file survives `drizzle-kit pull` overwrites.
 * Add type aliases here when new tables are added.
 *
 * Schema ownership: Python/SQLModel in session_db/models.py
 * When schema changes: run `DATABASE_URL="..." npx drizzle-kit pull`
 */

import type {
  projects,
  sessions,
  agents,
  agentLogs,
  interactiveMessages,
} from "./schema";

// ═══════════════════════════════════════════════════════════════════════════════
// TABLE TYPES
// ═══════════════════════════════════════════════════════════════════════════════

export type Project = typeof projects.$inferSelect;
export type NewProject = typeof projects.$inferInsert;

export type Session = typeof sessions.$inferSelect;
export type NewSession = typeof sessions.$inferInsert;

export type Agent = typeof agents.$inferSelect;
export type NewAgent = typeof agents.$inferInsert;

export type AgentLog = typeof agentLogs.$inferSelect;
export type NewAgentLog = typeof agentLogs.$inferInsert;

export type InteractiveMessage = typeof interactiveMessages.$inferSelect;
export type NewInteractiveMessage = typeof interactiveMessages.$inferInsert;
