import { relations } from "drizzle-orm/relations";
import { projects, sessions, agents, agentLogs } from "./schema";

export const sessionsRelations = relations(sessions, ({one, many}) => ({
	project: one(projects, {
		fields: [sessions.projectId],
		references: [projects.id]
	}),
	agents: many(agents),
	agentLogs: many(agentLogs),
}));

export const projectsRelations = relations(projects, ({many}) => ({
	sessions: many(sessions),
}));

export const agentsRelations = relations(agents, ({one, many}) => ({
	session: one(sessions, {
		fields: [agents.sessionId],
		references: [sessions.id]
	}),
	agentLogs: many(agentLogs),
}));

export const agentLogsRelations = relations(agentLogs, ({one}) => ({
	agent: one(agents, {
		fields: [agentLogs.agentId],
		references: [agents.id]
	}),
	session: one(sessions, {
		fields: [agentLogs.sessionId],
		references: [sessions.id]
	}),
}));