# Psybot API image for Google Cloud Run.
#
# Build:
#     gcloud builds submit --tag europe-west1-docker.pkg.dev/$PROJECT/psybot/api:$SHA .
#
# Deploy:
#     gcloud run deploy psybot-api \
#       --image europe-west1-docker.pkg.dev/$PROJECT/psybot/api:$SHA \
#       --region europe-west1 \
#       --platform managed \
#       --allow-unauthenticated \
#       --memory 512Mi \
#       --cpu 1 \
# --min-instances 0 \
# --max-instances 3 \
# --concurrency 10 \
# --timeout 30 \
# --set-env-vars "PSYBOT_KNOWLEDGE_DIR=/app/knowledge,PSYBOT_MAX_ITERS=3,PSYBOT_TEMPERATURE=0.4,PSYBOT_MAX_TOKENS=700,DEEPSEEK_MODEL=deepseek-chat,DEEPSEEK_API_URL=https://api.deepseek.com/v1" \
# --set-secrets "DEEPSEEK_API_KEY=DEEPSEEK_API_KEY:latest"
#
# CORS for production: extend _ALLOWED_ORIGINS in bobot.py to include
# https://emiliepommier.fr (and https://www.emiliepommier.fr) before going live.
# Currently it allows localhost:4200/8000 for the Angular dev server.

# ----------------------------------------------------------------------
# Stage 1: builder - install Python deps into a venv we can copy.
# ----------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Disable .pyc writes, force unbuffered stdout/stderr (Cloud Run logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Install deps first (better layer cache).
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------
# Stage 2: runtime - slim image, non-root user, knowledge baked in.
# ----------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Cloud Run injects PORT=8080. The bobot.py default is 8000 but PORT
    # overrides it at startup. Exposing it as ENV avoids surprises in uvicorn.
    PORT=8080

# Create a non-root user to run the app (Cloud Run best practice).
RUN groupadd --system --gid 10001 psybot \
    && useradd  --system --uid 10001 --gid psybot --home-dir /app --shell /sbin/nologin psybot

WORKDIR /app

# Copy the prebuilt venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Copy the application code + the RAG knowledge corpus.
# bobot.py imports "rag" and "llm" by name (not "from .rag"), so the cwd
# must contain both modules. --chown keeps the image small and ownership sane.
COPY --chown=psybot:psybot bobot.py llm.py rag.py ./
COPY --chown=psybot:psybot knowledge/ ./knowledge/

USER psybot

# Cloud Run probes / on TCP; it does NOT touch an HTTP path by default.
# The FastAPI app exposes /api/health/psybot. We expose 8080 (Cloud Run default).
EXPOSE 8080

# Use uvicorn directly so we can pin the host and workers. 1 worker is
# fine for the psybot workload (RAG is in-process and small).
CMD ["uvicorn", "bobot:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--log-level", "info", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]