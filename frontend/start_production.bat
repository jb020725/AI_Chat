@echo off
REM Production Startup Script for AI Chatbot Frontend (Windows)

echo 🚀 Starting AI Chatbot Frontend Production Build
echo ==================================================

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed. Please install npm first.
    pause
    exit /b 1
)

echo ✅ Node.js and npm are available

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ Dependencies already installed
)

REM Build the production version
echo 🔨 Building production version...
npm run build
if %errorlevel% neq 0 (
    echo ❌ Build failed
    pause
    exit /b 1
)
echo ✅ Production build completed

REM Check if build was successful
if not exist "dist" (
    echo ❌ Build directory 'dist' not found
    pause
    exit /b 1
)

echo.
echo 🌐 Production build is ready!
echo 📁 Build output: ./dist
echo.
echo 🚀 NEW INTEGRATION METHOD (No .env files needed!):
echo    ✅ Development: Uses Vite proxy to backend (localhost:8000)
echo    ✅ Production: Uses same domain (relative URLs)
echo    ✅ Automatic: No configuration needed
echo.
echo To serve the production build:
echo 1. Use a web server like nginx, Apache, or serve
echo 2. Or run: npx serve -s dist -l 3000
echo.
echo 🔗 Integration Details:
echo    - Frontend: http://localhost:3000
echo    - Backend: http://localhost:8000
echo    - Proxy: Automatically routes /api calls to backend
echo    - No .env files needed in frontend
echo.
echo The backend should be running on port 8000
echo Frontend will automatically connect via proxy in development
echo and same-domain in production!
echo.
pause
