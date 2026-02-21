"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Folder, Loader2, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { getProjects } from "@/lib/projects-api";
import { getProjectSessions } from "@/lib/sessions-api";
import { Button } from "@/components/ui/button";
import { OnboardingDialog } from "@/components/projects";
import type { ProjectSummary } from "@/types/project";
import type { SessionSummary, SessionStatus } from "@/types/session";

const SESSION_PREVIEW_LIMIT = 5;
const SESSION_FETCH_LIMIT = SESSION_PREVIEW_LIMIT + 1;

function getSessionDotColor(status: SessionStatus): string {
  if (status === "complete" || status === "docs") return "bg-green-500";
  if (status === "failed") return "bg-red-500";
  if (status === "plan" || status === "plan_done") return "bg-violet-500";
  if (status === "build") return "bg-amber-500";
  if (status === "spec" || status === "spec_done") return "bg-blue-500";
  return "bg-muted-foreground/50";
}

function getCompactAge(dateString: string | null | undefined): string {
  if (!dateString) return "--";

  // Handle PostgreSQL timestamp formats: "2026-02-21 10:05:22" or ISO 8601
  const normalized = dateString.includes("T") ? dateString : dateString.replace(" ", "T");
  const timestamp = new Date(normalized).getTime();
  const diffMs = Date.now() - timestamp;

  if (Number.isNaN(timestamp) || diffMs < 0) return "--";

  const totalMinutes = Math.floor(diffMs / (1000 * 60));
  if (totalMinutes < 1) return "now";

  const totalHours = Math.floor(totalMinutes / 60);
  if (totalHours < 1) return `${totalMinutes}m`;

  const days = Math.floor(totalHours / 24);
  const remainingHours = totalHours % 24;

  if (days === 0) return `${remainingHours}h`;
  if (days < 100) return `${days}d ${remainingHours}h`;
  return `${days}d`;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [sessionsByProject, setSessionsByProject] = useState<Record<string, SessionSummary[]>>(
    {},
  );
  const [hasMoreByProject, setHasMoreByProject] = useState<Record<string, boolean>>({});
  const [isLoadingSidebar, setIsLoadingSidebar] = useState(false);
  const [sidebarError, setSidebarError] = useState<string | null>(null);

  const activeRoute = useMemo(() => {
    const parts = pathname.split("/").filter(Boolean);
    if (parts[0] !== "projects") {
      return { projectSlug: null, sessionSlug: null };
    }
    return {
      projectSlug: parts[1] ?? null,
      sessionSlug: parts[2] === "sessions" ? (parts[3] ?? null) : null,
    };
  }, [pathname]);

  const loadSidebar = useCallback(async () => {
    setIsLoadingSidebar(true);
    setSidebarError(null);
    try {
      const projectList = await getProjects();
      setProjects(projectList);

      const perProject = await Promise.all(
        projectList.map(async (project) => {
          try {
            const sessions = await getProjectSessions(project.id, {
              limit: SESSION_FETCH_LIMIT,
            });
            return {
              projectId: project.id,
              sessions: sessions.slice(0, SESSION_PREVIEW_LIMIT),
              hasMore: sessions.length > SESSION_PREVIEW_LIMIT,
            };
          } catch {
            return {
              projectId: project.id,
              sessions: [] as SessionSummary[],
              hasMore: false,
            };
          }
        }),
      );

      setSessionsByProject(
        Object.fromEntries(perProject.map((entry) => [entry.projectId, entry.sessions])),
      );
      setHasMoreByProject(
        Object.fromEntries(perProject.map((entry) => [entry.projectId, entry.hasMore])),
      );
    } catch (error) {
      setSidebarError(
        error instanceof Error ? error.message : "Failed to load sidebar data",
      );
    } finally {
      setIsLoadingSidebar(false);
    }
  }, []);

  // Re-fetch sidebar data on every route change so sessions stay fresh
  useEffect(() => {
    loadSidebar();
  }, [loadSidebar, pathname]);

  // Also refresh when the browser tab regains focus (e.g. after working in terminal)
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        loadSidebar();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [loadSidebar]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-muted/40 via-background to-muted/15">
      <div className="flex min-h-screen w-full">
        <aside className="hidden w-80 shrink-0 border-r border-border/70 bg-background/85 backdrop-blur lg:flex lg:flex-col">
          <div className="border-b border-border/60 px-5 py-5">
            <Link href="/projects" className="block">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Lascari AI
              </p>
              <h1 className="mt-1 text-xl font-semibold tracking-tight">Sessions</h1>
            </Link>
            <div className="mt-4">
              <OnboardingDialog
                onSuccess={loadSidebar}
                trigger={(
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Project
                  </Button>
                )}
              />
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto px-3 py-4">
            {isLoadingSidebar && projects.length === 0 && (
              <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading sidebar...
              </div>
            )}

            {sidebarError && (
              <p className="px-3 py-2 text-sm text-destructive">{sidebarError}</p>
            )}

            {!isLoadingSidebar && !sidebarError && projects.length === 0 && (
              <p className="px-3 py-2 text-sm text-muted-foreground">
                No projects found.
              </p>
            )}

            <section>
              <h2 className="px-3 pb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Projects
              </h2>
              <ul className="space-y-1">
                {projects.map((project) => {
                  const projectIsActive = activeRoute.projectSlug === project.slug;
                  return (
                    <li key={project.id}>
                      <Link
                        href={`/projects/${project.slug}`}
                        className={cn(
                          "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors",
                          projectIsActive
                            ? "bg-muted text-foreground"
                            : "text-foreground/90 hover:bg-muted/60",
                        )}
                      >
                        <Folder className="h-4 w-4 text-muted-foreground" />
                        <span className="truncate">{project.name}</span>
                      </Link>

                      <div className="mt-1 space-y-1">
                        {(sessionsByProject[project.id] ?? []).map((session) => {
                          const isActiveSession =
                            activeRoute.projectSlug === project.slug &&
                            activeRoute.sessionSlug === session.session_slug;
                          const displayTitle = session.title || session.session_slug;
                          const age = getCompactAge(session.updated_at);
                          return (
                            <Link
                              key={session.id}
                              href={`/projects/${project.slug}/sessions/${session.session_slug}`}
                              className={cn(
                                "flex items-center gap-2 rounded-md py-1.5 transition-colors",
                                isActiveSession
                                  ? "bg-muted text-foreground"
                                  : "text-foreground/90 hover:bg-muted/60",
                              )}
                            >
                              <span className="w-[1.5rem] shrink-0 text-right font-mono text-[10px] leading-tight text-muted-foreground">
                                {age}
                              </span>
                              <span
                                className={cn(
                                  "h-1.5 w-1.5 shrink-0 rounded-full",
                                  getSessionDotColor(session.status),
                                )}
                              />
                              <span className="min-w-0 flex-1 truncate text-sm">
                                {displayTitle}
                              </span>
                            </Link>
                          );
                        })}

                        {!isLoadingSidebar && (sessionsByProject[project.id] ?? []).length === 0 && (
                          <p className="px-2 py-1 text-xs text-muted-foreground">
                            No sessions yet
                          </p>
                        )}

                        {hasMoreByProject[project.id] && (
                          <Link
                            href={`/projects/${project.slug}`}
                            className="block px-2 py-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
                          >
                            render more
                          </Link>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>
          </div>
        </aside>

        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-40 border-b border-border/70 bg-background/95 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80 lg:hidden">
            <div className="flex items-center justify-between">
              <Link href="/projects" className="text-sm font-semibold tracking-tight">
                LAI Session Manager
              </Link>
              <Link
                href="/projects"
                className="rounded-md px-2 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Projects
              </Link>
            </div>
          </header>

          <main className="flex-1 px-4 py-6 sm:px-8 sm:py-8 lg:px-10">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
