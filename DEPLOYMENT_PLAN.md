# VoiceAI Deployment Plan - Vercel Backend

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VERCEL DEPLOYMENT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  FRONTEND (Vercel)                         │   │
│  │                 frontend-react/                              │   │
│  │              voiceai-frontend.vercel.app                     │   │
│  └────────────────────────────┬────────────────────────────────┘   │
│                               │ HTTPS                               │
│                               ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  BACKEND API (Vercel)                        │   │
│  │                    api/ folder                                │   │
│  │              api.voiceai.vercel.app                          │   │
│  └──────────┬──────────────────┬───────────────────────────────┘   │
│             │                  │                                      │
│             ▼                  ▼                                      │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │   MongoDB Atlas  │  │   Groq/OpenAI    │                    │
│  │   (Database)     │  │   (LLM API)      │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Get Required API Keys

### 1.1 Groq API (Free - Recommended)
1. Go to https://console.groq.com/keys
2. Sign up/Login
3. Create API Key (free tier: 30 requests/minute)
4. **Model: llama-3.1-8b-instant (fast, free)**

### 1.2 OpenAI (Paid - Alternative)
1. Go to https://platform.openai.com/api-keys
2. Create API Key
3. **Model: gpt-3.5-turbo or gpt-4**

### 1.3 Your MongoDB Atlas (Already configured)
- Cluster: `atlas-aero-river.dyp83ag.mongodb.net`
- Database: `voice_ai_support`

---

## Step 2: Deploy Backend to Vercel

### 2.1 Create Vercel Project

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
cd voice-ai-support
vercel
```

### 2.2 Configure Environment Variables

In Vercel Dashboard → Your Project → Settings → Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `MONGODB_URL` | `mongodb+srv://Vercel-Admin-atlas-aero-river:Titankalimot08%21@atlas-aero-river.dyp83ag.mongodb.net/?appName=atlas-aero-river` | Your MongoDB Atlas URL |
| `DATABASE_NAME` | `voice_ai_support` | Database name |
| `LLM_PROVIDER` | `groq` | LLM provider |
| `GROQ_API_KEY` | `gsk_xxxxxxxx` | Your Groq API key |
| `REDIS_URL` | (optional) | Upstash Redis URL |

### 2.3 Deploy Command

```bash
vercel --prod
```

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Update API URL

In `frontend-react/src/App.jsx`, update the API base URL:

```javascript
const API_BASE = 'https://api.voiceai.vercel.app'
```

### 3.2 Deploy Frontend

```bash
cd frontend-react
vercel --prod
```

Or use Vercel Dashboard:
1. Import from GitHub
2. Set environment variable: `VITE_API_URL=https://api.yourproject.vercel.app`

---

## Step 4: Configure Custom Domain (Optional)

### 4.1 Backend Domain
1. Vercel Dashboard → Backend Project → Settings → Domains
2. Add: `api.yourdomain.com`
3. Update DNS records

### 4.2 Frontend Domain
1. Vercel Dashboard → Frontend Project → Settings → Domains
2. Add: `yourdomain.com` or `app.yourdomain.com`

---

## Step 5: Update MongoDB Atlas Network Access

In MongoDB Atlas:
1. Go to Security → Network Access
2. Add IP Whitelist:
   - `0.0.0.0/0` (Allow all - for development)
   - Or add Vercel's IP ranges for production

---

## Deployment Commands

```bash
# 1. Clone/Push code to GitHub
git add .
git commit -m "VoiceAI Vercel deployment ready"
git push origin main

# 2. Deploy Backend
cd voice-ai-support/api
vercel --prod

# 3. Deploy Frontend
cd ../frontend-react
vercel --prod

# 4. Or use Vercel Dashboard
# Import repo → Select framework → Configure env vars → Deploy
```

---

## Environment Variables Reference

### Backend (.env)
```env
# MongoDB Atlas (Your existing)
MONGODB_URL=mongodb+srv://Vercel-Admin-atlas-aero-river:Titankalimot08%21@atlas-aero-river.dyp83ag.mongodb.net/?appName=atlas-aero-river
DATABASE_NAME=voice_ai_support

# LLM Provider
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here

# Alternative: OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk_your_key_here

# Cache (Optional - Upstash Redis)
REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
```

### Frontend (.env.production)
```env
VITE_API_URL=https://api.voiceai.vercel.app
```

---

## API Endpoints

After deployment, your API will be available at:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API health check |
| `/health` | GET | Detailed health status |
| `/conversations` | POST | Create new conversation |
| `/conversations/{id}` | GET | Get conversation |
| `/conversations/{id}/text-message` | POST | Send text message |
| `/conversations/{id}/voice-message` | POST | Send voice message |

---

## File Structure

```
voice-ai-support/
├── api/
│   ├── __init__.py          # Package init
│   ├── index.py              # Main Flask app (Vercel handler)
│   ├── database.py           # MongoDB connection
│   ├── cache.py              # Redis/Upstash cache
│   ├── llm.py                # LLM integration (Groq/OpenAI)
│   └── requirements.txt      # Python dependencies
├── vercel.json              # Vercel configuration
├── frontend-react/           # React frontend
│   ├── src/App.jsx
│   └── vite.config.js
├── frontend-vue/            # Vue frontend
│   └── src/App.vue
├── Dockerfile               # Docker (optional)
└── docker-compose.yml       # Docker (optional)
```

---

## Cost Breakdown

| Service | Tier | Cost |
|---------|------|------|
| Vercel Frontend | Hobby (100GB bandwidth) | **Free** |
| Vercel Backend | Hobby (100GB bandwidth) | **Free** |
| Groq API | Free tier (30 req/min) | **Free** |
| MongoDB Atlas | M0 (512MB storage) | **Free** |
| Upstash Redis | Free (10K commands/day) | **Free** |

**Total: $0/month**

---

## Limitations & Considerations

### Vercel Hobby Limits
- 10-second timeout per request
- 100GB bandwidth/month
- No persistent processes

### For Production (Upgrade to Pro - $20/month)
- 60-second timeout per request
- Unlimited bandwidth
- Analytics & logs
- Priority support

### LLM Options for Production

| Provider | Model | Speed | Cost |
|----------|-------|-------|------|
| Groq | llama-3.1-8b-instant | Very Fast | Free tier |
| Groq | llama-3.1-70b-versatile | Fast | $0.59/1M tokens |
| OpenAI | gpt-3.5-turbo | Fast | $0.50/1M tokens |
| OpenAI | gpt-4 | Medium | $3/1M tokens |
| Anthropic | claude-3-haiku | Fast | $0.25/1M tokens |

---

## Troubleshooting

### CORS Errors
```python
# In api/index.py, CORS is configured in vercel.json
# Or add manually:
from flask_cors import CORS
CORS(app, origins=["https://your-frontend.vercel.app"])
```

### Timeout Errors
```python
# Increase timeout for LLM calls
response = httpx.post(url, timeout=60.0)
```

### MongoDB Connection Failed
1. Check IP whitelist in Atlas
2. Verify connection string format
3. Test locally with `MONGODB_URL=... python api/index.py`

### LLM Not Working
1. Verify API key is set correctly
2. Check Groq/OpenAI dashboard for usage
3. Test API key with curl:
```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

---

## Next Steps

1. [ ] Get Groq API Key from https://console.groq.com
2. [ ] Push code to GitHub
3. [ ] Create Vercel project
4. [ ] Add environment variables
5. [ ] Deploy backend
6. [ ] Deploy frontend
7. [ ] Test with https://your-frontend.vercel.app

---

## Support

- Vercel Docs: https://vercel.com/docs
- MongoDB Atlas: https://www.mongodb.com/docs/atlas/
- Groq: https://console.groq.com/docs
