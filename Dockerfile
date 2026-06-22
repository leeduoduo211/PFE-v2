# syntax=docker/dockerfile:1

# ── Stage 1: build the React SPA ─────────────────────────────────────────
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python API serving the SPA ──────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install the package with the API extra. ui.utils.{converters,registry,t0_mtm}
# are imported by the API but are Streamlit-free, so streamlit is not needed.
COPY pyproject.toml README.md ./
COPY pfev2/ ./pfev2/
COPY ui/ ./ui/
COPY api/ ./api/
RUN pip install --no-cache-dir -e ".[api]"

# Built SPA from stage 1, served by FastAPI at "/".
COPY --from=frontend /build/dist ./frontend/dist

ENV PFEV2_STATIC_DIR=/app/frontend/dist \
    PFEV2_DB_PATH=/data/runs.db
RUN mkdir -p /data
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
