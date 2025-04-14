# Use a base image with Python pre-installed
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install curl (needed to download Ollama) and git (sometimes needed for dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
# (Optional: If you have more dependencies, list them in requirements.txt)
# RUN pip install --no-cache-dir -r requirements.txt
# For this simple example, we only need 'requests'
RUN pip install --no-cache-dir requests

# Copy the Python script and entrypoint script into the container
COPY app.py .
COPY run.sh .

# Make the entrypoint script executable
RUN chmod +x run.sh

# Expose the default Ollama port (optional, but good practice if you ever want to connect from outside)
# EXPOSE 11434

# Set the entrypoint script to run when the container starts
ENTRYPOINT ["./run.sh"]
