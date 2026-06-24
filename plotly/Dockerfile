FROM python:3.14.4-slim-trixie

EXPOSE 8050

WORKDIR /app
COPY queues.py . 
COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python", "queues.py"]