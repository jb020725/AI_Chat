FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for ML packages
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run uses 8080)
EXPOSE 8080

# Run the application (use PORT environment variable)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
