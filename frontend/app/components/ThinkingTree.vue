<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useTreeStore } from '../stores/tree'
import * as d3 from 'd3'
import { gsap } from 'gsap'
import type { TreeNode } from '../stores/tree'
import ExportDialog from './ExportDialog.vue'
import TreeNodeEditor from './TreeNodeEditor.vue'
import TreeSetup from './TreeSetup.vue'
import AudioRecorder from './AudioRecorder.vue'

type RenderNode = {
  data: TreeNode
  depth: number
  x: number
  y: number
  parent: RenderNode | null
}

type SetupDirection = {
  id: string
  name: string
  emoji: string
  children?: SetupDirection[]
  metadata?: Record<string, unknown>
}

const treeStore = useTreeStore()
const treeContainer = ref<HTMLElement | null>(null)
const perfMetrics = ref('Render Time: 0 ms')
const showExportDialog = ref(false)
const showSetup = ref(true)
const showEditor = ref(false)
const showRecorder = ref(false)
const selectedNode = ref<TreeNode | null>(null)
const editorPosition = ref({ x: 0, y: 0 })
const isNewNode = ref(false)
const isAnalyzing = ref(false)
const aiResponse = ref<any>(null)
const recordingError = ref('')
const similarNodes = ref<{ id: string; label: string }[]>([])
const pendingNode = ref<{ node: TreeNode; parentId: string } | null>(null)

let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>
let gContainer: d3.Selection<SVGGElement, unknown, null, undefined>
let currentZoom: d3.ZoomBehavior<SVGSVGElement, unknown>
let resizeTimeout: number | undefined

function normalizeDebateTreeShape(nodes: TreeNode[]) {
  const root = nodes[0]
  if (!root || root.metadata?.treeMode !== 'debate') return nodes

  const children = root.children || []
  const hasOldStanceLayer = children.some((node) => node.metadata?.debateLevel === 'stance')
  if (!hasOldStanceLayer) return nodes

  root.children = children.flatMap((node) => {
    if (node.metadata?.debateLevel !== 'stance') return [node]

    const role = node.metadata?.debateRole
    const label = node.metadata?.debateLabel
    return (node.children || []).map((child) => ({
      ...child,
      parentId: root.id,
      metadata: {
        ...(child.metadata || {}),
        debateRole: role,
        debateLevel: 'direction',
        debateLabel: label,
        debateStanceLabel: node.label,
      },
    }))
  })

  return nodes
}

function restorePersistedTree() {
  if (typeof window === 'undefined' || treeStore.nodes.length > 0) return false

  try {
    const rawState = window.localStorage.getItem('thinking_tree_state')
    if (!rawState) return false

    const parsed = JSON.parse(rawState) as Partial<{
      id: string | null
      title: string
      description: string
      instructions: string
      activityMode: 'normal' | 'debate'
      debateProLabel: string
      debateConLabel: string
      nodes: TreeNode[]
      selectedNodeId: string | null
      lastSynced: string | null
    }>

    if (!Array.isArray(parsed.nodes) || parsed.nodes.length === 0) return false

    treeStore.id = parsed.id ?? null
    treeStore.title = parsed.title || parsed.nodes[0]?.label || '思维树'
    treeStore.description = parsed.description || ''
    treeStore.instructions = parsed.instructions || ''
    treeStore.activityMode = parsed.activityMode || 'normal'
    treeStore.debateProLabel = parsed.debateProLabel || '放走蚂蚁'
    treeStore.debateConLabel = parsed.debateConLabel || '踩扁蚂蚁'
    treeStore.nodes = normalizeDebateTreeShape(parsed.nodes)
    treeStore.selectedNodeId = parsed.selectedNodeId ?? null
    treeStore.lastSynced = parsed.lastSynced ?? null
    return true
  } catch (error) {
    console.warn('恢复本地思维树失败:', error)
    return false
  }
}

function createTreeNodeFromDirection(direction: SetupDirection, parentId: string): TreeNode {
  const node: TreeNode = {
    id: direction.id,
    label: direction.name,
    content: direction.name,
    nodeType: 'direction',
    parentId,
    children: [],
    metadata: {
      emoji: direction.emoji,
      ...direction.metadata,
    },
  }
  node.children = (direction.children || []).map((child) => createTreeNodeFromDirection(child, node.id))
  return node
}

function initializeTree(data: {
  theme: string
  mode?: 'normal' | 'debate'
  proLabel?: string
  conLabel?: string
  directions: SetupDirection[]
}) {
  const rootNode: TreeNode = {
    id: 'root',
    label: data.theme,
    content: data.theme,
    nodeType: 'root',
    parentId: null,
    children: data.directions.map((dir) => createTreeNodeFromDirection(dir, 'root')),
    metadata: {
      treeMode: data.mode || 'normal',
    },
  }

  treeStore.nodes = [rootNode]
  treeStore.title = data.theme
  treeStore.activityMode = data.mode || 'normal'
  if (data.proLabel) treeStore.debateProLabel = data.proLabel
  if (data.conLabel) treeStore.debateConLabel = data.conLabel
  showSetup.value = false
  nextTick(() => renderTree(treeStore.nodes))
}

function flattenNodeLabels(nodes: TreeNode[]): { id: string; label: string; content: string; nodeType: string }[] {
  return nodes.flatMap((node) => [
    {
      id: node.id,
      label: node.label,
      content: node.content,
      nodeType: node.nodeType,
    },
    ...flattenNodeLabels(node.children || []),
  ])
}

function buildTreeNode(node: TreeNode): { id: string; label: string; content: string; nodeType: string; metadata: Record<string, unknown>; children: any[] } {
  return {
    id: node.id,
    label: node.label,
    content: node.content,
    nodeType: node.nodeType,
    metadata: node.metadata || {},
    children: (node.children || []).map(child => buildTreeNode(child)),
  }
}

function hasNodeId(nodes: TreeNode[], id: string): boolean {
  return nodes.some((node) => node.id === id || hasNodeId(node.children || [], id))
}

function findNodeById(nodes: TreeNode[], id: string): TreeNode | null {
  for (const node of nodes) {
    if (node.id === id) return node
    const found = findNodeById(node.children || [], id)
    if (found) return found
  }
  return null
}

function buildSpeechTreeContext() {
  const root = treeStore.nodes[0]
  const directions = (root?.children || []).map((direction) => buildTreeNode(direction))

  return {
    tree_id: treeStore.id,
    theme: treeStore.title || root?.label || '思维树',
    description: treeStore.description,
    instructions: treeStore.instructions,
    root: root
      ? {
          id: root.id,
          label: root.label,
          content: root.content,
        }
      : null,
    directions,
    total_nodes: flattenNodeLabels(treeStore.nodes).length,
  }
}

function normalizeIdeaText(value: string) {
  return value
    .replace(/[，。！？、,.!?;；：“”"'（）()\s]/g, '')
    .replace(/这棵树|这个树|一棵树|树的/g, '树')
    .trim()
}

function ideaSimilarity(a: string, b: string) {
  const left = normalizeIdeaText(a)
  const right = normalizeIdeaText(b)
  if (!left || !right) return 0
  if (left === right) return 1
  if (left.includes(right) || right.includes(left)) {
    return Math.min(left.length, right.length) / Math.max(left.length, right.length)
  }
  const leftChars = new Set([...left])
  const rightChars = new Set([...right])
  const intersection = [...leftChars].filter((char) => rightChars.has(char)).length
  const union = new Set([...leftChars, ...rightChars]).size
  return union > 0 ? intersection / union : 0
}

function getLocalSimilarSiblings(parentId: string, label: string, content: string) {
  const parent = findNodeById(treeStore.nodes, parentId)
  if (!parent) return []
  return (parent.children || [])
    .filter((node) => {
      const labelScore = ideaSimilarity(label, node.label)
      const contentScore = ideaSimilarity(content, node.content || node.label)
      return Math.max(labelScore, contentScore) >= 0.72
    })
    .map((node) => ({ id: node.id, label: node.label }))
}

function debateRoleOf(node: TreeNode): 'pro' | 'con' | null {
  const role = node.metadata?.debateRole
  return role === 'pro' || role === 'con' ? role : null
}

function debateRoleForRender(node: RenderNode): 'pro' | 'con' | null {
  return debateRoleOf(node.data) || (node.parent ? debateRoleForRender(node.parent) : null)
}

function isDebateTree(rootData: TreeNode) {
  return rootData.metadata?.treeMode === 'debate'
    || (rootData.children || []).some((child) => debateRoleOf(child))
}

function debateStanceText(rootData: TreeNode, role: 'pro' | 'con') {
  const node = (rootData.children || []).find((child) => debateRoleOf(child) === role)
  return String(node?.metadata?.debateStanceLabel || (role === 'pro' ? '正方' : '反方'))
}

function inheritedDebateMetadata(parentId: string) {
  const parent = findNodeById(treeStore.nodes, parentId)
  if (!parent) return {}
  const metadata = parent.metadata || {}
  const role = metadata.debateRole
  if (role !== 'pro' && role !== 'con') return {}
  return {
    debateRole: role,
    debateLevel: 'leaf',
    debateLabel: metadata.debateLabel,
    debateStanceLabel: metadata.debateStanceLabel,
  }
}

function debateDirectionMetadata(role: 'pro' | 'con') {
  const root = treeStore.nodes[0]
  return {
    debateRole: role,
    debateLevel: 'direction',
    debateLabel: role === 'pro' ? '正方' : '反方',
    debateStanceLabel: root ? debateStanceText(root, role) : undefined,
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function truncateLabel(value: string, max = 8) {
  return value.length > max ? `${value.slice(0, max - 1)}…` : value
}

function buildRenderNodes(rootData: TreeNode, width: number, height: number): RenderNode[] {
  const rootX = width / 2
  const rootY = height * 0.78
  const renderRoot: RenderNode = { data: rootData, depth: 0, x: rootX, y: rootY, parent: null }
  const result: RenderNode[] = [renderRoot]
  const firstLevel = rootData.children ?? []
  const safeLeft = Math.max(130, width * 0.15)
  const safeRight = Math.min(width - 130, width * 0.85)
  const directionY = height * 0.39

  // 节点最小间距配置 - 增大间距避免重叠
  const MIN_NODE_SPACING = 130
  const NODE_RADIUS = 55

  function placeNestedChildren(parent: RenderNode, children: TreeNode[], depth: number, bandLeft: number, bandRight: number) {
    if (!children.length) return

    const columns = Math.min(children.length, 3)
    const rows = Math.ceil(children.length / columns)
    const spacing = Math.max(124, NODE_RADIUS * 2.15)
    const rowGap = Math.max(116, NODE_RADIUS * 2.05)
    const baseY = parent.y - Math.max(126, height * 0.12)

    children.forEach((child, index) => {
      const row = Math.floor(index / columns)
      const col = index % columns
      const itemsInRow = row === rows - 1 ? children.length - row * columns : columns
      const rowWidth = (itemsInRow - 1) * spacing
      const x = clamp(parent.x - rowWidth / 2 + col * spacing, bandLeft + 70, bandRight - 70)
      const y = clamp(baseY - row * rowGap + Math.sin(index + depth) * 6, 112, height - 190)
      const renderNode: RenderNode = { data: child, depth, x, y, parent }
      result.push(renderNode)

      const childCount = Math.max(1, child.children?.length ?? 0)
      const childBandHalf = Math.max(MIN_NODE_SPACING * 1.15, childCount * MIN_NODE_SPACING * 0.6)
      placeNestedChildren(
        renderNode,
        child.children ?? [],
        depth + 1,
        clamp(x - childBandHalf, bandLeft, bandRight),
        clamp(x + childBandHalf, bandLeft, bandRight)
      )
    })
  }

  function placeChildren(parent: RenderNode, children: TreeNode[], depth: number, bandLeft: number, bandRight: number) {
    if (!children.length) return

    const yStep = Math.max(108, Math.min(150, height * 0.15))
    const baseY = directionY - (depth - 1) * yStep
    const available = Math.max(150, bandRight - bandLeft)
    const maxColumns = depth === 1 ? children.length : Math.max(1, Math.floor(available / MIN_NODE_SPACING))
    const columns = Math.min(children.length, Math.max(1, maxColumns))
    const rows = Math.ceil(children.length / columns)
    const rowGap = Math.max(92, NODE_RADIUS * 1.85)
    const actualSpacing = columns === 1
      ? 0
      : depth === 1
        ? Math.max(104, available / Math.max(columns - 1, 1))
        : Math.max(MIN_NODE_SPACING, available / Math.max(columns - 1, 1))

    children.forEach((child, index) => {
      const row = Math.floor(index / columns)
      const col = index % columns
      const itemsInRow = row === rows - 1 ? children.length - row * columns : columns
      const rowWidth = (itemsInRow - 1) * actualSpacing
      const startX = bandLeft + (available - rowWidth) / 2
      const rowOffset = rows > 1 ? (row - (rows - 1) / 2) * rowGap : 0
      const jitterY = Math.sin(index * 1.5 + depth) * 8
      const x = clamp(startX + col * actualSpacing, 84, width - 84)
      const y = clamp(baseY + rowOffset + jitterY, 120, height - 170)
      const renderNode: RenderNode = { data: child, depth, x, y, parent }
      result.push(renderNode)

      // 为子节点分配带宽
      const childCount = Math.max(1, child.children?.length ?? 0)
      const childBandWidth = Math.max(MIN_NODE_SPACING * 1.6, childCount * MIN_NODE_SPACING)
      const childBandHalf = childBandWidth / 2
      
      placeNestedChildren(
        renderNode,
        child.children ?? [],
        depth + 1,
        clamp(x - childBandHalf, safeLeft * 0.5, safeRight),
        clamp(x + childBandHalf, safeLeft, width - safeLeft * 0.5)
      )
    })
  }

  if (isDebateTree(rootData)) {
    const centerGap = Math.max(150, width * 0.12)
    const proNodes = firstLevel.filter((node) => debateRoleOf(node) === 'pro')
    const conNodes = firstLevel.filter((node) => debateRoleOf(node) === 'con')
    const neutralNodes = firstLevel.filter((node) => !debateRoleOf(node))

    placeChildren(renderRoot, proNodes, 1, safeLeft, rootX - centerGap / 2)
    placeChildren(renderRoot, conNodes, 1, rootX + centerGap / 2, safeRight)
    if (neutralNodes.length) {
      placeChildren(renderRoot, neutralNodes, 1, rootX - centerGap * 0.25, rootX + centerGap * 0.25)
    }
  } else {
    placeChildren(renderRoot, firstLevel, 1, safeLeft, safeRight)
  }
  
  // 后处理：检测并修复重叠节点（使用更大的检测半径）
  resolveNestedOverlaps(result, NODE_RADIUS * 2.18, width, height)
  
  return result
}

function resolveNestedOverlaps(nodes: RenderNode[], minDistance: number, canvasWidth: number, canvasHeight: number) {
  for (let iteration = 0; iteration < 15; iteration++) {
    let hasOverlap = false

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (nodes[i].depth <= 1 || nodes[j].depth <= 1) continue
        if (nodes[i].parent === nodes[j] || nodes[j].parent === nodes[i]) continue

        const dx = nodes[j].x - nodes[i].x
        const dy = nodes[j].y - nodes[i].y
        const distance = Math.sqrt(dx * dx + dy * dy)

        if (distance < minDistance && distance > 0) {
          hasOverlap = true
          const overlap = (minDistance - distance) / 2
          const angle = Math.atan2(dy, dx)

          nodes[i].x = clamp(nodes[i].x - Math.cos(angle) * overlap, 80, canvasWidth - 80)
          nodes[i].y = clamp(nodes[i].y - Math.sin(angle) * overlap, 120, canvasHeight - 200)
          nodes[j].x = clamp(nodes[j].x + Math.cos(angle) * overlap, 80, canvasWidth - 80)
          nodes[j].y = clamp(nodes[j].y + Math.sin(angle) * overlap, 120, canvasHeight - 200)
        }
      }
    }
    if (!hasOverlap) break
  }
}

function resolveOverlaps(nodes: RenderNode[], minDistance: number, canvasWidth: number, canvasHeight: number) {
  // 多次迭代直到没有重叠
  for (let iteration = 0; iteration < 15; iteration++) {
    let hasOverlap = false
    
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        // 跳过父子关系的节点
        if (nodes[i].parent === nodes[j] || nodes[j].parent === nodes[i]) continue
        const dx = nodes[j].x - nodes[i].x
        const dy = nodes[j].y - nodes[i].y
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (distance < minDistance && distance > 0) {
          hasOverlap = true
          const overlap = (minDistance - distance) / 2
          const angle = Math.atan2(dy, dx)
          
          // 分开两个节点，保持在边界内
          nodes[i].x = clamp(nodes[i].x - Math.cos(angle) * overlap, 80, canvasWidth - 80)
          nodes[i].y = clamp(nodes[i].y - Math.sin(angle) * overlap, 120, canvasHeight - 200)
          nodes[j].x = clamp(nodes[j].x + Math.cos(angle) * overlap, 80, canvasWidth - 80)
          nodes[j].y = clamp(nodes[j].y + Math.sin(angle) * overlap, 120, canvasHeight - 200)
        }
      }
    }
    if (!hasOverlap) break
  }
}

function branchPath(d: RenderNode) {
  if (!d.parent) return ''
  const role = debateRoleOf(d.data)
  const source = d.parent.depth === 0
    ? {
        ...d.parent,
        x: role === 'pro' ? d.parent.x - 72 : role === 'con' ? d.parent.x + 72 : d.parent.x,
        y: d.parent.y - 132,
      }
    : d.parent
  const dy = source.y - d.y
  const bend = Math.max(36, Math.abs(d.x - source.x) * 0.18)
  const c1x = source.x + (d.x < source.x ? -bend : bend)
  const c2x = d.x - (d.x < source.x ? -bend : bend)

  return `M ${source.x} ${source.y}
    C ${c1x} ${source.y - dy * 0.45},
      ${c2x} ${d.y + dy * 0.45},
      ${d.x} ${d.y}`
}

function drawNodeShape(selection: d3.Selection<d3.BaseType, RenderNode, SVGGElement, unknown>) {
  const clusterCircleData = [
    { x: -26, y: -12, r: 34, opacity: 0.9 },
    { x: 8, y: -22, r: 38, opacity: 0.95 },
    { x: 34, y: -2, r: 31, opacity: 0.86 },
    { x: -2, y: 20, r: 32, opacity: 0.84 },
  ]

  selection
    .filter((d) => d.data.nodeType !== 'root')
    .selectAll('.leaf-cluster-petal')
    .data(() => clusterCircleData)
    .join('circle')
    .attr('class', 'leaf-cluster-petal')
    .attr('cx', (d) => d.x)
    .attr('cy', (d) => d.y)
    .attr('r', (d) => d.r)
    .attr('fill', function () {
      const node = d3.select(this.parentNode as SVGGElement).datum() as RenderNode
      const role = debateRoleForRender(node)
      if (role === 'pro') return 'url(#debate-pro-gradient)'
      if (role === 'con') return 'url(#debate-con-gradient)'
      return 'url(#direction-gradient)'
    })
    .attr('opacity', (d) => d.opacity)
    .attr('filter', 'url(#soft-shadow)')

  selection
    .append('path')
    .attr('class', 'leaf-path')
    .attr('d', (d) => {
      if (d.data.nodeType === 'root') {
        if (isDebateTree(d.data)) {
          return `M -72 66
            C -94 -8 -104 -108 -72 -154
            C -44 -112 -28 -42 -12 66
            C -30 88 -54 90 -72 66 Z
            M 12 66
            C 28 -42 44 -112 72 -154
            C 104 -108 94 -8 72 66
            C 54 90 30 88 12 66 Z`
        }
        return 'M -46 58 C -30 -16 -18 -95 0 -122 C 18 -95 30 -16 46 58 C 24 74 -24 74 -46 58 Z'
      }
      if (d.data.nodeType === 'direction') {
        return 'M -52 8 C -60 -28 -27 -58 12 -48 C 49 -40 69 -5 45 27 C 20 60 -37 51 -52 8 Z'
      }
      return 'M -43 5 C -48 -27 -18 -52 15 -40 C 48 -28 54 8 29 31 C 3 55 -39 39 -43 5 Z'
    })
    .attr('fill', (d) => {
      if (d.data.nodeType === 'root') return 'url(#trunk-gradient)'
      if (debateRoleForRender(d) === 'pro') return 'url(#debate-pro-gradient)'
      if (debateRoleForRender(d) === 'con') return 'url(#debate-con-gradient)'
      if (d.data.nodeType === 'direction') return 'url(#direction-gradient)'
      if (d.data.nodeType === 'insight') return '#9fc95f'
      return '#d5c06a'
    })
    .attr('filter', 'url(#soft-shadow)')
}

function renderTree(nodes: TreeNode[]) {
  if (!treeContainer.value || nodes.length === 0) return

  const startTime = performance.now()
  const rootData = nodes[0]
  if (!rootData) return

  const containerRect = treeContainer.value.getBoundingClientRect()
  const width = containerRect.width || window.innerWidth
  const height = containerRect.height || window.innerHeight
  const renderNodes = buildRenderNodes(rootData, width, height)
  const renderLinks = renderNodes.filter((node) => node.parent)
  const rootRender = renderNodes[0]
  const crownNodes = renderNodes.filter((node) => node.depth > 0)

  d3.select(treeContainer.value).selectAll('svg').remove()

  svg = d3
    .select(treeContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('aria-label', '儿童思维树画布')
    .style('background', 'transparent')

  const defs = svg.append('defs')

  const softShadow = defs
    .append('filter')
    .attr('id', 'soft-shadow')
    .attr('x', '-35%')
    .attr('y', '-35%')
    .attr('width', '170%')
    .attr('height', '170%')
  softShadow.append('feDropShadow').attr('dx', '0').attr('dy', '10').attr('stdDeviation', '7').attr('flood-opacity', '0.2')

  const rootGradient = defs.append('linearGradient').attr('id', 'root-gradient').attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '100%')
  rootGradient.append('stop').attr('offset', '0%').attr('stop-color', '#424035')
  rootGradient.append('stop').attr('offset', '58%').attr('stop-color', '#242923')
  rootGradient.append('stop').attr('offset', '100%').attr('stop-color', '#111713')

  const directionGradient = defs.append('linearGradient').attr('id', 'direction-gradient').attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '100%')
  directionGradient.append('stop').attr('offset', '0%').attr('stop-color', '#c9d979')
  directionGradient.append('stop').attr('offset', '100%').attr('stop-color', '#7faa4e')

  const debateProGradient = defs.append('linearGradient').attr('id', 'debate-pro-gradient').attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '100%')
  debateProGradient.append('stop').attr('offset', '0%').attr('stop-color', '#dff08a')
  debateProGradient.append('stop').attr('offset', '100%').attr('stop-color', '#76b85a')

  const debateConGradient = defs.append('linearGradient').attr('id', 'debate-con-gradient').attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '100%')
  debateConGradient.append('stop').attr('offset', '0%').attr('stop-color', '#f1d27d')
  debateConGradient.append('stop').attr('offset', '100%').attr('stop-color', '#d6875b')

  const trunkGradient = defs.append('linearGradient').attr('id', 'trunk-gradient').attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '0%')
  trunkGradient.append('stop').attr('offset', '0%').attr('stop-color', '#6b4b35')
  trunkGradient.append('stop').attr('offset', '50%').attr('stop-color', '#493424')
  trunkGradient.append('stop').attr('offset', '100%').attr('stop-color', '#7a563e')

  gContainer = svg.append('g').attr('class', 'tree-scene')

  currentZoom = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.45, 2.4])
    .translateExtent([
      [-width * 0.35, -height * 0.35],
      [width * 1.35, height * 1.25],
    ])
    .on('zoom', (event) => {
      gContainer.attr('transform', event.transform)
    })

  svg.call(currentZoom)

  if (rootRender && crownNodes.length) {
    const minX = d3.min(crownNodes, (d) => d.x) ?? width * 0.25
    const maxX = d3.max(crownNodes, (d) => d.x) ?? width * 0.75
    const minY = d3.min(crownNodes, (d) => d.y) ?? height * 0.25
    const maxY = d3.max(crownNodes, (d) => d.y) ?? height * 0.55
    const crownCenterX = (minX + maxX) / 2
    const crownCenterY = (minY + maxY) / 2 + 6
    const crownWidth = Math.max(480, maxX - minX + 360)
    const crownHeight = Math.max(270, maxY - minY + 220)

    const crownGroup = gContainer.append('g').attr('class', 'tree-crown')
    ;[
      { x: crownCenterX - crownWidth * 0.28, y: crownCenterY + 10, rx: crownWidth * 0.28, ry: crownHeight * 0.44 },
      { x: crownCenterX, y: crownCenterY - 34, rx: crownWidth * 0.34, ry: crownHeight * 0.5 },
      { x: crownCenterX + crownWidth * 0.3, y: crownCenterY + 8, rx: crownWidth * 0.28, ry: crownHeight * 0.44 },
      { x: crownCenterX - crownWidth * 0.03, y: crownCenterY + 52, rx: crownWidth * 0.42, ry: crownHeight * 0.38 },
    ].forEach((blob) => {
      crownGroup
        .append('ellipse')
        .attr('cx', blob.x)
        .attr('cy', blob.y)
        .attr('rx', blob.rx)
        .attr('ry', blob.ry)
        .attr('fill', 'rgba(113, 159, 102, 0.22)')
        .attr('stroke', 'rgba(238, 240, 204, 0.22)')
        .attr('stroke-width', 2)
    })

    if (!isDebateTree(rootData)) {
      gContainer
        .append('path')
        .attr('class', 'main-trunk')
        .attr(
          'd',
          `M ${rootRender.x - 34} ${rootRender.y + 42}
          C ${rootRender.x - 18} ${rootRender.y - 20}, ${rootRender.x - 18} ${rootRender.y - 78}, ${rootRender.x - 6} ${rootRender.y - 118}
          C ${rootRender.x + 10} ${rootRender.y - 80}, ${rootRender.x + 20} ${rootRender.y - 20}, ${rootRender.x + 34} ${rootRender.y + 42}
          C ${rootRender.x + 14} ${rootRender.y + 58}, ${rootRender.x - 14} ${rootRender.y + 58}, ${rootRender.x - 34} ${rootRender.y + 42} Z`
        )
        .attr('fill', 'url(#trunk-gradient)')
        .attr('opacity', 0.98)
        .attr('filter', 'url(#soft-shadow)')
    } else {
      const stanceGroup = gContainer.append('g').attr('class', 'debate-stance-text')
      ;[
        {
          x: rootRender.x - 158,
          y: rootRender.y - 4,
          label: '正方',
          text: debateStanceText(rootData, 'pro'),
          fill: 'rgba(245, 255, 219, 0.8)',
        },
        {
          x: rootRender.x + 158,
          y: rootRender.y - 4,
          label: '反方',
          text: debateStanceText(rootData, 'con'),
          fill: 'rgba(255, 240, 211, 0.82)',
        },
      ].forEach((item) => {
        const labelText = `${item.label} · ${truncateLabel(item.text, 7)}`
        stanceGroup
          .append('rect')
          .attr('x', item.x - 76)
          .attr('y', item.y - 18)
          .attr('width', 152)
          .attr('height', 32)
          .attr('rx', 16)
          .attr('fill', item.fill)
          .attr('stroke', 'rgba(255, 255, 238, 0.52)')
          .attr('stroke-width', 1)
        stanceGroup
          .append('text')
          .attr('x', item.x)
          .attr('y', item.y + 3)
          .attr('text-anchor', 'middle')
          .attr('fill', '#35442b')
          .attr('font-size', '15px')
          .attr('font-weight', '800')
          .text(labelText)
      })
    }
  }

  gContainer
    .selectAll('.link')
    .data(renderLinks)
    .join('path')
    .attr('class', (d) => `link link-depth-${Math.min(d.depth, 3)}`)
    .attr('d', branchPath)
    .attr('fill', 'none')
    .attr('stroke', (d) => (d.depth === 1 ? '#4b3428' : '#634a36'))
    .attr('stroke-width', (d) => Math.max(3.2, 16 - d.depth * 3.8))
    .attr('stroke-linecap', 'round')
    .attr('stroke-linejoin', 'round')
    .attr('opacity', (d) => (d.depth > 2 ? 0.72 : 0.92))

  const nodeGroups = gContainer
    .selectAll('.node')
    .data(renderNodes)
    .join('g')
    .attr('class', (d) => {
      const role = debateRoleForRender(d)
      return `node node-${d.data.nodeType} ${d.data.nodeType === 'insight' ? 'node-ai' : ''} ${role ? `node-debate-${role}` : ''}`
    })
    .attr('transform', (d) => `translate(${d.x},${d.y})`)
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      handleNodeClick(d.data, event)
    })

  drawNodeShape(nodeGroups)

  nodeGroups
    .append('rect')
    .attr('class', 'text-bg')
    .attr('x', (d) => {
      if (d.data.nodeType !== 'root') return -58
      return isDebateTree(d.data) ? -118 : -72
    })
    .attr('y', (d) => {
      if (d.data.nodeType !== 'root') return 42
      return isDebateTree(d.data) ? 84 : 70
    })
    .attr('width', (d) => {
      if (d.data.nodeType !== 'root') return 108
      return isDebateTree(d.data) ? 236 : 144
    })
    .attr('height', (d) => (d.data.nodeType === 'root' && isDebateTree(d.data) ? 30 : 26))
    .attr('rx', (d) => (d.data.nodeType === 'root' && isDebateTree(d.data) ? 15 : 13))
    .attr('fill', (d) => {
      const role = debateRoleForRender(d)
      if (d.data.nodeType === 'root') return 'rgba(33, 34, 28, 0.72)'
      if (role === 'pro') return 'rgba(244, 255, 213, 0.84)'
      if (role === 'con') return 'rgba(255, 238, 207, 0.86)'
      return 'rgba(255, 255, 245, 0.74)'
    })

  nodeGroups
    .append('text')
    .attr('class', 'node-text')
    .attr('text-anchor', 'middle')
    .attr('dy', (d) => {
      if (d.data.nodeType !== 'root') return 60
      return isDebateTree(d.data) ? 104 : 88
    })
    .attr('fill', (d) => (d.data.nodeType === 'root' ? '#fff9dc' : '#3b3b2c'))
    .attr('font-size', (d) => (d.data.nodeType === 'root' ? '13px' : '12px'))
    .attr('font-weight', '800')
    .text((d) => truncateLabel(d.data.label || d.data.content || '未命名', d.data.nodeType === 'root' ? 10 : 7))

  nodeGroups
    .append('circle')
    .attr('class', 'node-add-button')
    .attr('cx', (d) => (d.data.nodeType === 'root' ? 40 : 46))
    .attr('cy', (d) => (d.data.nodeType === 'root' ? -88 : -44))
    .attr('r', 11)
    .attr('display', (d) => (d.data.nodeType === 'root' && isDebateTree(d.data) ? 'none' : null))
    .attr('fill', '#f7f4dc')
    .attr('stroke', '#556743')
    .attr('stroke-width', 2)
    .attr('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      handleAddChild(d.data.id)
    })

  nodeGroups
    .append('text')
    .attr('class', 'node-add-text')
    .attr('x', (d) => (d.data.nodeType === 'root' ? 40 : 46))
    .attr('y', (d) => (d.data.nodeType === 'root' ? -84 : -40))
    .attr('display', (d) => (d.data.nodeType === 'root' && isDebateTree(d.data) ? 'none' : null))
    .attr('text-anchor', 'middle')
    .attr('fill', '#2f3d2a')
    .attr('font-size', '17px')
    .attr('font-weight', '900')
    .text('+')
    .style('pointer-events', 'none')

  if (rootRender && isDebateTree(rootData)) {
    const sideAddButtons = [
      { role: 'pro' as const, x: rootRender.x - 72, y: rootRender.y - 132 },
      { role: 'con' as const, x: rootRender.x + 72, y: rootRender.y - 132 },
    ]
    const rootAddGroups = gContainer
      .selectAll('.root-side-add')
      .data(sideAddButtons)
      .join('g')
      .attr('class', (d) => `root-side-add root-side-add-${d.role}`)
      .attr('transform', (d) => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation()
        handleAddChild('root', d.role)
      })

    rootAddGroups
      .append('circle')
      .attr('r', 13)
      .attr('fill', '#f7f4dc')
      .attr('stroke', '#556743')
      .attr('stroke-width', 2.2)

    rootAddGroups
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', 5)
      .attr('fill', '#2f3d2a')
      .attr('font-size', '18px')
      .attr('font-weight', '900')
      .text('+')
      .style('pointer-events', 'none')
  }

  perfMetrics.value = `Render Time: ${(performance.now() - startTime).toFixed(2)} ms | Nodes: ${renderNodes.length}`
}

const handleResize = () => {
  if (resizeTimeout) window.clearTimeout(resizeTimeout)
  resizeTimeout = window.setTimeout(() => {
    if (treeStore.nodes.length > 0) renderTree(treeStore.nodes)
  }, 180)
}

function handleNodeSave(data: { id: string; label: string; content: string }) {
  treeStore.updateNode(data.id, { label: data.label, content: data.content })
  showEditor.value = false
  selectedNode.value = null
}

function handleNodeClick(nodeData: TreeNode, event: any) {
  selectedNode.value = nodeData
  showEditor.value = true
  isNewNode.value = false

  const rect = event.currentTarget.getBoundingClientRect()
  editorPosition.value = {
    x: Math.min(Math.max(rect.right + 14, 24), window.innerWidth - 340),
    y: Math.min(Math.max(rect.top - 20, 88), window.innerHeight - 430),
  }
}

function handleNodeDelete(id: string) {
  treeStore.removeNode(id)
  showEditor.value = false
  selectedNode.value = null
}

function handleAddChild(parentId: string, debateRole?: 'pro' | 'con') {
  const isRootDirection = parentId === 'root'
  const newNode: TreeNode = {
    id: `node-${Date.now()}`,
    label: '',
    content: '',
    nodeType: isRootDirection ? 'direction' : 'answer',
    parentId,
    children: [],
    metadata: {
      ...(debateRole ? debateDirectionMetadata(debateRole) : inheritedDebateMetadata(parentId)),
    },
  }

  treeStore.addNode(parentId, newNode)
  selectedNode.value = newNode
  isNewNode.value = true
  showEditor.value = true
  editorPosition.value = {
    x: window.innerWidth / 2 - 160,
    y: window.innerHeight / 2 - 210,
  }
}

async function handleRecordingComplete(data: { base64: string; pcm: Int16Array; durationMs: number }) {
  isAnalyzing.value = true
  aiResponse.value = null
  recordingError.value = ''

  try {
    const response = await fetch('/api/speech/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio_base64: data.base64,
        provider: 'qwen',
        sample_rate: 16000,
        channels: 1,
        bit_depth: 16,
        activity_context: buildSpeechTreeContext(),
      }),
    })

    if (!response.ok) {
      let detail = 'AI分析失败'
      try {
        const errorBody = await response.json()
        detail = errorBody?.detail || errorBody?.message || detail
      } catch {
        detail = response.statusText || detail
      }
      throw new Error(detail)
    }

    const result = await response.json()
    aiResponse.value = result

    if (result.leaf_text) {
      const recommendedParentId =
        typeof result.recommended_parent_id === 'string' && result.recommended_parent_id
          ? result.recommended_parent_id
          : null
      const fallbackParentId = treeStore.nodes[0]?.children?.[0]?.id || treeStore.nodes[0]?.id || 'root'
      const parentId =
        recommendedParentId && hasNodeId(treeStore.nodes, recommendedParentId)
          ? recommendedParentId
          : fallbackParentId

      const candidateNode: TreeNode = {
        id: `ai-${Date.now()}`,
        label: result.leaf_text,
        content: result.rough_transcript || result.leaf_text,
        nodeType: 'insight',
        parentId,
        children: [],
        metadata: {
          ...inheritedDebateMetadata(parentId),
          source: 'speech',
          confidence: result.confidence,
          recommendedParentLabel: result.recommended_parent_label,
          classificationReason: result.classification_reason,
        },
      }

      const allNodes = flattenNodeLabels(treeStore.nodes)
      const modelSimilarNodes = (result.similar_node_ids || [])
        .map((id: string) => allNodes.find(n => n.id === id))
        .filter(Boolean)
        .map((n: any) => ({ id: n.id, label: n.label }))
      const localSimilarNodes = getLocalSimilarSiblings(parentId, candidateNode.label, candidateNode.content)
      const uniqueSimilarNodes = [...modelSimilarNodes, ...localSimilarNodes].filter(
        (node, index, list) => node.id !== candidateNode.id && list.findIndex((item) => item.id === node.id) === index
      )

      if (uniqueSimilarNodes.length > 0) {
        similarNodes.value = uniqueSimilarNodes
        pendingNode.value = { node: candidateNode, parentId }
      } else {
        treeStore.addNode(parentId, candidateNode)
      }
      // 弹窗保持打开，显示 AI 追问结果，由用户手动关闭
      // showRecorder.value = false
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '网络请求失败'
    recordingError.value = message.includes('fetch') || message.includes('Failed')
      ? '无法连接语音分析服务，请先启动后端服务，或稍后手动添加想法。'
      : message
    console.warn('录音分析未完成:', error)
  } finally {
    isAnalyzing.value = false
  }
}

function confirmAddNode() {
  if (pendingNode.value) {
    treeStore.addNode(pendingNode.value.parentId, pendingNode.value.node)
    pendingNode.value = null
    similarNodes.value = []
  }
}

function mergeWithSimilarNode(similarNodeId: string) {
  if (pendingNode.value) {
    // 将新节点的内容添加到相似节点的 metadata 中
    const similarNode = findNodeById(treeStore.nodes, similarNodeId)
    if (similarNode) {
      // 更新相似节点的内容，合并新旧信息
      const existingContent = similarNode.content || similarNode.label
      const newContent = pendingNode.value.node.content || pendingNode.value.node.label
      treeStore.updateNode(similarNodeId, {
        content: `${existingContent}；${newContent}`,
        metadata: {
          ...similarNode.metadata,
          mergedFrom: [...((similarNode.metadata?.mergedFrom as string[]) || []), pendingNode.value.node.id],
          mergeCount: ((similarNode.metadata?.mergeCount as number) || 0) + 1,
        },
      })
    }
    pendingNode.value = null
    similarNodes.value = []
  }
}

function cancelPendingNode() {
  pendingNode.value = null
  similarNodes.value = []
}

function handleContainerClick() {
  showEditor.value = false
  selectedNode.value = null
  d3.selectAll('.node').classed('selected', false)
}

function zoomIn() {
  if (svg && currentZoom) svg.transition().duration(260).call(currentZoom.scaleBy, 1.22)
}

function zoomOut() {
  if (svg && currentZoom) svg.transition().duration(260).call(currentZoom.scaleBy, 0.82)
}

function zoomReset() {
  if (svg && currentZoom) {
    svg.transition().duration(420).call(currentZoom.transform, d3.zoomIdentity)
  }
}

onMounted(() => {
  restorePersistedTree()

  if (treeStore.nodes.length === 0) {
    showSetup.value = true
  } else {
    showSetup.value = false
    setTimeout(() => renderTree(treeStore.nodes), 50)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeTimeout) clearTimeout(resizeTimeout)
  gsap.killTweensOf('.link, .leaf-path, .node, .node-text, .text-bg, .node-add-button, .node-add-text')
})

watch(
  () => treeStore.nodes,
  (newNodes) => {
    if (!showSetup.value) nextTick(() => renderTree(newNodes))
  },
  { deep: true }
)

function getSvgElement(): SVGSVGElement | null {
  if (!treeContainer.value) return null
  return treeContainer.value.querySelector('svg')
}

function openExportDialog() {
  showExportDialog.value = true
}
</script>

<template>
  <div class="tree-wrapper">
    <TreeSetup
      v-if="showSetup"
      :initial-theme="treeStore.title === 'New Thinking Tree' ? '' : treeStore.title"
      :initial-mode="treeStore.activityMode"
      :initial-pro-label="treeStore.debateProLabel"
      :initial-con-label="treeStore.debateConLabel"
      @complete="initializeTree"
    />

    <template v-else>
      <div class="woods-background"></div>
      <div class="soft-horizon"></div>
      <div class="hill-layer hill-layer-back"></div>
      <div class="hill-layer hill-layer-front"></div>

      <div id="tree-container" ref="treeContainer" @click="handleContainerClick"></div>

      <TreeNodeEditor
        v-if="showEditor"
        :node="selectedNode"
        :position="editorPosition"
        :is-new="isNewNode"
        @save="handleNodeSave"
        @delete="handleNodeDelete"
        @addChild="handleAddChild"
        @close="showEditor = false"
      />

      <div v-if="showRecorder" class="recorder-panel" @click.stop>
        <div class="recorder-header">
          <h3>录音记录孩子的想法</h3>
          <button class="close-btn" type="button" aria-label="关闭录音" @click.stop="showRecorder = false">×</button>
        </div>
        <AudioRecorder
          :target-sample-rate="16000"
          :max-duration-sec="60"
          :show-stats="true"
          @recording-complete="handleRecordingComplete"
          @error="(msg) => console.error('录音错误:', msg)"
        />
        <div v-if="isAnalyzing" class="analyzing-overlay">
          <div class="spinner"></div>
          <p>AI 正在分析孩子的想法...</p>
        </div>
        <div v-if="recordingError" class="recording-error">
          {{ recordingError }}
        </div>
        <div v-if="aiResponse" class="ai-response">
          <p><strong>AI 听到：</strong>{{ aiResponse.rough_transcript }}</p>
          <p><strong>建议叶子：</strong>{{ aiResponse.leaf_text }}</p>
          <p v-if="aiResponse.recommended_parent_label"><strong>建议位置：</strong>{{ aiResponse.recommended_parent_label }}</p>
          <p v-if="aiResponse.classification_reason"><strong>分类依据：</strong>{{ aiResponse.classification_reason }}</p>
          <p v-if="aiResponse.follow_up_question"><strong>追问：</strong>{{ aiResponse.follow_up_question }}</p>
        </div>

        <!-- 相似节点确认对话框 -->
        <div v-if="similarNodes.length > 0" class="similar-nodes-panel">
          <div class="similar-nodes-header">
            <h4>发现同层相似叶子</h4>
            <p>这条想法可能和已有叶子意思接近，请老师决定是否仍然加入。</p>
          </div>
          <div class="similar-nodes-list">
            <div
              v-for="similar in similarNodes"
              :key="similar.id"
              class="similar-node-item"
              @click="mergeWithSimilarNode(similar.id)"
            >
              <span class="similar-node-icon">🔄</span>
              <span class="similar-node-label">{{ similar.label }}</span>
              <span class="similar-node-action">合并到此</span>
            </div>
          </div>
          <div class="similar-nodes-actions">
            <button class="btn btn--outline" @click="confirmAddNode">
              仍然添加为新节点
            </button>
            <button class="btn btn--ghost" @click="cancelPendingNode">
              取消
            </button>
          </div>
        </div>
      </div>

      <div class="controls-wrapper" @click.stop>
        <div class="tree-title-pill">
          <span class="title-mark">🌳</span>
          <span>{{ treeStore.title || '思维树' }}</span>
        </div>

        <div class="zoom-controls" aria-label="缩放控制">
          <button type="button" title="缩小" @click.stop="zoomOut">−</button>
          <button type="button" title="居中" @click.stop="zoomReset">⌾</button>
          <button type="button" title="放大" @click.stop="zoomIn">+</button>
        </div>

        <div class="controls-bar" aria-label="树工具栏">
          <button class="control-btn record-btn" type="button" @click.stop="showRecorder = !showRecorder">
            <span class="btn-icon">🎙</span>
            <span>{{ showRecorder ? '关闭录音' : '录音' }}</span>
          </button>
          <button class="control-btn add-btn" type="button" @click.stop="handleAddChild('root')">
            <span class="btn-icon">＋</span>
            <span>添加想法</span>
          </button>
          <button class="control-btn export-btn" type="button" @click.stop="openExportDialog">
            <span class="btn-icon">⇩</span>
            <span>导出</span>
          </button>
        </div>
      </div>

      <ExportDialog
        v-model="showExportDialog"
        :svg-element="getSvgElement()"
        :activity-id="treeStore.activityId ?? undefined"
        :title="treeStore.title"
        :node-count="treeStore.nodeCount"
      />
    </template>
  </div>
</template>

<style scoped>
.tree-wrapper {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  font-family: ui-rounded, 'Trebuchet MS', 'Microsoft YaHei', system-ui, -apple-system, sans-serif;
  touch-action: none;
  background:
    url('/images/itw-day-bg.png') center center / cover no-repeat,
    #a5b995;
}

/* Into the Woods day background */
.woods-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    url('/images/itw-day-bg.png') center center / cover no-repeat,
    #a5b995;
}

.soft-horizon {
  display: none;
}

.hill-layer {
  display: none;
}

.hill-layer-back {
  display: none;
}

.hill-layer-front {
  display: none;
}

.woods-background::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.woods-background::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

#tree-container {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.controls-wrapper {
  position: absolute;
  inset: 0;
  z-index: 1200;
  pointer-events: none;
}

.tree-title-pill {
  position: absolute;
  top: 20px;
  left: 38px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  max-width: min(360px, calc(100vw - 240px));
  padding: 0 22px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  background: rgba(26, 46, 26, 0.6);
  color: #e8f0e8;
  font-size: 17px;
  font-weight: 900;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 14px 30px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  pointer-events: auto;
}

.title-mark {
  font-size: 19px;
}

.zoom-controls {
  position: absolute;
  top: 20px;
  right: 38px;
  display: flex;
  gap: 8px;
  padding: 7px;
  border-radius: 999px;
  background: rgba(26, 46, 26, 0.6);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 14px 30px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  pointer-events: auto;
}

.zoom-controls button {
  width: 40px;
  height: 40px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  color: #e8f0e8;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease;
}

.zoom-controls button:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.25);
}

.controls-bar {
  position: absolute;
  bottom: 34px;
  left: 50%;
  display: flex;
  gap: 12px;
  padding: 8px;
  border-radius: 999px;
  background: rgba(26, 46, 26, 0.7);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 18px 42px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px);
  transform: translateX(-50%);
  pointer-events: auto;
}

.control-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 112px;
  height: 48px;
  padding: 0 20px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  color: #e8f0e8;
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
}

.control-btn:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.25);
}

.record-btn {
  background: linear-gradient(180deg, rgba(180, 100, 160, 0.8) 0%, rgba(150, 60, 130, 0.9) 100%);
  color: #fff;
}

.record-btn:hover {
  background: linear-gradient(180deg, rgba(200, 120, 180, 0.9) 0%, rgba(170, 80, 150, 1) 100%);
}

.add-btn {
  background: linear-gradient(180deg, rgba(120, 180, 80, 0.8) 0%, rgba(80, 140, 50, 0.9) 100%);
  color: #fff;
}

.add-btn:hover {
  background: linear-gradient(180deg, rgba(140, 200, 100, 0.9) 0%, rgba(100, 160, 70, 1) 100%);
}

.export-btn {
  background: rgba(255, 255, 255, 0.15);
}

.export-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.btn-icon {
  font-size: 18px;
  line-height: 1;
}

.recorder-panel {
  position: absolute;
  right: 38px;
  bottom: 104px;
  width: min(420px, calc(100vw - 48px));
  padding: 20px;
  z-index: 200;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 26px;
  background: rgba(26, 46, 26, 0.85);
  box-shadow: 0 22px 58px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(24px);
  pointer-events: auto;
}

.recorder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.recorder-header h3 {
  margin: 0;
  color: #e8f0e8;
  font-size: 16px;
  font-weight: 900;
}

.close-btn {
  width: 34px;
  height: 34px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  color: #e8f0e8;
  font-size: 22px;
  cursor: pointer;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.analyzing-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 26px;
  background: rgba(26, 46, 26, 0.95);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(120, 180, 80, 0.3);
  border-top-color: #7da747;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.ai-response {
  margin-top: 14px;
  padding: 12px;
  border-radius: 16px;
  background: rgba(120, 180, 80, 0.2);
  color: #e8f0e8;
  font-size: 14px;
}

.ai-response p {
  margin: 4px 0;
}

.recording-error {
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(200, 100, 80, 0.3);
  border-radius: 16px;
  background: rgba(200, 100, 80, 0.2);
  color: #f0d0c0;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.5;
}

.similar-nodes-panel {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid rgba(120, 180, 80, 0.3);
  border-radius: 16px;
  background: rgba(120, 180, 80, 0.15);
}

.similar-nodes-header h4 {
  margin: 0 0 6px;
  color: #e8f0e8;
  font-size: 15px;
  font-weight: 800;
}

.similar-nodes-header p {
  margin: 0 0 12px;
  color: rgba(232, 240, 232, 0.8);
  font-size: 13px;
}

.similar-nodes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.similar-node-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.similar-node-item:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateX(4px);
}

.similar-node-icon {
  font-size: 18px;
}

.similar-node-label {
  flex: 1;
  color: #e8f0e8;
  font-size: 14px;
  font-weight: 600;
}

.similar-node-action {
  color: #a0d080;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(120, 180, 80, 0.2);
}

.similar-nodes-actions {
  display: flex;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn--outline {
  background: rgba(255, 255, 255, 0.1);
  color: #e8f0e8;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn--outline:hover {
  background: rgba(255, 255, 255, 0.2);
}

.btn--ghost {
  background: transparent;
  color: rgba(232, 240, 232, 0.7);
}

.btn--ghost:hover {
  background: rgba(255, 255, 255, 0.1);
}

:deep(.link) {
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 9px 8px rgba(0, 0, 0, 0.3));
}

:deep(.node) {
  cursor: pointer;
}

:deep(.tree-crown ellipse) {
  backdrop-filter: blur(3px);
}

:deep(.main-trunk) {
  stroke: rgba(255, 241, 190, 0.3);
  stroke-width: 1.5px;
}

:deep(.leaf-cluster-petal) {
  stroke: rgba(248, 248, 214, 0.3);
  stroke-width: 1px;
}

:deep(.leaf-path) {
  stroke: rgba(255, 255, 225, 0.6);
  stroke-width: 1.6;
  transition: filter 0.25s ease, transform 0.25s ease;
}

:deep(.node:hover .leaf-path) {
  filter: url(#soft-shadow) brightness(1.2);
}

:deep(.text-bg) {
  backdrop-filter: blur(8px);
}

:deep(.node-text) {
  pointer-events: none;
  paint-order: stroke;
  stroke: rgba(255, 255, 235, 0.08);
  stroke-width: 2px;
}

:deep(.node-add-button) {
  transition: fill 0.18s ease, transform 0.18s ease;
}

:deep(.node-add-button:hover) {
  fill: #ffffff;
}

@media (max-width: 768px) {
  .tree-title-pill {
    top: 18px;
    left: 16px;
    max-width: calc(100vw - 118px);
    min-height: 42px;
    padding: 0 15px;
    font-size: 14px;
  }

  .zoom-controls {
    top: 18px;
    right: 16px;
    gap: 5px;
    padding: 5px;
  }

  .zoom-controls button {
    width: 34px;
    height: 34px;
    font-size: 16px;
  }

  .controls-bar {
    bottom: 16px;
    width: calc(100vw - 28px);
    justify-content: center;
    gap: 6px;
    padding: 6px;
  }

  .control-btn {
    min-width: 0;
    flex: 1;
    height: 44px;
    padding: 0 8px;
    font-size: 13px;
  }

  .recorder-panel {
    left: 14px;
    right: 14px;
    bottom: 82px;
    width: auto;
    padding: 14px;
  }
}
</style>
