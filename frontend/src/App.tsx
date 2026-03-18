import { useEffect, useMemo, useState } from 'react'

type CallCategory =
  | 'medical'
  | 'insurance'
  | 'utility'
  | 'government'
  | 'repair'
  | 'workplace'
  | 'financial'
  | 'general'

type PrepRequest = {
  objective: string
  category: CallCategory
  target_entity: string
  target_phone: string
  user_notes: string
}

type FlowchartNode = {
  id: string
  speaker: 'you' | 'them'
  text: string
  is_question: boolean
  your_response: string
  notes: string
  children: string[]
}

type PrepResponse = {
  session_id: number
  objective_summary: string
  estimated_duration: string
  what_to_have_ready: string[]
  opening_script: string
  flowchart: FlowchartNode[]
  likely_questions: { question: string; suggested_answer: string; tip: string }[]
  anxiety_notes: string
  worst_case: string
}

type CoachMessage = {
  timestamp: number
  message_type: 'prompt' | 'info' | 'warning' | 'reassurance'
  text: string
  auto_fill_data: string
  urgency: 'normal' | 'attention' | 'important'
}

type ProxyRequest = {
  objective: string
  category: CallCategory
  target_entity: string
  target_phone: string
  decision_boundaries: string[]
  max_duration_seconds: number
}

type ProxyPlan = {
  session_id?: number
  status: string
  opening_statement: string
  target_phone: string
  message: string
}

type ProxySummary = {
  session_id: number
  status: string
  transcript: string
  summary: string
  decisions_made: string[]
  needs_your_confirmation: string[]
  next_steps: string[]
}

type SessionHistoryItem = {
  id: number
  mode: string
  category: string
  objective: string
  target_entity: string
  target_phone: string
  status: string
  created_at: string
}

type UserProfile = {
  id?: number
  display_name: string
  date_of_birth: string
  phone_number: string
  email: string
  address: string
  insurance_provider: string
  insurance_id: string
  primary_doctor: string
  medications: string
  allergies: string
  emergency_contact: string
  preferred_pharmacy: string
  sensory_profile: string
  max_hold_time_seconds: number
  preferred_call_times: string
  notes: string
}

type Mode = 'prep' | 'coach' | 'proxy' | 'history' | 'profile'

// Backend dev server URL (unsandboxed, on your Mac)
const API_BASE = 'http://localhost:8001'

function useApiBase() {
  return useMemo(() => {
    return API_BASE
  }, [])
}

function App() {
  const apiBase = useApiBase()
  const [mode, setMode] = useState<Mode>('prep')

  return (
    <div className="app-root">
      <header className="app-header">
        <div>
          <h1>PhoneAngel</h1>
          <p>AI phone call prep, live coaching, and proxy calling.</p>
        </div>
        <span className="app-badge">DigitalOcean Gradient AI</span>
      </header>

      <nav className="app-nav">
        <NavButton label="Prep" active={mode === 'prep'} onClick={() => setMode('prep')} />
        <NavButton label="Live Coach" active={mode === 'coach'} onClick={() => setMode('coach')} />
        <NavButton label="AI Proxy" active={mode === 'proxy'} onClick={() => setMode('proxy')} />
        <NavButton label="History" active={mode === 'history'} onClick={() => setMode('history')} />
        <NavButton label="Profile" active={mode === 'profile'} onClick={() => setMode('profile')} />
      </nav>

      <main className="app-main">
        {mode === 'prep' && <PrepMode apiBase={apiBase} />}
        {mode === 'coach' && <CoachMode apiBase={apiBase} />}
        {mode === 'proxy' && <ProxyMode apiBase={apiBase} />}
        {mode === 'history' && <HistoryView apiBase={apiBase} />}
        {mode === 'profile' && <ProfileView apiBase={apiBase} />}
      </main>
    </div>
  )
}

type NavButtonProps = {
  label: string
  active: boolean
  onClick: () => void
}

function NavButton({ label, active, onClick }: NavButtonProps) {
  return (
    <button
      type="button"
      className={active ? 'nav-button nav-button-active' : 'nav-button'}
      onClick={onClick}
    >
      {label}
    </button>
  )
}

type PrepModeProps = { apiBase: string }

function PrepMode({ apiBase }: PrepModeProps) {
  const [form, setForm] = useState<PrepRequest>({
    objective: '',
    category: 'general',
    target_entity: '',
    target_phone: '',
    user_notes: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PrepResponse | null>(null)

  const handleChange = (field: keyof PrepRequest, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const resp = await fetch(`${apiBase}/api/prep`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail ?? `Request failed with ${resp.status}`)
      }

      const data = (await resp.json()) as PrepResponse
      setResult(data)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section aria-labelledby="prep-title">
      <div className="section-header">
        <div>
          <h2 id="prep-title">Mode 1 — Call Prep</h2>
          <p>See the whole conversation before you dial.</p>
        </div>
      </div>

      <div className="layout-two-column">
        <form className="card" onSubmit={handleSubmit}>
          <h3>What call do you need to make?</h3>

          <label className="field">
            <span>Objective</span>
            <textarea
              required
              value={form.objective}
              onChange={(e) => handleChange('objective', e.target.value)}
              placeholder="Reschedule my dentist appointment to next Thursday afternoon."
              rows={3}
            />
          </label>

          <label className="field">
            <span>Category</span>
            <select
              value={form.category}
              onChange={(e) => handleChange('category', e.target.value as CallCategory)}
            >
              <option value="general">General</option>
              <option value="medical">Medical</option>
              <option value="insurance">Insurance</option>
              <option value="utility">Utility / Bills</option>
              <option value="government">Government</option>
              <option value="repair">Repairs / Maintenance</option>
              <option value="workplace">Workplace</option>
              <option value="financial">Financial</option>
            </select>
          </label>

          <label className="field">
            <span>Who are you calling?</span>
            <input
              type="text"
              value={form.target_entity}
              onChange={(e) => handleChange('target_entity', e.target.value)}
              placeholder="Dr. Smith's Dental Office"
            />
          </label>

          <label className="field">
            <span>Phone number (optional)</span>
            <input
              type="tel"
              value={form.target_phone}
              onChange={(e) => handleChange('target_phone', e.target.value)}
              placeholder="+1 (555) 123-4567"
            />
          </label>

          <label className="field">
            <span>Anything to mention or avoid?</span>
            <textarea
              value={form.user_notes}
              onChange={(e) => handleChange('user_notes', e.target.value)}
              placeholder="For example: I prefer afternoon calls and need extra time to process information."
              rows={3}
            />
          </label>

          {error && <p className="error-text">{error}</p>}

          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? 'Preparing call plan…' : 'Generate call plan'}
          </button>
        </form>

        <div className="card results-pane">
          {!result && !loading && (
            <p className="muted">
              Your flowchart, script, and questions will appear here after you generate a plan.
            </p>
          )}

          {loading && <p>Talking to PhoneAngel… this usually takes a few seconds.</p>}

          {result && (
            <div className="prep-results">
              <section>
                <h3>Overview</h3>
                <p>{result.objective_summary}</p>
                <p className="muted">Estimated duration: {result.estimated_duration}</p>
                {result.what_to_have_ready?.length > 0 && (
                  <>
                    <h4>Have these ready</h4>
                    <ul>
                      {result.what_to_have_ready.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </>
                )}
              </section>

              <section>
                <h3>Opening script</h3>
                <p className="script-block">{result.opening_script}</p>
              </section>

              {result.likely_questions?.length > 0 && (
                <section>
                  <h3>Likely questions</h3>
                  <div className="table">
                    <div className="table-row table-head">
                      <div>They might ask…</div>
                      <div>Suggested answer</div>
                      <div>Tip</div>
                    </div>
                    {result.likely_questions.map((q, idx) => (
                      <div className="table-row" key={`${q.question}-${idx}`}>
                        <div>{q.question}</div>
                        <div>{q.suggested_answer}</div>
                        <div className="muted">{q.tip}</div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {result.flowchart?.length > 0 && (
                <section>
                  <h3>Conversation flowchart</h3>
                  <p className="muted">
                    Follow the steps from top to bottom. Boxes in blue are you; grey is them.
                  </p>
                  <FlowchartList nodes={result.flowchart} />
                </section>
              )}

              <section className="grid-two">
                <div>
                  <h3>Anxiety notes</h3>
                  <p className="muted">{result.anxiety_notes}</p>
                </div>
                <div>
                  <h3>Worst-case plan</h3>
                  <p className="muted">{result.worst_case}</p>
                </div>
              </section>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

type FlowchartListProps = {
  nodes: FlowchartNode[]
}

function FlowchartList({ nodes }: FlowchartListProps) {
  const nodeMap = useMemo(
    () => new Map(nodes.map((n) => [n.id, n])),
    [nodes],
  )

  const roots = useMemo(() => {
    const childIds = new Set<string>()
    nodes.forEach((n) => n.children.forEach((c) => childIds.add(c)))
    return nodes.filter((n) => !childIds.has(n.id))
  }, [nodes])

  const renderNode = (node: FlowchartNode) => (
    <li key={node.id} className={`flow-node flow-node-${node.speaker}`}>
      <div className="flow-node-main">
        <div className="flow-node-speaker">{node.speaker === 'you' ? 'You' : 'Them'}</div>
        <div className="flow-node-text">{node.text}</div>
      </div>
      {node.is_question && node.your_response && (
        <div className="flow-node-response">
          <span className="label">Suggested response:</span> {node.your_response}
        </div>
      )}
      {node.notes && <div className="flow-node-notes">{node.notes}</div>}
      {node.children.length > 0 && (
        <ul className="flow-children">
          {node.children.map((childId) => {
            const child = nodeMap.get(childId)
            return child ? renderNode(child) : null
          })}
        </ul>
      )}
    </li>
  )

  return (
    <ul className="flow-list">
      {roots.length > 0 ? roots.map((n) => renderNode(n)) : nodes.map((n) => renderNode(n))}
    </ul>
  )
}

type CoachModeProps = { apiBase: string }

function CoachMode({ apiBase }: CoachModeProps) {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [objective, setObjective] = useState('')
  const [name, setName] = useState('')
  const [chunk, setChunk] = useState('')
  const [messages, setMessages] = useState<CoachMessage[]>([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    return () => {
      socket?.close()
    }
  }, [socket])

  const connect = () => {
    setError(null)
    const ws = new WebSocket(apiBase.replace('http', 'ws') + '/ws/coach/1')

    ws.onopen = () => {
      setConnected(true)
      ws.send(
        JSON.stringify({
          objective: objective || 'General phone call',
          name: name || undefined,
        }),
      )
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'coaching') {
          const newMessages = (data.messages ?? []) as CoachMessage[]
          setMessages((prev) => [...prev, ...newMessages])
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onerror = () => {
      setError('WebSocket error. Is the backend running on the same host?')
    }

    ws.onclose = () => {
      setConnected(false)
      setSocket(null)
    }

    setSocket(ws)
  }

  const disconnect = () => {
    socket?.close()
  }

  const sendChunk = () => {
    if (!socket || !connected || !chunk.trim()) return
    socket.send(JSON.stringify({ speaker: 'them', text: chunk }))
    setChunk('')
  }

  return (
    <section aria-labelledby="coach-title">
      <div className="section-header">
        <div>
          <h2 id="coach-title">Mode 2 — Live Coach</h2>
          <p>Stream in transcript chunks and get real-time coaching prompts.</p>
        </div>
      </div>

      <div className="layout-two-column">
        <div className="card">
          <h3>Connect</h3>
          <label className="field">
            <span>What is this call about?</span>
            <input
              type="text"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Change my appointment time."
            />
          </label>
          <label className="field">
            <span>Your name (optional)</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Alex"
            />
          </label>

          <div className="button-row">
            {!connected ? (
              <button type="button" className="primary-button" onClick={connect}>
                Connect coach
              </button>
            ) : (
              <button type="button" className="secondary-button" onClick={disconnect}>
                Disconnect
              </button>
            )}
          </div>
          {error && <p className="error-text">{error}</p>}

          <hr />

          <h3>Send transcript chunk</h3>
          <p className="muted">
            In production this comes from real-time speech-to-text. For now you can paste what was
            just said and hit &quot;Send&quot;.
          </p>
          <textarea
            rows={3}
            value={chunk}
            onChange={(e) => setChunk(e.target.value)}
            placeholder='For example: "Can you read me your date of birth?"'
          />
          <button type="button" className="primary-button" onClick={sendChunk} disabled={!connected}>
            Send chunk
          </button>
        </div>

        <div className="card results-pane">
          <h3>Coaching feed</h3>
          {messages.length === 0 && (
            <p className="muted">Coaching prompts will appear here during your call.</p>
          )}
          <ul className="coach-list">
            {messages.map((m, idx) => (
              <li key={`${m.timestamp}-${idx}`} className={`coach-item coach-${m.message_type}`}>
                <div className="coach-meta">
                  <span className="coach-type">{m.message_type}</span>
                  {m.urgency !== 'normal' && <span className="coach-urgency">{m.urgency}</span>}
                </div>
                <div className="coach-text">{m.text}</div>
                {m.auto_fill_data && (
                  <div className="coach-autofill">
                    <span className="label">Auto-fill:</span> {m.auto_fill_data}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}

type ProxyModeProps = { apiBase: string }

function ProxyMode({ apiBase }: ProxyModeProps) {
  const [form, setForm] = useState<ProxyRequest>({
    objective: '',
    category: 'general',
    target_entity: '',
    target_phone: '',
    decision_boundaries: [],
    max_duration_seconds: 300,
  })
  const [boundariesRaw, setBoundariesRaw] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [plan, setPlan] = useState<ProxyPlan | null>(null)
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [transcript, setTranscript] = useState('')
  const [summary, setSummary] = useState<ProxySummary | null>(null)
  const [summarizing, setSummarizing] = useState(false)

  const handleChange = (field: keyof ProxyRequest, value: string) => {
    if (field === 'max_duration_seconds') {
      const num = parseInt(value || '0', 10)
      setForm((prev) => ({ ...prev, max_duration_seconds: Number.isNaN(num) ? 0 : num }))
    } else if (field === 'category') {
      setForm((prev) => ({ ...prev, category: value as CallCategory }))
    } else {
      setForm((prev) => ({ ...prev, [field]: value }))
    }
  }

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setPlan(null)
    setSummary(null)

    const boundaries =
      boundariesRaw
        .split('\n')
        .map((b) => b.trim())
        .filter(Boolean) ?? []

    try {
      const resp = await fetch(`${apiBase}/api/proxy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, decision_boundaries: boundaries }),
      })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail ?? `Request failed with ${resp.status}`)
      }
      const data = (await resp.json()) as ProxyPlan & { session_id: number }
      setPlan(data)
      setSessionId(data.session_id)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleSummarize = async () => {
    if (!sessionId) return
    setSummarizing(true)
    setError(null)

    try {
      const url = new URL(`${apiBase}/api/proxy/${sessionId}/summarize`)
      if (transcript.trim()) {
        url.searchParams.set('transcript', transcript)
      }
      const resp = await fetch(url, { method: 'POST' })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail ?? `Request failed with ${resp.status}`)
      }
      const data = (await resp.json()) as ProxySummary
      setSummary(data)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSummarizing(false)
    }
  }

  return (
    <section aria-labelledby="proxy-title">
      <div className="section-header">
        <div>
          <h2 id="proxy-title">Mode 3 — AI Proxy Caller</h2>
          <p>Have PhoneAngel plan and later summarize calls made on your behalf.</p>
        </div>
      </div>

      <div className="layout-two-column">
        <form className="card" onSubmit={handleGeneratePlan}>
          <h3>Call details</h3>

          <label className="field">
            <span>Objective</span>
            <textarea
              required
              value={form.objective}
              onChange={(e) => handleChange('objective', e.target.value)}
              placeholder="Book a new primary-care appointment for next week."
              rows={3}
            />
          </label>

          <label className="field">
            <span>Category</span>
            <select
              value={form.category}
              onChange={(e) => handleChange('category', e.target.value as CallCategory)}
            >
              <option value="general">General</option>
              <option value="medical">Medical</option>
              <option value="insurance">Insurance</option>
              <option value="utility">Utility / Bills</option>
              <option value="government">Government</option>
              <option value="repair">Repairs / Maintenance</option>
              <option value="workplace">Workplace</option>
              <option value="financial">Financial</option>
            </select>
          </label>

          <label className="field">
            <span>Who should we call?</span>
            <input
              type="text"
              value={form.target_entity}
              onChange={(e) => handleChange('target_entity', e.target.value)}
              placeholder="Dr. Smith's Office"
            />
          </label>

          <label className="field">
            <span>Phone number</span>
            <input
              type="tel"
              value={form.target_phone}
              onChange={(e) => handleChange('target_phone', e.target.value)}
              placeholder="+1 (555) 123-4567"
            />
          </label>

          <label className="field">
            <span>What decisions can PhoneAngel make on its own?</span>
            <textarea
              value={boundariesRaw}
              onChange={(e) => setBoundariesRaw(e.target.value)}
              placeholder={'One per line, for example:\nAccept any appointment Thu or Fri after 2pm.\nDo NOT agree to a copay over $50.'}
              rows={4}
            />
          </label>

          <label className="field">
            <span>Max call length (seconds)</span>
            <input
              type="number"
              min={60}
              max={1800}
              value={form.max_duration_seconds}
              onChange={(e) => handleChange('max_duration_seconds', e.target.value)}
            />
          </label>

          {error && <p className="error-text">{error}</p>}

          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? 'Planning call…' : 'Generate proxy call plan'}
          </button>
        </form>

        <div className="card results-pane">
          {!plan && !loading && (
            <p className="muted">
              After you generate a plan you&apos;ll see the opening script and details here.
            </p>
          )}

          {loading && <p>Talking to PhoneAngel…</p>}

          {plan && (
            <div className="proxy-results">
              <section>
                <h3>Planned opening statement</h3>
                <p className="script-block">{plan.opening_statement}</p>
                <p className="muted">
                  Target number: <strong>{plan.target_phone}</strong>
                </p>
                <p className="muted">{plan.message}</p>
                <p className="muted">
                  Session ID: <code>{sessionId}</code>
                </p>
              </section>

              <section>
                <h3>After the call</h3>
                <p className="muted">
                  When the call is finished, paste the transcript below and PhoneAngel will create a
                  summary and list of next steps.
                </p>
                <textarea
                  rows={6}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Paste call transcript here (optional). If left empty, the server will use any transcript stored for this session."
                />
                <button
                  type="button"
                  className="primary-button"
                  onClick={handleSummarize}
                  disabled={summarizing}
                >
                  {summarizing ? 'Summarizing…' : 'Summarize call'}
                </button>
              </section>

              {summary && (
                <section className="summary-section">
                  <h3>Call summary</h3>
                  <p>{summary.summary}</p>

                  {summary.decisions_made?.length > 0 && (
                    <>
                      <h4>Decisions made</h4>
                      <ul>
                        {summary.decisions_made.map((d) => (
                          <li key={d}>{d}</li>
                        ))}
                      </ul>
                    </>
                  )}

                  {summary.needs_your_confirmation?.length > 0 && (
                    <>
                      <h4>Needs your confirmation</h4>
                      <ul>
                        {summary.needs_your_confirmation.map((d) => (
                          <li key={d}>{d}</li>
                        ))}
                      </ul>
                    </>
                  )}

                  {summary.next_steps?.length > 0 && (
                    <>
                      <h4>Next steps</h4>
                      <ul>
                        {summary.next_steps.map((d) => (
                          <li key={d}>{d}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </section>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

type HistoryViewProps = { apiBase: string }

function HistoryView({ apiBase }: HistoryViewProps) {
  const [items, setItems] = useState<SessionHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const resp = await fetch(`${apiBase}/api/sessions/1`)
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}))
          throw new Error(data.detail ?? `Request failed with ${resp.status}`)
        }
        const data = (await resp.json()) as SessionHistoryItem[]
        setItems(data)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [apiBase])

  return (
    <section aria-labelledby="history-title">
      <div className="section-header">
        <div>
          <h2 id="history-title">History</h2>
          <p>See your past prepared, coached, and proxy calls.</p>
        </div>
      </div>

      <div className="card">
        {loading && <p>Loading history…</p>}
        {error && <p className="error-text">{error}</p>}
        {!loading && !error && items.length === 0 && (
          <p className="muted">No call sessions yet. Generate a plan or start a call to begin.</p>
        )}

        {items.length > 0 && (
          <div className="table">
            <div className="table-row table-head">
              <div>When</div>
              <div>Mode</div>
              <div>Category</div>
              <div>Objective</div>
              <div>Status</div>
            </div>
            {items.map((s) => (
              <div className="table-row" key={s.id}>
                <div>{new Date(s.created_at).toLocaleString()}</div>
                <div>{s.mode}</div>
                <div>{s.category}</div>
                <div>{s.objective}</div>
                <div>{s.status}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

type ProfileViewProps = { apiBase: string }

function ProfileView({ apiBase }: ProfileViewProps) {
  const [profile, setProfile] = useState<UserProfile>({
    id: 1,
    display_name: '',
    date_of_birth: '',
    phone_number: '',
    email: '',
    address: '',
    insurance_provider: '',
    insurance_id: '',
    primary_doctor: '',
    medications: '',
    allergies: '',
    emergency_contact: '',
    preferred_pharmacy: '',
    sensory_profile: 'normal',
    max_hold_time_seconds: 120,
    preferred_call_times: '',
    notes: '',
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const resp = await fetch(`${apiBase}/api/profile/1`)
        if (!resp.ok) {
          if (resp.status === 404) {
            setLoading(false)
            return
          }
          const data = await resp.json().catch(() => ({}))
          throw new Error(data.detail ?? `Request failed with ${resp.status}`)
        }
        const data = (await resp.json()) as UserProfile
        setProfile(data)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [apiBase])

  const handleChange = (field: keyof UserProfile, value: string | number) => {
    setSaved(false)
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      const resp = await fetch(`${apiBase}/api/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail ?? `Request failed with ${resp.status}`)
      }
      const data = (await resp.json()) as UserProfile
      setProfile(data)
      setSaved(true)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <section aria-labelledby="profile-title">
      <div className="section-header">
        <div>
          <h2 id="profile-title">Profile</h2>
          <p>Information used to auto-fill answers and tailor coaching.</p>
        </div>
      </div>

      <form className="card" onSubmit={handleSave}>
        {loading && <p>Loading profile…</p>}
        {error && <p className="error-text">{error}</p>}

        <div className="layout-two-column-compact">
          <label className="field">
            <span>Preferred name</span>
            <input
              type="text"
              value={profile.display_name}
              onChange={(e) => handleChange('display_name', e.target.value)}
            />
          </label>

          <label className="field">
            <span>Date of birth</span>
            <input
              type="text"
              value={profile.date_of_birth}
              onChange={(e) => handleChange('date_of_birth', e.target.value)}
              placeholder="YYYY-MM-DD"
            />
          </label>

          <label className="field">
            <span>Phone number</span>
            <input
              type="tel"
              value={profile.phone_number}
              onChange={(e) => handleChange('phone_number', e.target.value)}
            />
          </label>

          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={profile.email}
              onChange={(e) => handleChange('email', e.target.value)}
              placeholder="you@example.com"
            />
          </label>

          <label className="field">
            <span>Insurance provider</span>
            <input
              type="text"
              value={profile.insurance_provider}
              onChange={(e) => handleChange('insurance_provider', e.target.value)}
              placeholder="e.g. BlueCross BlueShield"
            />
          </label>

          <label className="field">
            <span>Insurance ID</span>
            <input
              type="text"
              value={profile.insurance_id}
              onChange={(e) => handleChange('insurance_id', e.target.value)}
            />
          </label>

          <label className="field">
            <span>Primary doctor</span>
            <input
              type="text"
              value={profile.primary_doctor}
              onChange={(e) => handleChange('primary_doctor', e.target.value)}
              placeholder="e.g. Dr. Smith (dentist)"
            />
          </label>

          <label className="field">
            <span>Medications</span>
            <input
              type="text"
              value={profile.medications}
              onChange={(e) => handleChange('medications', e.target.value)}
              placeholder="e.g. None, or Ibuprofen 200mg"
            />
          </label>

          <label className="field">
            <span>Allergies</span>
            <input
              type="text"
              value={profile.allergies}
              onChange={(e) => handleChange('allergies', e.target.value)}
              placeholder="e.g. None, or Penicillin"
            />
          </label>

          <label className="field">
            <span>Emergency contact</span>
            <input
              type="text"
              value={profile.emergency_contact}
              onChange={(e) => handleChange('emergency_contact', e.target.value)}
              placeholder="e.g. Sai — (415) 555-0199"
            />
          </label>

          <label className="field field-full">
            <span>Address</span>
            <input
              type="text"
              value={profile.address}
              onChange={(e) => handleChange('address', e.target.value)}
            />
          </label>

          <label className="field">
            <span>Preferred pharmacy</span>
            <input
              type="text"
              value={profile.preferred_pharmacy}
              onChange={(e) => handleChange('preferred_pharmacy', e.target.value)}
            />
          </label>

          <label className="field">
            <span>Sensory profile</span>
            <select
              value={profile.sensory_profile}
              onChange={(e) => handleChange('sensory_profile', e.target.value)}
            >
              <option value="normal">Normal</option>
              <option value="voice_sensitive">Voice sensitive</option>
              <option value="silence_anxious">Silence makes me anxious</option>
              <option value="hold_music_trigger">Hold music is triggering</option>
            </select>
          </label>

          <label className="field">
            <span>Max hold time (seconds)</span>
            <input
              type="number"
              min={30}
              max={1200}
              value={profile.max_hold_time_seconds}
              onChange={(e) =>
                handleChange('max_hold_time_seconds', parseInt(e.target.value || '0', 10))
              }
            />
          </label>

          <label className="field field-full">
            <span>Preferred call times</span>
            <input
              type="text"
              value={profile.preferred_call_times}
              onChange={(e) => handleChange('preferred_call_times', e.target.value)}
              placeholder="For example: Weekdays after 3pm."
            />
          </label>

          <label className="field field-full">
            <span>Accessibility notes</span>
            <textarea
              rows={3}
              value={profile.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              placeholder="Anything you want PhoneAngel to know about how to support you."
            />
          </label>
        </div>

        <div className="button-row">
          <button type="submit" className="primary-button" disabled={saving}>
            {saving ? 'Saving…' : 'Save profile'}
          </button>
          {saved && <span className="success-text">Saved.</span>}
        </div>
      </form>
    </section>
  )
}

export default App
