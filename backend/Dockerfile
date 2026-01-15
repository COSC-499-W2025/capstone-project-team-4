# Use official Python image
FROM python:3.11.0-slim

# Install system dependencies for python-magic and git
RUN apt-get update && apt-get install -y \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

# Copy only dependency list first (for caching)
COPY requirements.txt .

# Install dependencies directly (no venv needed in Docker)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Configure Git to trust the /app directory (fixes CI/CD ownership issues)
RUN git config --global --add safe.directory /app && \
    git config --global --add safe.directory '*' && \
    git config --global init.defaultBranch main

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
