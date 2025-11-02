FROM python:3.11-slim
WORKDIR /app
COPY tg_bot/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY tg_bot /app/tg_bot
ENV PYTHONPATH=/app
CMD ["python", "-m", "tg_bot.main"]
