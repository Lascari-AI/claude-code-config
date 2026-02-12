import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Status color utilities for consistent badge/indicator styling.
 */

/**
 * Get Tailwind color classes for project status badges.
 */
export function getProjectStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    onboarding: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    pending: "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400",
    paused: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    archived: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  };
  return colors[status] || colors.pending;
}

/**
 * Get Tailwind color classes for session phase status indicators.
 */
export function getPhaseStatusColor(status: "complete" | "in_progress" | "pending"): string {
  const colors: Record<string, string> = {
    complete: "bg-green-500",
    in_progress: "bg-blue-500 animate-pulse",
    pending: "bg-gray-300 dark:bg-gray-600",
  };
  return colors[status] || colors.pending;
}

/**
 * Get Tailwind color classes for session status badges.
 */
export function getSessionStatusColor(status: string): string {
  const colors: Record<string, string> = {
    created: "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400",
    spec: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    spec_done: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    plan: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
    plan_done: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
    build: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
    docs: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    complete: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    failed: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    paused: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  };
  return colors[status] || colors.created;
}

/**
 * Get Tailwind color classes for agent status badges.
 */
export function getAgentStatusColorUtil(status: string): string {
  const colors: Record<string, string> = {
    pending: "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400",
    queued: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    executing: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
    complete: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    failed: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    cancelled: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  };
  return colors[status] || colors.pending;
}
