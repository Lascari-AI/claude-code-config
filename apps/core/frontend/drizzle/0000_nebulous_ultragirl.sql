-- Current sql file was generated after introspecting the database
-- If you want to run this migration please uncomment this code before executing migrations
/*
CREATE TABLE "projects" (
	"id" uuid PRIMARY KEY NOT NULL,
	"name" varchar NOT NULL,
	"slug" varchar NOT NULL,
	"path" varchar NOT NULL,
	"repo_url" varchar,
	"status" varchar NOT NULL,
	"onboarding_status" json,
	"metadata" json,
	"created_at" timestamp NOT NULL,
	"updated_at" timestamp NOT NULL
);
--> statement-breakpoint
CREATE TABLE "sessions" (
	"id" uuid PRIMARY KEY NOT NULL,
	"session_slug" varchar NOT NULL,
	"title" varchar,
	"description" text,
	"project_id" uuid,
	"status" varchar NOT NULL,
	"session_type" varchar NOT NULL,
	"working_dir" varchar NOT NULL,
	"session_dir" varchar,
	"git_worktree" varchar,
	"git_branch" varchar,
	"spec_exists" boolean NOT NULL,
	"plan_exists" boolean NOT NULL,
	"checkpoints_total" integer NOT NULL,
	"checkpoints_completed" integer NOT NULL,
	"total_input_tokens" integer NOT NULL,
	"total_output_tokens" integer NOT NULL,
	"total_cost" double precision NOT NULL,
	"error_message" text,
	"error_phase" varchar,
	"metadata" json,
	"created_at" timestamp NOT NULL,
	"updated_at" timestamp NOT NULL,
	"started_at" timestamp,
	"completed_at" timestamp
);
--> statement-breakpoint
CREATE TABLE "agents" (
	"id" uuid PRIMARY KEY NOT NULL,
	"session_id" uuid NOT NULL,
	"agent_type" varchar NOT NULL,
	"name" varchar,
	"sdk_session_id" varchar,
	"model" varchar NOT NULL,
	"model_alias" varchar,
	"system_prompt" text,
	"working_dir" varchar,
	"status" varchar NOT NULL,
	"checkpoint_id" integer,
	"task_group_id" varchar,
	"input_tokens" integer NOT NULL,
	"output_tokens" integer NOT NULL,
	"cost" double precision NOT NULL,
	"error_message" text,
	"allowed_tools" text,
	"metadata" json,
	"created_at" timestamp NOT NULL,
	"updated_at" timestamp NOT NULL,
	"started_at" timestamp,
	"completed_at" timestamp
);
--> statement-breakpoint
CREATE TABLE "agent_logs" (
	"id" uuid PRIMARY KEY NOT NULL,
	"agent_id" uuid NOT NULL,
	"session_id" uuid NOT NULL,
	"sdk_session_id" varchar,
	"event_category" varchar NOT NULL,
	"event_type" varchar NOT NULL,
	"content" text,
	"payload" json,
	"summary" text,
	"tool_name" varchar,
	"tool_input" text,
	"tool_output" text,
	"entry_index" integer,
	"checkpoint_id" integer,
	"timestamp" timestamp NOT NULL,
	"duration_ms" integer
);
--> statement-breakpoint
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "agents" ADD CONSTRAINT "agents_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "public"."sessions"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "agent_logs" ADD CONSTRAINT "agent_logs_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "public"."agents"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "agent_logs" ADD CONSTRAINT "agent_logs_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "public"."sessions"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
CREATE UNIQUE INDEX "ix_projects_slug" ON "projects" USING btree ("slug" text_ops);--> statement-breakpoint
CREATE INDEX "ix_projects_status" ON "projects" USING btree ("status" text_ops);--> statement-breakpoint
CREATE INDEX "ix_sessions_project_id" ON "sessions" USING btree ("project_id" uuid_ops);--> statement-breakpoint
CREATE UNIQUE INDEX "ix_sessions_session_slug" ON "sessions" USING btree ("session_slug" text_ops);--> statement-breakpoint
CREATE INDEX "ix_sessions_status" ON "sessions" USING btree ("status" text_ops);--> statement-breakpoint
CREATE INDEX "ix_agents_agent_type" ON "agents" USING btree ("agent_type" text_ops);--> statement-breakpoint
CREATE INDEX "ix_agents_sdk_session_id" ON "agents" USING btree ("sdk_session_id" text_ops);--> statement-breakpoint
CREATE INDEX "ix_agents_session_id" ON "agents" USING btree ("session_id" uuid_ops);--> statement-breakpoint
CREATE INDEX "ix_agents_status" ON "agents" USING btree ("status" text_ops);--> statement-breakpoint
CREATE INDEX "ix_agent_logs_agent_id" ON "agent_logs" USING btree ("agent_id" uuid_ops);--> statement-breakpoint
CREATE INDEX "ix_agent_logs_event_category" ON "agent_logs" USING btree ("event_category" text_ops);--> statement-breakpoint
CREATE INDEX "ix_agent_logs_event_type" ON "agent_logs" USING btree ("event_type" text_ops);--> statement-breakpoint
CREATE INDEX "ix_agent_logs_session_id" ON "agent_logs" USING btree ("session_id" uuid_ops);--> statement-breakpoint
CREATE INDEX "ix_agent_logs_timestamp" ON "agent_logs" USING btree ("timestamp" timestamp_ops);--> statement-breakpoint
CREATE INDEX "ix_agent_logs_tool_name" ON "agent_logs" USING btree ("tool_name" text_ops);
*/