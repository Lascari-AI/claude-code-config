/**
 * Project TypeScript Interfaces
 *
 * Type definitions matching the backend API models.
 */

/**
 * Full project entity with all fields.
 */
export interface Project {
  id: string;
  name: string;
  slug: string;
  path: string;
  repo_url: string | null;
  status: ProjectStatus;
  onboarding_status: OnboardingStatus;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * Lightweight project info for list views.
 */
export interface ProjectSummary {
  id: string;
  name: string;
  slug: string;
  status: string;
  path: string;
  created_at: string;
  updated_at: string;
}

/**
 * Project lifecycle status.
 */
export type ProjectStatus =
  | "pending"
  | "onboarding"
  | "active"
  | "paused"
  | "archived";

/**
 * Onboarding steps tracking.
 */
export interface OnboardingStatus {
  path_validated: boolean;
  claude_dir_exists: boolean;
  settings_configured: boolean;
  skills_linked: boolean;
  agents_linked: boolean;
  docs_foundation: boolean;
}

/**
 * DTO for creating a new project.
 */
export interface ProjectCreate {
  name: string;
  slug: string;
  path: string;
  repo_url?: string;
  status?: ProjectStatus;
  onboarding_status?: Partial<OnboardingStatus>;
  metadata_?: Record<string, unknown>;
}

/**
 * DTO for updating a project (all fields optional).
 */
export interface ProjectUpdate {
  name?: string;
  slug?: string;
  path?: string;
  repo_url?: string | null;
  status?: ProjectStatus;
  onboarding_status?: Partial<OnboardingStatus>;
  metadata_?: Record<string, unknown>;
}
