/**
 * Session Spec API Route
 *
 * Serves spec.md content for a session from the filesystem.
 * Looks up session by slug, constructs session directory path, reads spec.md.
 */

import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import { join } from "path";
import { db, sessions } from "@/db";
import { eq } from "drizzle-orm";

interface SpecContent {
  content: string;
  exists: boolean;
}

/**
 * Get session directory path from session record.
 *
 * Tries session_dir first, then falls back to constructing from working_dir.
 */
function getSessionDir(
  session: typeof sessions.$inferSelect
): string | null {
  if (session.sessionDir) {
    return session.sessionDir;
  }

  // Fallback: construct path from working_dir + agents/sessions/{slug}
  if (session.workingDir) {
    return join(session.workingDir, "agents", "sessions", session.sessionSlug);
  }

  return null;
}

/**
 * GET /api/sessions/[slug]/spec
 *
 * Get the spec.md content for a session.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;

  try {
    // Look up session by slug
    const result = await db
      .select()
      .from(sessions)
      .where(eq(sessions.sessionSlug, slug))
      .limit(1);

    if (result.length === 0) {
      return NextResponse.json(
        { error: `Session with slug '${slug}' not found` },
        { status: 404 }
      );
    }

    const session = result[0];
    const sessionDir = getSessionDir(session);

    if (!sessionDir) {
      return NextResponse.json(
        { error: `Session directory not found for '${slug}'` },
        { status: 404 }
      );
    }

    // Read spec.md
    const specPath = join(sessionDir, "spec.md");

    try {
      const content = await readFile(specPath, "utf-8");
      return NextResponse.json<SpecContent>({
        content,
        exists: true,
      });
    } catch (fileError) {
      // File doesn't exist or can't be read
      if ((fileError as NodeJS.ErrnoException).code === "ENOENT") {
        return NextResponse.json(
          { error: `spec.md not found for session '${slug}'` },
          { status: 404 }
        );
      }
      throw fileError;
    }
  } catch (error) {
    console.error("Error fetching session spec:", error);
    return NextResponse.json(
      { error: "Failed to fetch session spec" },
      { status: 500 }
    );
  }
}
