/**
 * API client composable with error handling, interceptors, and caching.
 */
import { ref, readonly } from 'vue'

// Types
export interface ApiError {
  message: string
  status: number
  data?: unknown
}

export interface ApiResponse<T> {
  data: T | null
  error: ApiError | null
  status: number
}

export interface RequestConfig {
  headers?: Record<string, string>
  params?: Record<string, string | number | boolean>
  timeout?: number
  retry?: number
  cache?: boolean
  cacheTTL?: number
}

// Global state
const isLoading = ref(false)
const authToken = ref<string | null>(null)

// Simple in-memory cache
const cache = new Map<string, { data: unknown; expiry: number }>()

/**
 * API client composable
 */
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  /**
   * Set authentication token
   */
  function setAuthToken(token: string | null) {
    authToken.value = token
    if (token) {
      localStorage.setItem('auth_token', token)
    } else {
      localStorage.removeItem('auth_token')
    }
  }

  /**
   * Get authentication token
   */
  function getAuthToken(): string | null {
    if (!authToken.value) {
      authToken.value = localStorage.getItem('auth_token')
    }
    return authToken.value
  }

  /**
   * Build request headers
   */
  function buildHeaders(customHeaders?: Record<string, string>): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }

    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return headers
  }

  /**
   * Build URL with query parameters
   */
  function buildUrl(path: string, params?: Record<string, string | number | boolean>): string {
    const url = new URL(path, baseURL)

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value))
        }
      })
    }

    return url.toString()
  }

  /**
   * Get cache key
   */
  function getCacheKey(method: string, url: string): string {
    return `${method}:${url}`
  }

  /**
   * Get from cache
   */
  function getFromCache<T>(key: string): T | null {
    const entry = cache.get(key)
    if (!entry) return null

    if (Date.now() > entry.expiry) {
      cache.delete(key)
      return null
    }

    return entry.data as T
  }

  /**
   * Set cache
   */
  function setCache(key: string, data: unknown, ttl: number): void {
    cache.set(key, {
      data,
      expiry: Date.now() + ttl,
    })
  }

  /**
   * Clear cache
   */
  function clearCache(pattern?: string): void {
    if (!pattern) {
      cache.clear()
      return
    }

    for (const key of cache.keys()) {
      if (key.includes(pattern)) {
        cache.delete(key)
      }
    }
  }

  /**
   * Handle API response
   */
  async function handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const status = response.status

    if (!response.ok) {
      let errorData: unknown
      try {
        errorData = await response.json()
      } catch {
        errorData = { message: response.statusText }
      }

      const error: ApiError = {
        message: (errorData as { detail?: string })?.detail || response.statusText,
        status,
        data: errorData,
      }

      // Handle specific status codes
      if (status === 401) {
        setAuthToken(null)
      }

      return { data: null, error, status }
    }

    try {
      const data = await response.json() as T
      return { data, error: null, status }
    } catch {
      return { data: null, error: null, status }
    }
  }

  /**
   * Make API request
   */
  async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    requestConfig: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      headers: customHeaders,
      params,
      timeout = 30000,
      retry = 0,
      cache: useCache = false,
      cacheTTL = 5 * 60 * 1000, // 5 minutes
    } = requestConfig

    // Check cache for GET requests
    if (method === 'GET' && useCache) {
      const url = buildUrl(path, params)
      const cacheKey = getCacheKey(method, url)
      const cached = getFromCache<T>(cacheKey)
      if (cached) {
        return { data: cached, error: null, status: 200 }
      }
    }

    isLoading.value = true

    const url = buildUrl(path, params)
    const headers = buildHeaders(customHeaders)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    let lastError: ApiError | null = null

    for (let attempt = 0; attempt <= retry; attempt++) {
      try {
        const response = await fetch(url, {
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        })

        clearTimeout(timeoutId)
        const result = await handleResponse<T>(response)

        // Cache successful GET requests
        if (method === 'GET' && useCache && result.data && result.status === 200) {
          const cacheKey = getCacheKey(method, url)
          setCache(cacheKey, result.data, cacheTTL)
        }

        isLoading.value = false
        return result
      } catch (error) {
        lastError = {
          message: error instanceof Error ? error.message : 'Network error',
          status: 0,
        }

        if (attempt < retry) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000))
        }
      }
    }

    clearTimeout(timeoutId)
    isLoading.value = false

    return {
      data: null,
      error: lastError,
      status: 0,
    }
  }

  /**
   * GET request
   */
  async function get<T>(path: string, requestConfig?: RequestConfig): Promise<ApiResponse<T>> {
    return request<T>('GET', path, undefined, requestConfig)
  }

  /**
   * POST request
   */
  async function post<T>(path: string, body?: unknown, requestConfig?: RequestConfig): Promise<ApiResponse<T>> {
    return request<T>('POST', path, body, requestConfig)
  }

  /**
   * PUT request
   */
  async function put<T>(path: string, body?: unknown, requestConfig?: RequestConfig): Promise<ApiResponse<T>> {
    return request<T>('PUT', path, body, requestConfig)
  }

  /**
   * DELETE request
   */
  async function del<T>(path: string, requestConfig?: RequestConfig): Promise<ApiResponse<T>> {
    return request<T>('DELETE', path, undefined, requestConfig)
  }

  /**
   * Upload file
   */
  async function upload<T>(path: string, file: File, requestConfig?: RequestConfig): Promise<ApiResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    isLoading.value = true

    const url = buildUrl(path)
    const headers: Record<string, string> = {}

    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      })

      isLoading.value = false
      return handleResponse<T>(response)
    } catch (error) {
      isLoading.value = false
      return {
        data: null,
        error: {
          message: error instanceof Error ? error.message : 'Upload failed',
          status: 0,
        },
        status: 0,
      }
    }
  }

  return {
    isLoading: readonly(isLoading),
    authToken: readonly(authToken),
    setAuthToken,
    getAuthToken,
    get,
    post,
    put,
    del,
    upload,
    request,
    clearCache,
  }
}
