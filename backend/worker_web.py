"""Celery worker wrapped in a minimal HTTP server.

Render's free tier only runs Web Services (not Background Workers).
This shim satisfies Render's HTTP health check while running the Celery
worker in a subprocess.
"""
import os
import subprocess
import sys
import threading

import uvicorn
from fastapi import FastAPI

app = FastAPI(docs_url=None, redoc_url=None)


@app.get("/health")
def health():
    return {"status": "ok", "role": "worker"}


def _run_worker():
    subprocess.run(
        [
            sys.executable, "-m", "celery",
            "-A", "workers.celery_app:celery_app",
            "worker",
            "--loglevel=info",
            "--concurrency=1",
        ]
    )


if __name__ == "__main__":
    threading.Thread(target=_run_worker, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
