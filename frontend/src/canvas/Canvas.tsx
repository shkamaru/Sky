import { useEffect, useRef, useState } from 'react'
import { Stage, Layer, Rect, Text, Arrow, Group } from 'react-konva'
import { useAppStore } from '../store/useAppStore'
import type Konva from 'konva'

const NODE_W = 280
const NODE_H = 60
const BG_COLOR = '#0f0f0f'
const NODE_COLOR = '#1a1a2e'
const NODE_BORDER = '#6c63ff'
const SELECTED_BORDER = '#a78bfa'
const ARROW_COLOR = '#6c63ff'
const TEXT_COLOR = '#e2e8f0'

export default function Canvas({ onNodeSelect }: { onNodeSelect: (id: number) => void }) {
  const stageRef = useRef<Konva.Stage>(null)
  const { nodes, arrows, selectedNodeId, setNodes, setArrows, addNode, updateNode, setSelectedNodeId } = useAppStore()

  // Load existing nodes and arrows on mount
  useEffect(() => {
    fetch('/api/canvas/nodes')
      .then((r) => r.json())
      .then((d) => setNodes(d.nodes))

    fetch('/api/canvas/arrows')
      .then((r) => r.json())
      .then((d) => setArrows(d.arrows))
  }, [])

  // Click on empty canvas → create node
  const handleStageClick = async (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (e.target !== e.target.getStage() && e.target.name() !== 'bg') return

    const stage = stageRef.current!
    const pointer = stage.getPointerPosition()!
    const scale = stage.scaleX()
    const pos = {
      x: (pointer.x - stage.x()) / scale - NODE_W / 2,
      y: (pointer.y - stage.y()) / scale - NODE_H / 2,
    }

    const res = await fetch('/api/canvas/nodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ x: pos.x, y: pos.y, node_type: 'chat' }),
    })
    const newNode = await res.json()
    addNode(newNode)
    setSelectedNodeId(newNode.id)
    onNodeSelect(newNode.id)
  }

  // Drag node → persist new position
  const handleDragEnd = async (id: number, x: number, y: number) => {
    updateNode(id, { x, y })
    await fetch(`/api/canvas/nodes/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ x, y }),
    })
  }

  // Zoom with scroll
  const handleWheel = (e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault()
    const stage = stageRef.current!
    const oldScale = stage.scaleX()
    const pointer = stage.getPointerPosition()!
    const scaleBy = 1.08
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy
    const clamped = Math.min(Math.max(newScale, 0.1), 5)

    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    }
    stage.scale({ x: clamped, y: clamped })
    stage.position({
      x: pointer.x - mousePointTo.x * clamped,
      y: pointer.y - mousePointTo.y * clamped,
    })
  }

  // Build arrow points from node positions
  const getArrowPoints = (fromId: number, toId: number): number[] | null => {
    const from = nodes.find((n) => n.id === fromId)
    const to = nodes.find((n) => n.id === toId)
    if (!from || !to) return null
    return [
      from.x + NODE_W / 2, from.y + NODE_H / 2,
      to.x + NODE_W / 2, to.y + NODE_H / 2,
    ]
  }

  return (
    <Stage
      ref={stageRef}
      width={window.innerWidth}
      height={window.innerHeight}
      draggable
      onDblClick={handleStageClick}
      onWheel={handleWheel}
      style={{ background: BG_COLOR }}
    >
      <Layer>
        {/* Invisible background rect to capture clicks */}
        <Rect
          name="bg"
          x={-50000} y={-50000}
          width={100000} height={100000}
          fill="transparent"
        />

        {/* Arrows */}
        {arrows.map((arrow) => {
          const points = getArrowPoints(arrow.from_node_id, arrow.to_node_id)
          if (!points) return null
          return (
            <Arrow
              key={arrow.id}
              points={points}
              stroke={ARROW_COLOR}
              strokeWidth={Math.max(1, arrow.similarity_score * 3)}
              opacity={0.4 + arrow.similarity_score * 0.4}
              pointerLength={10}
              pointerWidth={8}
              fill={ARROW_COLOR}
            />
          )
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <Group
            key={node.id}
            x={node.x}
            y={node.y}
            draggable
            onDragEnd={(e) => handleDragEnd(node.id, e.target.x(), e.target.y())}
            onClick={() => {
              setSelectedNodeId(node.id)
              onNodeSelect(node.id)
            }}
          >
            <Rect
              width={NODE_W}
              height={NODE_H}
              fill={NODE_COLOR}
              stroke={selectedNodeId === node.id ? SELECTED_BORDER : NODE_BORDER}
              strokeWidth={selectedNodeId === node.id ? 2 : 1}
              cornerRadius={8}
              shadowColor="#6c63ff"
              shadowBlur={selectedNodeId === node.id ? 12 : 4}
              shadowOpacity={0.3}
            />
            <Text
              x={12}
              y={12}
              width={NODE_W - 24}
              height={NODE_H - 24}
              text={node.title}
              fontSize={13}
              fill={TEXT_COLOR}
              ellipsis
              wrap="none"
            />
          </Group>
        ))}
      </Layer>
    </Stage>
  )
}
