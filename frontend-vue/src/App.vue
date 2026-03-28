<template>
  <div class="app">
    <header class="header">
      <div class="logo">
        <div class="logo-icon">🎙️</div>
        <h1>VoiceAI Support</h1>
      </div>
      <div class="status-bar">
        <div class="status-item">
          <span :class="['status-dot', health.ollama]"></span>
          <span>Ollama {{ health.ollama === 'connected' ? '✓' : '✗' }}</span>
        </div>
        <div class="status-item">
          <span :class="['status-dot', health.redis]"></span>
          <span>Redis {{ health.redis === 'connected' ? '✓' : '✗' }}</span>
        </div>
      </div>
    </header>

    <main class="main">
      <section class="chat-section">
        <div class="chat-header">
          <h2>Conversation</h2>
          <span class="conversation-id">
            {{ conversationId ? `ID: ${conversationId.slice(0, 8)}...` : 'Creating...' }}
          </span>
        </div>

        <div class="chat-messages">
          <div v-if="messages.length === 0 && !isLoading" class="loading-indicator">
            <p>Start a conversation by typing a message or recording your voice 🎤</p>
          </div>
          
          <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
            <div class="message-avatar">
              {{ msg.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content">
              <div class="message-text">{{ msg.content }}</div>
              <div class="message-time">{{ msg.time }}</div>
            </div>
          </div>

          <div v-if="isLoading" class="message ai">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div class="wave-container">
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
                <div class="wave-bar"></div>
              </div>
            </div>
          </div>
          <div ref="messagesEnd"></div>
        </div>

        <div class="chat-input-container">
          <div class="chat-input-wrapper">
            <textarea
              class="chat-input"
              placeholder="Type your message..."
              v-model="inputText"
              @keyup.enter.exact="sendTextMessage"
              rows="1"
            ></textarea>
            <button 
              :class="['voice-btn', { recording: isRecording }]"
              @click="isRecording ? stopRecording() : startRecording()"
            >
              {{ isRecording ? '⏹' : '🎤' }}
            </button>
            <button 
              class="send-btn" 
              @click="sendTextMessage"
              :disabled="!inputText.trim() || isLoading"
            >
              ➤
            </button>
          </div>
        </div>
      </section>

      <aside class="sidebar">
        <button class="new-chat-btn" @click="createConversation">
          + New Conversation
        </button>

        <div class="card">
          <h3>Session Stats</h3>
          <div class="stat-grid">
            <div class="stat-item">
              <div class="stat-value">{{ userMessagesCount }}</div>
              <div class="stat-label">Messages</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ messages.length }}</div>
              <div class="stat-label">Total</div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>System Status</h3>
          <div class="stat-grid">
            <div class="stat-item">
              <div class="stat-value" :style="{ color: health.ollama === 'connected' ? 'var(--success)' : 'var(--error)' }">
                {{ health.ollama === 'connected' ? '✓' : '✗' }}
              </div>
              <div class="stat-label">LLM Engine</div>
            </div>
            <div class="stat-item">
              <div class="stat-value" :style="{ color: health.redis === 'connected' ? 'var(--success)' : 'var(--error)' }">
                {{ health.redis === 'connected' ? '✓' : '✗' }}
              </div>
              <div class="stat-label">Cache</div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>Model</h3>
          <div class="stat-item" style="grid-column: span 2">
            <div class="stat-value" style="font-size: 1rem">{{ health.model || 'llama3.2' }}</div>
            <div class="stat-label">Active LLM</div>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUpdated, nextTick } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const conversationId = ref(null)
const messages = ref([])
const inputText = ref('')
const isRecording = ref(false)
const isLoading = ref(false)
const health = ref({ ollama: 'disconnected', redis: 'disconnected' })
const messagesEnd = ref(null)
let mediaRecorder = null

const userMessagesCount = computed(() => {
  return messages.value.filter(m => m.role === 'user').length
})

onMounted(() => {
  createConversation()
  checkHealth()
  setInterval(checkHealth, 10000)
})

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesEnd.value) {
      messagesEnd.value.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

const checkHealth = async () => {
  try {
    const res = await axios.get(`${API_BASE}/health`)
    health.value = res.data
  } catch (err) {
    health.value = { ollama: 'disconnected', redis: 'disconnected' }
  }
}

const createConversation = async () => {
  try {
    const res = await axios.post(`${API_BASE}/conversations`)
    conversationId.value = res.data.conversation_id
    messages.value = []
  } catch (err) {
    console.error('Failed to create conversation:', err)
  }
}

const sendTextMessage = async () => {
  if (!inputText.value.trim() || !conversationId.value) return
  
  const userMessage = { role: 'user', content: inputText.value, time: new Date().toLocaleTimeString() }
  messages.value.push(userMessage)
  inputText.value = ''
  isLoading.value = true
  scrollToBottom()
  
  try {
    const res = await axios.post(`${API_BASE}/conversations/${conversationId.value}/text-message`, 
      { message: userMessage.content },
      { headers: { 'Content-Type': 'application/json' } }
    )
    const aiMessage = { role: 'ai', content: res.data.ai_response, time: new Date().toLocaleTimeString() }
    messages.value.push(aiMessage)
  } catch (err) {
    console.error('Failed to send message:', err)
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    const audioChunks = []
    
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data)
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
      stream.getTracks().forEach(t => t.stop())
      await sendVoiceMessage(audioBlob)
    }
    
    mediaRecorder.start()
    isRecording.value = true
  } catch (err) {
    console.error('Failed to start recording:', err)
  }
}

const stopRecording = () => {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    isRecording.value = false
  }
}

const sendVoiceMessage = async (audioBlob) => {
  if (!conversationId.value) return
  
  messages.value.push({ role: 'user', content: '🎤 Voice message', time: new Date().toLocaleTimeString() })
  isLoading.value = true
  scrollToBottom()
  
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.webm')
    
    const res = await axios.post(`${API_BASE}/conversations/${conversationId.value}/voice-message`, formData)
    const aiMessage = { role: 'ai', content: res.data.ai_response, time: new Date().toLocaleTimeString() }
    messages.value.push(aiMessage)
  } catch (err) {
    console.error('Failed to send voice message:', err)
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>
