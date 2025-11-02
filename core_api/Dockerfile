FROM python:3.11-slim
WORKDIR /app
COPY core_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY core_api /app/core_api
ENV PYTHONPATH=/app
CMD ["uvicorn", "core_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
