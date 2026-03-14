import { useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000/api'

export function App() {
  const [sessionId] = useState('demo-session')
  const [narrative, setNarrative] = useState('点击“生成叙事”以触发最小命令链路。')
  const [health, setHealth] = useState(null)

  const generateNarrative = async () => {
    const response = await fetch(`${API_BASE}/orchestration/narrative`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: '探索废弃古堡', sessionId })
    })
    const data = await response.json()
    setNarrative(data.narrative)
  }

  const loadHealth = async () => {
    const response = await fetch(`${API_BASE}/health`)
    const data = await response.json()
    setHealth(data)
  }

  return (
    <main className="container">
      <h1>Desktop TRPG 启动健康检查</h1>
      <section className="card">
        <button onClick={loadHealth}>刷新健康检查</button>
        {health && (
          <ul>
            <li>模型可用性：{health.model.available ? '可用' : '不可用'}（{health.model.provider}）</li>
            <li>数据库可用性：{health.database.available ? '可用' : '不可用'}（{health.database.engine}）</li>
          </ul>
        )}
      </section>

      <section className="card">
        <h2>最小命令链路</h2>
        <button onClick={generateNarrative}>生成叙事</button>
        <p>{narrative}</p>
      </section>
    </main>
  )
}
