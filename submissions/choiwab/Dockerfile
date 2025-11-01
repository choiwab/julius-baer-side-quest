# Modern Banking Client - Dockerfile
# Multi-stage build for optimal image size

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY banking_client.py .
COPY config.py .
COPY cli.py .

# Make CLI executable
RUN chmod +x cli.py

# Add .local/bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV BANKING_API_URL=http://host.docker.internal:8123

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('${BANKING_API_URL}/accounts/validate/ACC1000')" || exit 1

# Default command shows help
CMD ["python", "cli.py", "--help"]

# Examples:
# Build: docker build -t banking-client .
# Run transfer: docker run banking-client python cli.py transfer --from ACC1000 --to ACC1001 --amount 100
# Interactive: docker run -it banking-client python banking_client.py
