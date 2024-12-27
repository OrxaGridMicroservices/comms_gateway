FROM python:3.9-slim

# Set environment variables to avoid prompts
ENV PYTHONUNBUFFERED=1 \
    PDS_INTERVAL=60 \
    ADS_INTERVAL=10 \
    MQTT_BROKER=localhost \
    MQTT_PORT=1883

WORKDIR /app

# Copy the entire application code
COPY . .

# Copy requirements.txt first to leverage Docker caching
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the default MQTT port
EXPOSE 1883

# Command to run the script
CMD ["python", "main.py"]