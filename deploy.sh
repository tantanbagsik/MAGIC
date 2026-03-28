#!/bin/bash

# VoiceAI Deployment Script
# Usage: ./deploy.sh [option]

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}   VoiceAI Deployment Script${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

show_help() {
    echo "Usage: ./deploy.sh [option]"
    echo ""
    echo "Options:"
    echo "  docker      - Deploy using Docker"
    echo "  railway     - Deploy to Railway"
    echo "  render      - Deploy to Render"
    echo "  local       - Run locally with uvicorn"
    echo "  build       - Build Docker image"
    echo "  test        - Test the API"
    echo "  help        - Show this help message"
}

deploy_docker() {
    echo -e "${YELLOW}Deploying with Docker...${NC}"
    docker-compose up -d --build
    echo -e "${GREEN}Deployed! Access at http://localhost:8000${NC}"
}

deploy_railway() {
    echo -e "${YELLOW}Deploying to Railway...${NC}"
    npm install -g @railway/cli
    railway login
    railway init
    railway up
    echo -e "${GREEN}Deployed to Railway!${NC}"
}

deploy_render() {
    echo -e "${YELLOW}Deploying to Render...${NC}"
    render deploy
    echo -e "${GREEN}Deployed to Render!${NC}"
}

run_local() {
    echo -e "${YELLOW}Starting local server...${NC}"
    pip install -r requirements.txt
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

build_docker() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t voiceai-backend .
    echo -e "${GREEN}Built successfully!${NC}"
}

test_api() {
    echo -e "${YELLOW}Testing API...${NC}"
    echo ""
    echo "1. Testing health endpoint..."
    curl -s http://localhost:8000/health | python -m json.tool
    echo ""
    echo "2. Creating conversation..."
    CONV_ID=$(curl -s -X POST http://localhost:8000/conversations | python -c "import sys,json; print(json.load(sys.stdin)['conversation_id'])")
    echo "   Conversation ID: $CONV_ID"
    echo ""
    echo "3. Testing text message..."
    curl -s -X POST "http://localhost:8000/conversations/$CONV_ID/text-message" \
        -H "Content-Type: application/json" \
        -d '{"message":"Hello!"}' | python -m json.tool
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
}

# Main
case "${1:-help}" in
    docker)
        deploy_docker
        ;;
    railway)
        deploy_railway
        ;;
    render)
        deploy_render
        ;;
    local)
        run_local
        ;;
    build)
        build_docker
        ;;
    test)
        test_api
        ;;
    help|*)
        show_help
        ;;
esac
