# Stage 1: Build frontend
FROM cgr.dev/chainguard/node:latest AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + static frontend
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# Install backend dependencies
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# Copy backend source
COPY backend/yado/ ./yado/

# Copy built frontend
COPY --from=frontend /app/frontend/build ./static/

# Data directory for SQLite
RUN mkdir -p /data
ENV DATABASE_URL=sqlite+aiosqlite:////data/yado.db

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "yado.main:app", "--host", "0.0.0.0", "--port", "8000"]
