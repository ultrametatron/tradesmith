FROM python:3.11-slim

# Install certificates (needed by requests/HTTPs)
RUN apt-get update && apt-get install -y ca-certificates

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all code, including our entrypoint script
COPY . .

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

# Entrypoint will dispatch to the correct script based on service name
CMD ["./entrypoint.sh"]
