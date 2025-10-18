# Multi-stage Dockerfile for Claude Agent SDK - Agent 7 POC
# Includes Python 3.11 + Node.js 18+ + Claude Code CLI

FROM python:3.11-slim

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify installations
RUN node --version && npm --version && python --version

# Install Claude Code CLI globally (CRITICAL for SDK)
RUN npm install -g @anthropic-ai/claude-code

# Verify Claude CLI installation
RUN which claude && claude --version

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Copy agents directory (contains Agent 7)
COPY agents/ ./agents/
# Copy template directory (contains utils like env_loader)
COPY template/ ./template/
# Copy API wrapper
COPY deployment/api.py .
# Copy .env.example for reference
COPY .env.example .

# Create results directory for any output
RUN mkdir -p /app/results

# Expose port for FastAPI
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI server with uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
