#!/bin/bash

# Railway Deployment Script for VoiceAI Support

echo "🚀 Deploying VoiceAI Support to Railway..."

# Login to Railway (interactive)
echo "Please login to Railway..."
railway login

# Navigate to project directory
cd voice-ai-support || exit 1

# Link to project
echo "Linking to project..."
railway link --project automation8

# Set environment variables
echo "Setting environment variables..."
railway variable set GROQ_API_KEY
railway variable set MONGODB_URL
railway variable set DATABASE_NAME=voice_ai_support
railway variable set LLM_PROVIDER=groq

# Deploy
echo "Deploying..."
railway up

echo "✅ Deployment complete!"
railway domain
