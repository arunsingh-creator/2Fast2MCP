FROM python:3.12-slim

WORKDIR /app

COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp-server/ ./mcp-server/
COPY workflows/ ./workflows/
COPY dashboard/ ./dashboard/

WORKDIR /app/mcp-server

EXPOSE 8080

# Run REST API + Dashboard server
CMD ["python", "server.py", "api"]
