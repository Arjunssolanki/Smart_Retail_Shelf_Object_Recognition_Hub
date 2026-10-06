# Use an optimized, official slim Python environment runtime
FROM python:3.12-slim

# Prevent Python from writing pyc files to disk and ensure direct log streaming
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establish the working directory footprint inside the container instance
WORKDIR /workspace

# Install system-level dependencies required for database networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy over package dependency structures first to leverage caching
COPY requirements.txt .

# Install isolated framework dependencies natively inside the environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy all remaining architecture code layers into the operational workspace
COPY . .

# Expose Streamlit's official web server port boundary
EXPOSE 8501

# Health check rule to guarantee the interface pipeline remains active
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Master execution instruction launching your web portal dashboard engine
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
