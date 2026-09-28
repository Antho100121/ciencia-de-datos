FROM python:3.12-slim

WORKDIR /usfq

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "ingestion/ingest.py"]