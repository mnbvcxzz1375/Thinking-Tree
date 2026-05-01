export default defineEventHandler(() => {
  // Mock tree list - replace with real database
  return {
    trees: [
      {
        id: '1',
        title: 'Sample Thinking Tree',
        nodeCount: 3,
        createdAt: new Date().toISOString(),
      },
    ],
  }
})
