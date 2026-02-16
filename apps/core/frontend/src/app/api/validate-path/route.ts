/**
 * Path Validation API Route
 *
 * Validates a project path for onboarding.
 * Checks if path exists, is a directory, and has .claude folder.
 */

import { NextRequest, NextResponse } from "next/server";
import { stat } from "fs/promises";
import { join, normalize } from "path";
import { homedir } from "os";

interface ValidationRequest {
  name: string;
  path: string;
}

interface ValidationResponse {
  path_validated: boolean;
  claude_dir_exists: boolean;
  path_error: string | null;
}

/**
 * Expand ~ to home directory
 */
function expandPath(path: string): string {
  if (path.startsWith("~")) {
    return join(homedir(), path.slice(1));
  }
  return path;
}

/**
 * Check if a path exists and is a directory
 */
async function isDirectory(path: string): Promise<boolean> {
  try {
    const stats = await stat(path);
    return stats.isDirectory();
  } catch {
    return false;
  }
}

/**
 * Check if path exists at all
 */
async function pathExists(path: string): Promise<boolean> {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

export async function POST(request: NextRequest) {
  let body: ValidationRequest;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json<ValidationResponse>(
      {
        path_validated: false,
        claude_dir_exists: false,
        path_error: "Invalid request body",
      },
      { status: 400 }
    );
  }

  const { path: rawPath } = body;

  if (!rawPath) {
    return NextResponse.json<ValidationResponse>({
      path_validated: false,
      claude_dir_exists: false,
      path_error: "Path is required",
    });
  }

  // Expand and normalize path
  const expandedPath = normalize(expandPath(rawPath));

  // Check if path exists
  const exists = await pathExists(expandedPath);
  if (!exists) {
    return NextResponse.json<ValidationResponse>({
      path_validated: false,
      claude_dir_exists: false,
      path_error: "Path does not exist",
    });
  }

  // Check if path is a directory
  const isDir = await isDirectory(expandedPath);
  if (!isDir) {
    return NextResponse.json<ValidationResponse>({
      path_validated: false,
      claude_dir_exists: false,
      path_error: "Path is not a directory",
    });
  }

  // Check for .claude directory
  const claudeDirPath = join(expandedPath, ".claude");
  const claudeDirExists = await isDirectory(claudeDirPath);

  return NextResponse.json<ValidationResponse>({
    path_validated: true,
    claude_dir_exists: claudeDirExists,
    path_error: null,
  });
}
