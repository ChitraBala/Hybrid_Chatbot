FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ANONYMIZED_TELEMETRY=False

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# Compatibility constraints for the supplied 2024-era Chroma/OpenAI versions.
RUN pip install --no-cache-dir -r requirements.txt "numpy==1.26.4" "httpx==0.27.2" \
    && pip check

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/chroma_db /app/.streamlit \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser app.py backend.py spotify_web_app_architecture.pdf ./
COPY --chown=appuser:appuser .streamlit/config.toml ./.streamlit/config.toml

USER appuser
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)" || exit 1

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
