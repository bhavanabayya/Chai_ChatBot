# ───────────── FRONTEND (React/Vite) BUILD ─────────────
FROM node:20-alpine AS fe_builder
WORKDIR /app/frontend

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy rest of frontend source and build
COPY frontend ./
RUN npm run build

# ───────────── BACKEND (FastAPI) ─────────────
FROM python:3.10-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend ./backend

# Copy built frontend into image (so FastAPI can serve it)
COPY --from=fe_builder /app/frontend/dist /app/frontend/dist

# Expose port for Azure App Service
ENV PORT=8000
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
