# Mecenai MCP server (stdio) — used by MCP directories (e.g. Glama) to start the server and list its tools.
# The web concierge runs separately (see render.yaml).
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY mcp_server.py .
CMD ["python", "mcp_server.py"]
