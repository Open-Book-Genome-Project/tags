#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# You can change the model name here if you want to use a different one
# Make sure the model name here matches the one used in app.py
OLLAMA_MODEL="llama2"
# -------------------

echo "Starting Ollama server in the background..."
# Start ollama serve in the background
ollama serve &
# Get the process ID of the ollama server
pid=$!

echo "Waiting for Ollama server to be ready..."
# Wait for a few seconds to give the server time to start
# A more robust check would be to poll the API endpoint, but sleep is simpler for this example
sleep 10

# Check if the server is running by trying to list local models
if ! ollama list > /dev/null 2>&1; then
    echo "Error: Ollama server failed to start."
    # Optionally try to kill the process if it's somehow stuck
    kill $pid > /dev/null 2>&1 || true
    exit 1
fi
echo "Ollama server started."

echo "Pulling model '$OLLAMA_MODEL' (this might take a while if not cached)..."
ollama pull "$OLLAMA_MODEL"
echo "Model '$OLLAMA_MODEL' is ready."

echo "Running Python application (app.py)..."
# Run the Python script
python app.py

echo "Python script finished."

echo "Stopping Ollama server..."
# Stop the Ollama server gracefully
kill $pid
# Wait for the process to terminate
wait $pid
echo "Ollama server stopped. Exiting container."

exit 0
