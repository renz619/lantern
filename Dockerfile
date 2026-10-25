# Builds the website, then serves it and the API from one Python server.

FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Use the real backend on the same address (not mock data, not localhost).
ENV VITE_USE_MOCKS=false VITE_API_URL=
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
# Member A's Gemini, search and diff code; the backend imports it from here.
COPY ai/ ai/
# main.py looks for frontend/dist next to backend/
COPY --from=frontend /frontend/dist frontend/dist

WORKDIR /app/backend
# Render sets PORT; 8000 is the fallback for running the image locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
