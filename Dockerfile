FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (optional but safe)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY requirements.txt .

# Install with increased timeout and retry
RUN pip install --no-cache-dir --default-timeout=100 --retries=5 \
    -i https://pypi.org/simple \
    -r requirements.txt

# Copy all code folders
COPY backend ./backend
COPY scripts ./scripts
# COPY tests ./tests  # Uncomment if needed

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]