FROM python:3.11-slim

#FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create memory directory with proper permissions
RUN mkdir -p /app/closer_memory_db && chmod 777 /app/closer_memory_db

# Set environment variables
ENV DOCKER_ENV=true
ENV MCP_TRANSPORT=sse
ENV PYTHONUNBUFFERED=1

# Expose SSE port
EXPOSE 8000

# Run the server with SSE transport
CMD ["python3", "server.py", "--sse"]