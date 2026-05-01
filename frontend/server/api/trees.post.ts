export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  return {
    id: crypto.randomUUID(),
    title: body?.title || 'New Tree',
    nodes: [],
    createdAt: new Date().toISOString(),
  }
})
