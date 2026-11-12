FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY migration-up.py .
ENTRYPOINT ["python", "migration-up.py"]
CMD ["up"]
