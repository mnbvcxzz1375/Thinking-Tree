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

let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>
let gContainer: d3.Selection<SVGGElement, unknown, null, undefined>
let currentZoom: d3.ZoomBehavior<SVGSVGElement, unknown>
let resizeTimeout: number | undefined

function restorePersistedTree() {
  if (typeof window === 'undefined' || treeStore.nodes.length > 0) return false

  try {
    const rawState = window.localStorage.getItem('thinking_tree_state')
    if (!rawState) return false

    const parsed = JSON.parse(rawState) as Partial<{
      id: string | null
      title: string
      description: string
      nodes: TreeNode[]
      selectedNodeId: string | null
      lastSynced: string | null
    }>

    if (!Array.isArray(parsed.nodes) || parsed.nodes.length === 0) return false

    treeStore.id = parsed.id ?? null
    treeStore.title = parsed.title || parsed.nodes[0]?.label || '思维树'
    treeStore.description = parsed.description || ''
    treeStore.nodes = parsed.nodes
    treeStore.selectedNodeId = parsed.selectedNodeId ?? null
    treeStore.lastSynced = parsed.lastSynced ?? null
    return true
  } catch (error) {
    console.warn('恢复本地思维树失败:', error)
    return false
  }
}

function initializeTree(data: { theme: string; directions: { id: string; name: string; emoji: string }[] }) {
  const rootNode: TreeNode = {
    id: 'root',
    label: data.theme,
    content: data.theme,
    nodeType: 'root',
    parentId: null,
    children: data.directions.map((dir) => ({
      id: dir.id,
      label: dir.name,
      content: dir.name,
      nodeType: 'direction',
      parentId: 'root',
      children: [],
    })),
  }

  treeStore.nodes = [rootNode]
  treeStore.title = data.theme
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

function hasNodeId(nodes: TreeNode[], id: string): boolean {
  return nodes.some((node) => node.id === id || hasNodeId(node.children || [], id))
}

function buildSpeechTreeContext() {
  const root = treeStore.nodes[0]
  const directions = (root?.children || []).map((direction) => ({
    id: direction.id,
    label: direction.label,
    content: direction.content,
    children: flattenNodeLabels(direction.children || []),
  }))

  return {
    tree_id: treeStore.id,
    theme: treeStore.title || root?.label || '思维树',
    description: treeStore.description,
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

  function placeChildren(parent: RenderNode, children: TreeNode[], depth: number, bandLeft: number, bandRight: number) {
    if (!children.length) return

    const yStep = Math.max(76, Math.min(118, height * 0.12))
    const baseY = directionY - (depth - 1) * yStep
    const available = Math.max(90, bandRight - bandLeft)

    children.forEach((child, index) => {
      const ratio = children.length === 1 ? 0.5 : index / (children.length - 1)
      const jitter = children.length > 1 ? Math.sin(index * 1.7 + depth) * Math.min(34, available / 12) : 0
      const x = clamp(bandLeft + ratio * available + jitter, 72, width - 72)
      const y = clamp(baseY + Math.cos(index * 1.2 + depth) * (depth === 1 ? 42 : 28), 116, height - 180)
      const renderNode: RenderNode = { data: child, depth, x, y, parent }
      result.push(renderNode)

      const childCount = Math.max(1, child.children?.length ?? 0)
      const childBand = Math.min(available / Math.max(children.length, 1), 220 + childCount * 34)
      placeChildren(
        renderNode,
        child.children ?? [],
        depth + 1,
        clamp(x - childBand / 2, safeLeft * 0.5, safeRight),
        clamp(x + childBand / 2, safeLeft, width - safeLeft * 0.5)
      )
    })
  }

  placeChildren(renderRoot, firstLevel, 1, safeLeft, safeRight)
  return result
}

function branchPath(d: RenderNode) {
  if (!d.parent) return ''
  const source = d.parent.depth === 0
    ? { ...d.parent, y: d.parent.y - 92 }
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
    .attr('fill', 'url(#direction-gradient)')
    .attr('opacity', (d) => d.opacity)
    .attr('filter', 'url(#soft-shadow)')

  selection
    .append('path')
    .attr('class', 'leaf-path')
    .attr('d', (d) => {
      if (d.data.nodeType === 'root') {
        return 'M -46 58 C -30 -16 -18 -95 0 -122 C 18 -95 30 -16 46 58 C 24 74 -24 74 -46 58 Z'
      }
      if (d.data.nodeType === 'direction') {
        return 'M -52 8 C -60 -28 -27 -58 12 -48 C 49 -40 69 -5 45 27 C 20 60 -37 51 -52 8 Z'
      }
      return 'M -43 5 C -48 -27 -18 -52 15 -40 C 48 -28 54 8 29 31 C 3 55 -39 39 -43 5 Z'
    })
    .attr('fill', (d) => {
      if (d.data.nodeType === 'root') return 'url(#trunk-gradient)'
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
    .attr('class', (d) => `node node-${d.data.nodeType} ${d.data.nodeType === 'insight' ? 'node-ai' : ''}`)
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
    .attr('x', (d) => (d.data.nodeType === 'root' ? -72 : -58))
    .attr('y', (d) => (d.data.nodeType === 'root' ? 70 : 42))
    .attr('width', (d) => (d.data.nodeType === 'root' ? 144 : 108))
    .attr('height', 26)
    .attr('rx', 13)
    .attr('fill', (d) => (d.data.nodeType === 'root' ? 'rgba(33, 34, 28, 0.72)' : 'rgba(255, 255, 245, 0.74)'))

  nodeGroups
    .append('text')
    .attr('class', 'node-text')
    .attr('text-anchor', 'middle')
    .attr('dy', (d) => (d.data.nodeType === 'root' ? 88 : 60))
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
    .attr('text-anchor', 'middle')
    .attr('fill', '#2f3d2a')
    .attr('font-size', '17px')
    .attr('font-weight', '900')
    .text('+')
    .style('pointer-events', 'none')

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

function handleAddChild(parentId: string) {
  const newNode: TreeNode = {
    id: `node-${Date.now()}`,
    label: '',
    content: '',
    nodeType: 'answer',
    parentId,
    children: [],
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
          source: 'speech',
          confidence: result.confidence,
          recommendedParentLabel: result.recommended_parent_label,
          classificationReason: result.classification_reason,
        },
      }

      treeStore.addNode(parentId, candidateNode)
      showRecorder.value = false
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
    <TreeSetup v-if="showSetup" @complete="initializeTree" />

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
          <p v-if="aiResponse.follow_up_question"><strong>追问：</strong>{{ aiResponse.follow_up_question }}</p>
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
  background: #aeb49b;
}

.woods-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    linear-gradient(180deg, rgba(221, 212, 160, 0.54) 0%, rgba(164, 189, 165, 0.82) 50%, rgba(100, 148, 93, 0.92) 100%),
    radial-gradient(ellipse at 50% 8%, rgba(236, 230, 183, 0.74) 0%, rgba(236, 230, 183, 0) 42%),
    #a7b6a0;
}

.soft-horizon {
  position: absolute;
  left: -5%;
  right: -5%;
  bottom: 16vh;
  height: 24vh;
  z-index: 0;
  background: linear-gradient(180deg, rgba(207, 204, 146, 0), rgba(210, 194, 112, 0.35), rgba(78, 130, 82, 0.16));
  filter: blur(14px);
}

.hill-layer {
  position: absolute;
  left: -6%;
  right: -6%;
  bottom: -8vh;
  z-index: 0;
  height: 31vh;
  background-repeat: repeat-x;
  background-size: 360px 210px;
  background-position: bottom center;
}

.hill-layer-back {
  bottom: 7vh;
  height: 21vh;
  opacity: 0.9;
  background-image:
    radial-gradient(ellipse at 48% 100%, #d3bd63 0 28%, rgba(211, 189, 99, 0) 29%),
    radial-gradient(ellipse at 10% 100%, #83aa6d 0 20%, rgba(131, 170, 109, 0) 21%),
    radial-gradient(ellipse at 78% 100%, #b2b46c 0 24%, rgba(178, 180, 108, 0) 25%);
  filter: blur(0.5px);
}

.hill-layer-front {
  height: 30vh;
  background-size: 430px 260px;
  background-image:
    radial-gradient(ellipse at 15% 100%, #d4bd65 0 31%, rgba(212, 189, 101, 0) 32%),
    radial-gradient(ellipse at 48% 100%, #80ab64 0 26%, rgba(128, 171, 100, 0) 27%),
    radial-gradient(ellipse at 82% 100%, #ddc56e 0 35%, rgba(221, 197, 110, 0) 36%);
}

#tree-container {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.controls-wrapper {
  position: absolute;
  inset: 0;
  z-index: 100;
  pointer-events: none;
}

.tree-title-pill {
  position: absolute;
  top: 112px;
  left: 38px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  max-width: min(360px, calc(100vw - 240px));
  padding: 0 22px;
  border: 1px solid rgba(255, 255, 255, 0.38);
  border-radius: 999px;
  background: rgba(255, 255, 244, 0.54);
  color: #27311f;
  font-size: 17px;
  font-weight: 900;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7), 0 14px 30px rgba(41, 48, 27, 0.12);
  backdrop-filter: blur(16px);
  pointer-events: auto;
}

.title-mark {
  font-size: 19px;
}

.zoom-controls {
  position: absolute;
  top: 112px;
  right: 38px;
  display: flex;
  gap: 8px;
  padding: 7px;
  border-radius: 999px;
  background: rgba(255, 255, 244, 0.48);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.66), 0 14px 30px rgba(41, 48, 27, 0.12);
  backdrop-filter: blur(16px);
  pointer-events: auto;
}

.zoom-controls button {
  width: 40px;
  height: 40px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 253, 237, 0.9);
  color: #2f3328;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease;
}

.zoom-controls button:hover {
  transform: translateY(-1px);
  background: #fff9dc;
}

.controls-bar {
  position: absolute;
  bottom: 34px;
  left: 50%;
  display: flex;
  gap: 12px;
  padding: 8px;
  border-radius: 999px;
  background: rgba(45, 48, 34, 0.28);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24), 0 18px 42px rgba(30, 36, 22, 0.22);
  backdrop-filter: blur(18px);
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
  background: rgba(255, 249, 220, 0.9);
  color: #2d3226;
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
}

.control-btn:hover {
  transform: translateY(-2px);
  background: #fff8d8;
}

.record-btn {
  background: linear-gradient(180deg, #f4d2ea 0%, #d973ca 100%);
  color: #fff7ff;
}

.add-btn {
  background: linear-gradient(180deg, #e6edb4 0%, #98bd55 100%);
  color: #25351d;
}

.export-btn {
  background: rgba(255, 249, 220, 0.92);
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
  border: 1px solid rgba(255, 255, 255, 0.42);
  border-radius: 26px;
  background: rgba(255, 255, 242, 0.78);
  box-shadow: 0 22px 58px rgba(28, 34, 22, 0.24);
  backdrop-filter: blur(22px);
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
  color: #26311f;
  font-size: 16px;
  font-weight: 900;
}

.close-btn {
  width: 34px;
  height: 34px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #424534;
  font-size: 22px;
  cursor: pointer;
}

.analyzing-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 26px;
  background: rgba(255, 255, 242, 0.92);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(80, 102, 57, 0.18);
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
  background: rgba(230, 237, 180, 0.62);
  color: #2e3726;
  font-size: 14px;
}

.ai-response p {
  margin: 4px 0;
}

.recording-error {
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(160, 75, 55, 0.22);
  border-radius: 16px;
  background: rgba(255, 231, 208, 0.72);
  color: #6c2d20;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.5;
}

:deep(.link) {
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 9px 8px rgba(44, 31, 20, 0.16));
}

:deep(.node) {
  cursor: pointer;
}

:deep(.tree-crown ellipse) {
  backdrop-filter: blur(3px);
}

:deep(.main-trunk) {
  stroke: rgba(255, 241, 190, 0.2);
  stroke-width: 1.5px;
}

:deep(.leaf-cluster-petal) {
  stroke: rgba(248, 248, 214, 0.22);
  stroke-width: 1px;
}

:deep(.leaf-path) {
  stroke: rgba(255, 255, 225, 0.5);
  stroke-width: 1.6;
  transition: filter 0.25s ease, transform 0.25s ease;
}

:deep(.node:hover .leaf-path) {
  filter: url(#soft-shadow) brightness(1.08);
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
    top: 92px;
    left: 16px;
    max-width: calc(100vw - 118px);
    min-height: 42px;
    padding: 0 15px;
    font-size: 14px;
  }

  .zoom-controls {
    top: 92px;
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
