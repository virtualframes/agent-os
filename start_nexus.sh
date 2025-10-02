#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to kill all background jobs on exit
cleanup() {
    echo "Shutting down services..."
    # Kill all child processes of this script
    pkill -P $$
}

trap cleanup EXIT

# --- Environment Variable Checks ---
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY environment variable is not set."
    echo "Please set it before running the script, for example:"
    echo "export ANTHROPIC_API_KEY='your-anthropic-api-key'"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Warning: GITHUB_TOKEN environment variable is not set."
    echo "GitHub integration will not work. You can set a placeholder:"
    echo "export GITHUB_TOKEN='your-github-token'"
fi


# --- Gateway Service ---
echo "Starting Gateway service..."
(
  cd gateway
  # Check if node_modules exists, if not run npm install
  if [ ! -d "node_modules" ]; then
    echo "node_modules not found in gateway, running npm install..."
    npm install
  fi
  # Use the dev script from package.json
  npm run dev
) &


# --- Python Backend ---

# Install Python dependencies
echo "Installing Python dependencies from requirements.txt..."
pip install --quiet -r requirements.txt

# Start MCP router
echo "Starting MCP Router service..."
uvicorn terminal_nexus.mcp.main:app --reload --port 8090 &

# Start all microservices
echo "Starting microservices..."
uvicorn services.synthesize.main:app --reload --port 8017 &
uvicorn services.priority.main:app --reload --port 8015 &
uvicorn services.scan.main:app --reload --port 8021 &
uvicorn services.rank.main:app --reload --port 8013 &


# Wait for services to start up
echo "Waiting for services to initialize..."
sleep 5 # Allow time for servers to start before launching UI

# --- Launch Terminal UI ---
echo "Launching Nexus Terminal..."
python -m terminal_nexus.main

echo "Nexus Terminal exited."