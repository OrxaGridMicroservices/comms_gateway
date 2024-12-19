FROM python:3.9-slim

WORKDIR /app

COPY main.py config.json ./

RUN pip install paho-mqtt

CMD ["python", "main.py"]