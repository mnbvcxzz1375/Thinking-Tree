export default defineEventHandler((_event) => {
  return {
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'thinking-tree-api',
  }
})
