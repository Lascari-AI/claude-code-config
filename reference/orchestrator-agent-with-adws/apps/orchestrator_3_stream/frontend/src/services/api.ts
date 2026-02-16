/**
 * API Configuration
 *
 * Axios instance configured with base URL and interceptors
 */

import axios from 'axios'

// Get base URL from environment variables
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:9403'

// Create axios instance
export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)

    if (error.response) {
      // Server responded with error status
      console.error('Response data:', error.response.data)
      console.error('Response status:', error.response.status)
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received:', error.request)
    } else {
      // Error in request setup
      console.error('Request setup error:', error.message)
    }

    return Promise.reject(error)
  }
)
