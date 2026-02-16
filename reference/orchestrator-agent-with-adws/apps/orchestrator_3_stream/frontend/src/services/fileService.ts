/**
 * File Service
 *
 * Provides functionality for opening files in IDE and managing file operations
 */

import { apiClient } from './api'

export interface OpenFileResponse {
  status: 'success' | 'error'
  message?: string
  file_path?: string
}

/**
 * Open a file in the configured IDE (Cursor or VS Code)
 * @param absolutePath - Absolute path to the file
 * @returns Promise<OpenFileResponse>
 */
export async function openFileInIDE(absolutePath: string): Promise<OpenFileResponse> {
  try {
    const response = await apiClient.post<OpenFileResponse>('/api/open-file', {
      file_path: absolutePath
    })

    if (response.data.status === 'success') {
      console.log(`[FileService] Opened file in IDE: ${absolutePath}`)
      return response.data
    } else {
      console.error(`[FileService] Failed to open file: ${response.data.message}`)
      return response.data
    }
  } catch (error: any) {
    console.error('[FileService] Error opening file in IDE:', error)
    return {
      status: 'error',
      message: error.response?.data?.message || error.message || 'Failed to open file in IDE'
    }
  }
}

/**
 * Check if IDE integration is available
 * @returns Promise<boolean>
 */
export async function isIDEAvailable(): Promise<boolean> {
  try {
    // Try to open a test file (doesn't actually open, just checks availability)
    const response = await apiClient.post<OpenFileResponse>('/api/open-file', {
      file_path: '/dev/null'
    })

    return response.data.status !== 'error' ||
           !response.data.message?.includes('disabled')
  } catch (error) {
    return false
  }
}

export default {
  openFileInIDE,
  isIDEAvailable
}
