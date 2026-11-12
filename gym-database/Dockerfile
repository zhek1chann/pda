FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY migrations ./migrations
COPY scripts ./scripts
ENTRYPOINT ["python", "scripts/migrate.py"]
CMD ["up"]
