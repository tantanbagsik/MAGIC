#!/bin/bash

# VoiceAI Deployment Script
# Deploys Backend + Frontend to Vercel

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   VoiceAI Vercel Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for Vercel CLI
echo -e "${YELLOW}Step 1: Checking Vercel CLI...${NC}"
if command -v vercel &> /dev/null; then
    echo -e "${GREEN}✓ Vercel CLI installed${NC}"
else
    echo -e "${YELLOW}Installing Vercel CLI...${NC}"
    npm install -g vercel
fi
echo ""

# Check Node.js
echo -e "${YELLOW}Step 2: Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓ Node.js installed: $(node --version)${NC}"
else
    echo -e "${RED}✗ Node.js not found. Please install Node.js first.${NC}"
    exit 1
fi
echo ""

# Deploy Backend
echo -e "${YELLOW}Step 3: Deploying Backend API...${NC}"
echo ""
cd api
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install flask pymongo redis httpx python-dotenv
echo ""

echo -e "${YELLOW}Deploying to Vercel...${NC}"
vercel --prod --yes
cd ..
echo ""

# Get Backend URL
echo -e "${YELLOW}Step 4: Getting Backend URL...${NC}"
echo -e "${YELLOW}Please enter your Vercel Backend URL (e.g., https://api-xxxx.vercel.app):${NC}"
read -r BACKEND_URL
echo ""

# Update Frontend .env
echo -e "${YELLOW}Step 5: Updating Frontend API URL...${NC}"
echo "VITE_API_URL=$BACKEND_URL" > frontend-react/.env.production
echo "VITE_API_URL=$BACKEND_URL" > frontend-vue/.env.production
echo -e "${GREEN}✓ Frontend API URL updated${NC}"
echo ""

# Deploy React Frontend
echo -e "${YELLOW}Step 6: Deploying React Frontend...${NC}"
cd frontend-react
vercel --prod --yes
cd ..
echo ""

# Deploy Vue Frontend
echo -e "${YELLOW}Step 7: Deploying Vue Frontend...${NC}"
cd frontend-vue
vercel --prod --yes
cd ..
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Your URLs:${NC}"
echo -e "  Backend API: ${BACKEND_URL}"
echo -e "  (Check Vercel dashboard for frontend URLs)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set environment variables in Vercel dashboard:"
echo "   - MONGODB_URL"
echo "   - DATABASE_NAME=voice_ai_support"
echo "   - LLM_PROVIDER=groq"
echo "   - GROQ_API_KEY=your_key"
echo ""
echo "2. Get Groq API Key: https://console.groq.com/keys"
echo ""
