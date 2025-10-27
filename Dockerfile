# Use official Python image
FROM python:3.14.0-slim

# Install system dependencies for python-magic
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy only dependency list first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a virtual environment inside the container
RUN python -m venv /venv

# Activate the virtual environment
ENV PATH="/venv/bin:$PATH"

# Copy the rest of the project
COPY . .

#Added this line to ensure src is recognized as a module
ENV PYTHONPATH="/app"

# Run your app
CMD ["python", "src/main.py"]
