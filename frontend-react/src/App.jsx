import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [health, setHealth] = useState({ ollama: 'disconnected', redis: 'disconnected' })
  const messagesEndRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    createConversation()
    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const checkHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/health`)
      setHealth(res.data)
    } catch (err) {
      setHealth({ ollama: 'disconnected', redis: 'disconnected' })
    }
  }

  const createConversation = async () => {
    try {
      const res = await axios.post(`${API_BASE}/conversations`)
      setConversationId(res.data.conversation_id)
      setMessages([])
    } catch (err) {
      console.error('Failed to create conversation:', err)
    }
  }

  const sendTextMessage = async () => {
    if (!inputText.trim() || !conversationId) return
    
    const userMessage = { role: 'user', content: inputText, time: new Date().toLocaleTimeString() }
    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)
    
    try {
      const res = await axios.post(`${API_BASE}/conversations/${conversationId}/text-message`, 
        { message: inputText },
        { headers: { 'Content-Type': 'application/json' } }
      )
      const aiMessage = { role: 'ai', content: res.data.ai_response, time: new Date().toLocaleTimeString() }
      setMessages(prev => [...prev, aiMessage])
    } catch (err) {
      console.error('Failed to send message:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorderRef.current = new MediaRecorder(stream)
      const audioChunks = []
      
      mediaRecorderRef.current.ondataavailable = e => audioChunks.push(e.data)
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
        stream.getTracks().forEach(t => t.stop())
        await sendVoiceMessage(audioBlob)
      }
      
      mediaRecorderRef.current.start()
      setIsRecording(true)
    } catch (err) {
      console.error('Failed to start recording:', err)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const sendVoiceMessage = async (audioBlob) => {
    if (!conversationId) return
    
    setMessages(prev => [...prev, { role: 'user', content: '🎤 Voice message', time: new Date().toLocaleTimeString() }])
    setIsLoading(true)
    
    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'audio.webm')
      
      const res = await axios.post(`${API_BASE}/conversations/${conversationId}/voice-message`, formData)
      const aiMessage = { role: 'ai', content: res.data.ai_response, time: new Date().toLocaleTimeString() }
      setMessages(prev => [...prev, aiMessage])
    } catch (err) {
      console.error('Failed to send voice message:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendTextMessage()
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">🎙️</div>
          <h1>VoiceAI Support</h1>
        </div>
        <div className="status-bar">
          <div className="status-item">
            <span className={`status-dot ${health.ollama}`}></span>
            <span>Ollama {health.ollama === 'connected' ? '✓' : '✗'}</span>
          </div>
          <div className="status-item">
            <span className={`status-dot ${health.redis}`}></span>
            <span>Redis {health.redis === 'connected' ? '✓' : '✗'}</span>
          </div>
        </div>
      </header>

      <main className="main">
        <section className="chat-section">
          <div className="chat-header">
            <h2>Conversation</h2>
            <span className="conversation-id">
              {conversationId ? `ID: ${conversationId.slice(0, 8)}...` : 'Creating...'}
            </span>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && !isLoading && (
              <div className="loading-indicator">
                <p>Start a conversation by typing a message or recording your voice 🎤</p>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-text">{msg.content}</div>
                  <div className="message-time">{msg.time}</div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message ai">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="wave-container">
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <div className="chat-input-wrapper">
              <textarea
                ref={textareaRef}
                className="chat-input"
                placeholder="Type your message..."
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                rows={1}
              />
              <button 
                className={`voice-btn ${isRecording ? 'recording' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
              >
                {isRecording ? '⏹' : '🎤'}
              </button>
              <button 
                className="send-btn" 
                onClick={sendTextMessage}
                disabled={!inputText.trim() || isLoading}
              >
                ➤
              </button>
            </div>
          </div>
        </section>

        <aside className="sidebar">
          <button className="new-chat-btn" onClick={createConversation}>
            + New Conversation
          </button>

          <div className="card">
            <h3>Session Stats</h3>
            <div className="stat-grid">
              <div className="stat-item">
                <div className="stat-value">{messages.filter(m => m.role === 'user').length}</div>
                <div className="stat-label">Messages</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{messages.length}</div>
                <div className="stat-label">Total</div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3>System Status</h3>
            <div className="stat-grid">
              <div className="stat-item">
                <div className="stat-value" style={{ color: health.ollama === 'connected' ? 'var(--success)' : 'var(--error)' }}>
                  {health.ollama === 'connected' ? '✓' : '✗'}
                </div>
                <div className="stat-label">LLM Engine</div>
              </div>
              <div className="stat-item">
                <div className="stat-value" style={{ color: health.redis === 'connected' ? 'var(--success)' : 'var(--error)' }}>
                  {health.redis === 'connected' ? '✓' : '✗'}
                </div>
                <div className="stat-label">Cache</div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3>Model</h3>
            <div className="stat-item" style={{ gridColumn: 'span 2' }}>
              <div className="stat-value" style={{ fontSize: '1rem' }}>{health.model || 'llama3.2'}</div>
              <div className="stat-label">Active LLM</div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  )
}

export default App
