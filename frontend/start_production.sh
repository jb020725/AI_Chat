#!/bin/bash

# Production Startup Script for AI Chatbot Frontend

echo "🚀 Starting AI Chatbot Frontend Production Build"
echo "=================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js and npm are available"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Build the production version
echo "🔨 Building production version..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi
echo "✅ Production build completed"

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Build directory 'dist' not found"
    exit 1
fi

echo ""
echo "🌐 Production build is ready!"
echo "📁 Build output: ./dist"
echo ""
echo "🚀 NEW INTEGRATION METHOD (No .env files needed!):"
echo "   ✅ Development: Uses Vite proxy to backend (localhost:8000)"
echo "   ✅ Production: Uses same domain (relative URLs)"
echo "   ✅ Automatic: No configuration needed"
echo ""
echo "To serve the production build:"
echo "1. Use a web server like nginx, Apache, or serve"
echo "2. Or run: npx serve -s dist -l 3000"
echo ""
echo "🔗 Integration Details:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend: http://localhost:8000"
echo "   - Proxy: Automatically routes /api calls to backend"
echo "   - No .env files needed in frontend"
echo ""
echo "The backend should be running on port 8000"
echo "Frontend will automatically connect via proxy in development"
echo "and same-domain in production!"
