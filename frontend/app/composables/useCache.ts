/**
 * Caching composable with TTL, invalidation, and stale-while-revalidate.
 */
import { ref, readonly } from 'vue'

// Types
export interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
  staleTTL: number
  key: string
}

export interface CacheOptions {
  ttl?: number // Time to live in ms
  staleTTL?: number // Stale-while-revalidate window in ms
  maxSize?: number // Maximum cache entries
  persist?: boolean // Persist to localStorage
  storageKey?: string // localStorage key prefix
}

// Default options
const DEFAULT_OPTIONS: Required<CacheOptions> = {
  ttl: 5 * 60 * 1000, // 5 minutes
  staleTTL: 10 * 60 * 1000, // 10 minutes stale window
  maxSize: 100,
  persist: false,
  storageKey: 'app_cache',
}

/**
 * Cache composable
 */
export function useCache(options: CacheOptions = {}) {
  const config = { ...DEFAULT_OPTIONS, ...options }

  // In-memory cache
  const cache = new Map<string, CacheEntry<unknown>>()

  // Stats
  const hits = ref(0)
  const misses = ref(0)

  /**
   * Load cache from localStorage
   */
  function loadFromStorage(): void {
    if (!config.persist) return

    try {
      const stored = localStorage.getItem(config.storageKey)
      if (stored) {
        const entries = JSON.parse(stored) as Record<string, CacheEntry<unknown>>
        Object.entries(entries).forEach(([key, entry]) => {
          cache.set(key, entry)
        })
      }
    } catch (e) {
      console.warn('Failed to load cache from storage:', e)
    }
  }

  /**
   * Save cache to localStorage
   */
  function saveToStorage(): void {
    if (!config.persist) return

    try {
      const entries: Record<string, CacheEntry<unknown>> = {}
      cache.forEach((value, key) => {
        entries[key] = value
      })
      localStorage.setItem(config.storageKey, JSON.stringify(entries))
    } catch (e) {
      console.warn('Failed to save cache to storage:', e)
    }
  }

  /**
   * Check if entry is expired
   */
  function isExpired(entry: CacheEntry<unknown>): boolean {
    return Date.now() > entry.timestamp + entry.ttl
  }

  /**
   * Check if entry is stale (but within stale window)
   */
  function isStale(entry: CacheEntry<unknown>): boolean {
    return Date.now() > entry.timestamp + entry.ttl && 
           Date.now() <= entry.timestamp + entry.staleTTL
  }

  /**
   * Get from cache
   */
  function get<T>(key: string): { data: T | null; isStale: boolean } {
    const entry = cache.get(key) as CacheEntry<T> | undefined

    if (!entry) {
      misses.value++
      return { data: null, isStale: false }
    }

    // Check if completely expired
    if (Date.now() > entry.timestamp + entry.staleTTL) {
      cache.delete(key)
      misses.value++
      return { data: null, isStale: false }
    }

    hits.value++
    return {
      data: entry.data,
      isStale: isStale(entry),
    }
  }

  /**
   * Set cache entry
   */
  function set<T>(key: string, data: T, options?: { ttl?: number; staleTTL?: number }): void {
    // Enforce max size
    if (cache.size >= config.maxSize) {
      // Remove oldest entry
      const firstKey = cache.keys().next().value
      if (firstKey) {
        cache.delete(firstKey)
      }
    }

    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl: options?.ttl ?? config.ttl,
      staleTTL: options?.staleTTL ?? config.staleTTL,
      key,
    }

    cache.set(key, entry)
    saveToStorage()
  }

  /**
   * Delete cache entry
   */
  function del(key: string): boolean {
    const deleted = cache.delete(key)
    if (deleted) saveToStorage()
    return deleted
  }

  /**
   * Invalidate cache entries by pattern
   */
  function invalidate(pattern: string | RegExp): number {
    let count = 0
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern

    for (const key of cache.keys()) {
      if (regex.test(key)) {
        cache.delete(key)
        count++
      }
    }

    if (count > 0) saveToStorage()
    return count
  }

  /**
   * Clear all cache
   */
  function clear(): void {
    cache.clear()
    if (config.persist) {
      localStorage.removeItem(config.storageKey)
    }
  }

  /**
   * Get cache stats
   */
  function getStats() {
    return {
      size: cache.size,
      hits: hits.value,
      misses: misses.value,
      hitRate: hits.value + misses.value > 0 
        ? (hits.value / (hits.value + misses.value) * 100).toFixed(1) + '%'
        : '0%',
    }
  }

  /**
   * Fetch with cache (stale-while-revalidate pattern)
   */
  async function fetchWithCache<T>(
    key: string,
    fetcher: () => Promise<T>,
    options?: { ttl?: number; staleTTL?: number }
  ): Promise<T> {
    const cached = get<T>(key)

    // Return fresh data immediately
    if (cached.data && !cached.isStale) {
      return cached.data
    }

    // If stale, return stale data but revalidate in background
    if (cached.data && cached.isStale) {
      // Background revalidation
      fetcher().then(data => {
        set(key, data, options)
      }).catch(e => {
        console.warn('Background revalidation failed:', e)
      })

      return cached.data
    }

    // No cache, fetch fresh
    const data = await fetcher()
    set(key, data, options)
    return data
  }

  // Load persisted cache on init
  loadFromStorage()

  return {
    // State
    hits: readonly(hits),
    misses: readonly(misses),

    // Actions
    get,
    set,
    del,
    invalidate,
    clear,
    getStats,
    fetchWithCache,
  }
}
