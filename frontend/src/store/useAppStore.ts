import { create } from 'zustand'

export interface CanvasNode {
  id: number
  x: number
  y: number
  width: number
  height: number
  node_type: 'chat' | 'file'
  title: string
  conversation_id: number | null
  file_id: number | null
}

export interface Arrow {
  id: number
  from_node_id: number
  to_node_id: number
  similarity_score: number
}

interface AppState {
  // Canvas
  nodes: CanvasNode[]
  arrows: Arrow[]
  selectedNodeId: number | null
  activeModel: string

  // Actions
  setNodes: (nodes: CanvasNode[]) => void
  addNode: (node: CanvasNode) => void
  updateNode: (id: number, patch: Partial<CanvasNode>) => void
  setArrows: (arrows: Arrow[]) => void
  addArrow: (arrow: Arrow) => void
  setSelectedNodeId: (id: number | null) => void
  setActiveModel: (model: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  nodes: [],
  arrows: [],
  selectedNodeId: null,
  activeModel: 'qwen2.5:14b',

  setNodes: (nodes) => set({ nodes }),
  addNode: (node) => set((s) => ({ nodes: [...s.nodes, node] })),
  updateNode: (id, patch) =>
    set((s) => ({
      nodes: s.nodes.map((n) => (n.id === id ? { ...n, ...patch } : n)),
    })),
  setArrows: (arrows) => set({ arrows }),
  addArrow: (arrow) => set((s) => ({ arrows: [...s.arrows, arrow] })),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setActiveModel: (model) => set({ activeModel: model }),
}))
