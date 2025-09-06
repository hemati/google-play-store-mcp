# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Ensure Python outputs are unbuffered
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy project metadata and source
COPY pyproject.toml ./
COPY src ./src
COPY scripts/render_entrypoint.sh ./render-entrypoint.sh

# Install dependencies
RUN pip install --no-cache-dir .

# Expose the default MCP HTTP port
EXPOSE 8000

# Start the MCP server
ENTRYPOINT ["./render-entrypoint.sh"]
CMD ["python", "-m", "googleplay_mcp.server"]
