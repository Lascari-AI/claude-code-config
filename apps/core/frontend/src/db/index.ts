/**
 * Drizzle Client Initialization
 *
 * Provides a singleton database client for server-side queries.
 * Uses the postgres driver with Drizzle ORM.
 *
 * Usage:
 *   import { db } from '@/db';
 *   const result = await db.select().from(projects);
 */

import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

// Create PostgreSQL connection
const connectionString = process.env.DATABASE_URL!;

// Create postgres.js client
// Note: max 1 connection for serverless environments (Next.js API routes)
const client = postgres(connectionString, { max: 1 });

// Create Drizzle client with schema for typed queries
export const db = drizzle(client, { schema });

// Re-export schema for convenience
export * from "./schema";
