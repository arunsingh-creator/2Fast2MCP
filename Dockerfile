FROM python:3.12-slim

WORKDIR /app

COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp-server/ ./mcp-server/
COPY workflows/ ./workflows/

WORKDIR /app/mcp-server

EXPOSE 8080

# Default: run as MCP server (stdio transport)
# Override with CMD ["python", "server.py", "api"] to run REST API
CMD ["python", "server.py"]
