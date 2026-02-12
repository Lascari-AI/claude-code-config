"use client";

/**
 * DirectoryBrowser Component
 *
 * A file browser for selecting project directories.
 * Fetches directory listings from the backend API.
 */

import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  browseDirectories,
  type DirectoryEntry,
  type BrowseResponse,
} from "@/lib/projects-api";

interface DirectoryBrowserProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (path: string) => void;
  initialPath?: string;
}

/**
 * Directory browser dialog for selecting a project path.
 *
 * Features:
 * - Navigate directories
 * - Shows .claude indicator for Claude-configured projects
 * - Type path directly or click to navigate
 */
export function DirectoryBrowser({
  open,
  onOpenChange,
  onSelect,
  initialPath = "~",
}: DirectoryBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [inputPath, setInputPath] = useState(initialPath);
  const [data, setData] = useState<BrowseResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  // Fetch directory listing
  const fetchDirectory = useCallback(async (path: string) => {
    setIsLoading(true);
    try {
      const result = await browseDirectories(path);
      setData(result);
      setCurrentPath(result.current_path);
      setInputPath(result.current_path);
      setSelectedPath(null);
    } catch (err) {
      console.error("Failed to browse directory:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load initial directory when dialog opens
  useEffect(() => {
    if (open) {
      fetchDirectory(initialPath);
    }
  }, [open, initialPath, fetchDirectory]);

  // Navigate to a directory
  const handleNavigate = (path: string) => {
    fetchDirectory(path);
  };

  // Handle path input submission
  const handlePathSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputPath.trim()) {
      fetchDirectory(inputPath.trim());
    }
  };

  // Handle directory selection (single click)
  const handleSelect = (entry: DirectoryEntry) => {
    setSelectedPath(entry.path);
  };

  // Handle directory open (double click)
  const handleOpen = (entry: DirectoryEntry) => {
    if (entry.is_directory) {
      handleNavigate(entry.path);
    }
  };

  // Confirm selection
  const handleConfirm = () => {
    if (selectedPath) {
      onSelect(selectedPath);
      onOpenChange(false);
    }
  };

  // Select current directory
  const handleSelectCurrent = () => {
    onSelect(currentPath);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] h-[500px] flex flex-col">
        <DialogHeader>
          <DialogTitle>Browse for Project</DialogTitle>
          <DialogDescription>
            Navigate to your project directory. Directories with a{" "}
            <Badge variant="secondary" className="text-xs">
              .claude
            </Badge>{" "}
            badge are already configured.
          </DialogDescription>
        </DialogHeader>

        {/* Path Input */}
        <form onSubmit={handlePathSubmit} className="flex gap-2">
          <Input
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            placeholder="/path/to/project"
            className="font-mono text-sm flex-1"
          />
          <Button type="submit" variant="outline" disabled={isLoading}>
            Go
          </Button>
        </form>

        {/* Directory Listing */}
        <div className="flex-1 min-h-0 border rounded-md">
          <ScrollArea className="h-full">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <LoadingSpinner className="w-6 h-6 text-muted-foreground" />
              </div>
            ) : data?.error ? (
              <div className="p-4 text-sm text-destructive">{data.error}</div>
            ) : (
              <div className="p-1">
                {/* Parent directory */}
                {data?.parent_path && (
                  <button
                    onClick={() => handleNavigate(data.parent_path!)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted rounded-md text-left"
                  >
                    <ParentIcon className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground">..</span>
                  </button>
                )}

                {/* Directory entries */}
                {data?.entries.map((entry) => (
                  <button
                    key={entry.path}
                    onClick={() => handleSelect(entry)}
                    onDoubleClick={() => handleOpen(entry)}
                    className={cn(
                      "w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted rounded-md text-left",
                      selectedPath === entry.path && "bg-muted"
                    )}
                  >
                    <FolderIcon
                      className={cn(
                        "w-4 h-4",
                        entry.has_claude_dir
                          ? "text-blue-500"
                          : "text-muted-foreground"
                      )}
                    />
                    <span className="flex-1 truncate">{entry.name}</span>
                    {entry.has_claude_dir && (
                      <Badge variant="secondary" className="text-xs">
                        .claude
                      </Badge>
                    )}
                  </button>
                ))}

                {/* Empty state */}
                {data?.entries.length === 0 && !data?.error && (
                  <div className="p-4 text-sm text-muted-foreground text-center">
                    No subdirectories found
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Current path display */}
        <div className="text-xs text-muted-foreground font-mono truncate">
          Current: {currentPath}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={handleSelectCurrent}
          >
            Select Current Folder
          </Button>
          <Button
            type="button"
            onClick={handleConfirm}
            disabled={!selectedPath}
          >
            Select
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("animate-spin", className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
      />
    </svg>
  );
}

function ParentIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 10h18M3 10l6-6m-6 6l6 6"
      />
    </svg>
  );
}
