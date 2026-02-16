/**
 * Directory Browser API Route
 *
 * Server-side filesystem browsing for project selection.
 * Runs on Node.js, allowing direct filesystem access.
 */

import { NextRequest, NextResponse } from "next/server";
import { readdir, stat } from "fs/promises";
import { join, dirname, normalize } from "path";
import { homedir } from "os";

interface DirectoryEntry {
  name: string;
  path: string;
  is_directory: boolean;
  has_claude_dir: boolean;
}

interface BrowseResponse {
  current_path: string;
  parent_path: string | null;
  entries: DirectoryEntry[];
  error: string | null;
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
 * Check if a directory contains a .claude subdirectory
 */
async function hasClaudeDir(path: string): Promise<boolean> {
  return isDirectory(join(path, ".claude"));
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const rawPath = searchParams.get("path") || "~";

  // Expand and normalize path
  const expandedPath = normalize(expandPath(rawPath));

  // Security: block system directories
  const blockedPrefixes = ["/proc", "/sys", "/dev"];
  for (const blocked of blockedPrefixes) {
    if (expandedPath.startsWith(blocked)) {
      return NextResponse.json<BrowseResponse>({
        current_path: expandedPath,
        parent_path: null,
        entries: [],
        error: "Access to system directories is not allowed",
      });
    }
  }

  // Check if path exists
  try {
    const stats = await stat(expandedPath);
    if (!stats.isDirectory()) {
      return NextResponse.json<BrowseResponse>({
        current_path: expandedPath,
        parent_path: dirname(expandedPath),
        entries: [],
        error: "Path is not a directory",
      });
    }
  } catch {
    return NextResponse.json<BrowseResponse>({
      current_path: expandedPath,
      parent_path: dirname(expandedPath),
      entries: [],
      error: "Path does not exist",
    });
  }

  // Get parent path (null if at root)
  const parentPath = dirname(expandedPath);
  const isRoot = parentPath === expandedPath;

  // Read directory contents
  try {
    const items = await readdir(expandedPath);
    const entries: DirectoryEntry[] = [];

    for (const name of items.sort()) {
      // Skip hidden files/directories
      if (name.startsWith(".")) {
        continue;
      }

      const itemPath = join(expandedPath, name);

      // Only include directories
      if (await isDirectory(itemPath)) {
        entries.push({
          name,
          path: itemPath,
          is_directory: true,
          has_claude_dir: await hasClaudeDir(itemPath),
        });
      }
    }

    return NextResponse.json<BrowseResponse>({
      current_path: expandedPath,
      parent_path: isRoot ? null : parentPath,
      entries,
      error: null,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";

    if (message.includes("EACCES") || message.includes("permission")) {
      return NextResponse.json<BrowseResponse>({
        current_path: expandedPath,
        parent_path: isRoot ? null : parentPath,
        entries: [],
        error: "Permission denied",
      });
    }

    return NextResponse.json<BrowseResponse>({
      current_path: expandedPath,
      parent_path: isRoot ? null : parentPath,
      entries: [],
      error: `Failed to read directory: ${message}`,
    });
  }
}
