FROM python:3.11-slim
RUN apt-get update && apt-get install -y ca-certificates
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
CMD ["python","run_intraday.py"]
