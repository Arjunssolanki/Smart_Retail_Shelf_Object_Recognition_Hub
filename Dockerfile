# Use the official lightweight Python runtime baseline image
FROM python:3.11-slim

# Prevent Python from writing pycache files and buffer outputs to keep logs clean
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the active working directory container pathway
WORKDIR /app

# Install system dependencies needed for compiling native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency tracker file into the application cache layer
COPY requirements.txt .

# Install all isolated architectural python frameworks at once
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire local project directory tree into the app folder container workspace
COPY . .

# Expose port 8501 to allow incoming web browser traffic to reach Streamlit
EXPOSE 8501

# Run the system entrypoint command to launch the web dashboard interface hub
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
