FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 && rm -rf /var/lib/apt/lists/*
COPY vision_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY vision_service /app/vision_service
ENV PYTHONPATH=/app
CMD ["uvicorn", "vision_service.app:app", "--host", "0.0.0.0", "--port", "8001"]
