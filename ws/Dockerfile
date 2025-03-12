# Use Python base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy server files
COPY ws/server.py .

# Install dependencies
RUN pip install fastapi uvicorn websockets

# Expose the WebSocket port
EXPOSE 8000

# Command to run the WebSocket server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]