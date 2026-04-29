import { useEffect, useState } from 'react'
import { useAppStore } from '../store/useAppStore'

export default function ModelSelector() {
  const { activeModel, setActiveModel } = useAppStore()
  const [models, setModels] = useState<string[]>([])

  useEffect(() => {
    fetch('/api/models')
      .then((r) => r.json())
      .then((d) => setModels(d.models || []))
  }, [])

  return (
    <select
      value={activeModel}
      onChange={(e) => setActiveModel(e.target.value)}
      className="bg-[#1a1a2e] text-[#a78bfa] border border-[#2a2a4a] rounded-md px-2 py-1 text-xs outline-none cursor-pointer"
    >
      {models.map((m) => (
        <option key={m} value={m}>{m}</option>
      ))}
    </select>
  )
}
