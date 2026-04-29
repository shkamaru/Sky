import { useState } from 'react'
import Canvas from './canvas/Canvas'
import ChatPanel from './chat/ChatPanel'
import ModelSelector from './components/ModelSelector'

export default function App() {
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)

  return (
    <div className="w-full h-full flex flex-col bg-[#0f0f0f]">
      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-2 bg-[#0d0d1a]/80 backdrop-blur border-b border-[#2a2a4a]">
        <span className="text-[#a78bfa] font-semibold text-sm tracking-wide">SKY</span>
        <div className="flex items-center gap-3">
          <span className="text-[#4b5563] text-xs">double-click canvas to create a node</span>
          <ModelSelector />
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 flex pt-10">
        {/* Canvas takes all remaining space */}
        <div className={`flex-1 transition-all duration-300 ${selectedNodeId ? 'mr-[380px]' : ''}`}>
          <Canvas onNodeSelect={(id) => setSelectedNodeId(id)} />
        </div>

        {/* Chat panel slides in from right */}
        {selectedNodeId && (
          <div className="absolute right-0 top-10 bottom-0 w-[380px] z-10">
            <ChatPanel
              nodeId={selectedNodeId}
              onClose={() => setSelectedNodeId(null)}
            />
          </div>
        )}
      </div>
    </div>
  )
}
