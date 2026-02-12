/**
 * API Client Configuration
 *
 * Base configuration and fetch wrapper for API requests.
 */

/**
 * Base URL for the API.
 * Configured via NEXT_PUBLIC_API_URL environment variable.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Fetch wrapper with error handling and JSON parsing.
 *
 * @param endpoint - API endpoint (relative to base URL)
 * @param options - Fetch options
 * @returns Parsed JSON response
 * @throws ApiError on non-2xx responses
 */
export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  // Handle no content responses (e.g., DELETE)
  if (response.status === 204) {
    return undefined as T;
  }

  // Parse response body
  let data: T | { detail: string };
  try {
    data = await response.json();
  } catch {
    throw new ApiError(
      "Failed to parse response",
      response.status,
      "Invalid JSON response"
    );
  }

  // Handle error responses
  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? (data as { detail: string }).detail
        : undefined;

    throw new ApiError(
      `API request failed: ${response.statusText}`,
      response.status,
      detail
    );
  }

  return data as T;
}
