/**
 * Virtual scroll composable for efficient rendering of large lists.
 * Only renders visible items + buffer, dramatically reducing DOM nodes.
 */
import { ref, computed, onMounted, onUnmounted, watch, type Ref } from 'vue'

// Types
export interface VirtualScrollOptions {
  /** Height of each item in pixels */
  itemHeight: number
  /** Number of items to render outside viewport (buffer) */
  bufferCount?: number
  /** Container element ref */
  containerRef: Ref<HTMLElement | null>
  /** Items array */
  items: Ref<unknown[]>
  /** Enable smooth scrolling */
  smoothScroll?: boolean
}

export interface VirtualScrollReturn {
  /** Items to render (visible + buffer) */
  visibleItems: Ref<unknown[]>
  /** Starting index of visible items */
  startIndex: Ref<number>
  /** Total height of all items */
  totalHeight: Ref<number>
  /** Offset top for positioning */
  offsetY: Ref<number>
  /** Scroll to specific index */
  scrollToIndex: (index: number) => void
  /** Scroll to top */
  scrollToTop: () => void
  /** Current scroll position */
  scrollTop: Ref<number>
  /** Is user at bottom */
  isAtBottom: Ref<boolean>
  /** Is user at top */
  isAtTop: Ref<boolean>
}

/**
 * Virtual scroll composable
 */
export function useVirtualScroll(options: VirtualScrollOptions): VirtualScrollReturn {
  const {
    itemHeight,
    bufferCount = 5,
    containerRef,
    items,
    smoothScroll = false,
  } = options

  // State
  const scrollTop = ref(0)
  const containerHeight = ref(0)

  // Computed
  const totalHeight = computed(() => items.value.length * itemHeight)

  const startIndex = computed(() => {
    const index = Math.floor(scrollTop.value / itemHeight)
    return Math.max(0, index - bufferCount)
  })

  const endIndex = computed(() => {
    if (!containerHeight.value) return startIndex.value + bufferCount * 2
    const visibleCount = Math.ceil(containerHeight.value / itemHeight)
    return Math.min(items.value.length, startIndex.value + visibleCount + bufferCount * 2)
  })

  const visibleItems = computed(() =>
    items.value.slice(startIndex.value, endIndex.value)
  )

  const offsetY = computed(() => startIndex.value * itemHeight)

  const isAtTop = computed(() => scrollTop.value <= 0)
  const isAtBottom = computed(() => {
    if (!containerRef.value) return false
    const el = containerRef.value
    return scrollTop.value + containerHeight.value >= el.scrollHeight - 10
  })

  // Handlers
  function handleScroll() {
    if (!containerRef.value) return
    scrollTop.value = containerRef.value.scrollTop
  }

  function handleResize() {
    if (!containerRef.value) return
    containerHeight.value = containerRef.value.clientHeight
  }

  // Actions
  function scrollToIndex(index: number) {
    if (!containerRef.value) return
    const targetTop = index * itemHeight
    containerRef.value.scrollTo({
      top: targetTop,
      behavior: smoothScroll ? 'smooth' : 'instant',
    })
  }

  function scrollToTop() {
    if (!containerRef.value) return
    containerRef.value.scrollTo({
      top: 0,
      behavior: smoothScroll ? 'smooth' : 'instant',
    })
  }

  // Lifecycle
  let resizeObserver: ResizeObserver | null = null

  onMounted(() => {
    if (!containerRef.value) return

    containerRef.value.addEventListener('scroll', handleScroll, { passive: true })
    containerHeight.value = containerRef.value.clientHeight

    resizeObserver = new ResizeObserver(() => handleResize())
    resizeObserver.observe(containerRef.value)
  })

  onUnmounted(() => {
    if (containerRef.value) {
      containerRef.value.removeEventListener('scroll', handleScroll)
    }
    resizeObserver?.disconnect()
  })

  // Watch for container changes
  watch(containerRef, (newEl, oldEl) => {
    if (oldEl) {
      oldEl.removeEventListener('scroll', handleScroll)
      resizeObserver?.unobserve(oldEl)
    }
    if (newEl) {
      newEl.addEventListener('scroll', handleScroll, { passive: true })
      containerHeight.value = newEl.clientHeight
      resizeObserver?.observe(newEl)
    }
  })

  return {
    visibleItems,
    startIndex,
    totalHeight,
    offsetY,
    scrollToIndex,
    scrollToTop,
    scrollTop,
    isAtBottom,
    isAtTop,
  }
}
