#!/bin/bash
# Start Industrial Electrical RCA API Server

# Create virtual environment if it doesn't exist
if [ ! -d "../.venv" ]; then
    echo "Creating virtual environment in project root..."
    python3 -m venv ../.venv
fi

# Activate virtual environment
if [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
elif [ -f "../.venv/Scripts/activate" ]; then
    source ../.venv/Scripts/activate
fi

# Set environment variables
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"

echo "Starting Industrial Electrical Agentic RCA Server on port 8001..."
uvicorn app:app --reload --host 0.0.0.0 --port 8001