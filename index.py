"""Vercel entrypoint for the Tender Intelligence FastAPI application.

Vercel serves files under ``api/`` beneath the ``/api`` URL prefix. The
existing application was designed with routes such as ``/health`` and
``/auth/...``. This adapter removes the Vercel ``/api`` prefix before
forwarding requests, so existing backend routes remain unchanged.
"""

from __future__ import annotations

import os
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_SRC = os.path.join(ROOT, "backend", "src")
if BACKEND_SRC not in sys.path:
    sys.path.insert(0, BACKEND_SRC)

# Serverless functions must not rely on a long-running background worker or
# startup embedding warmup.
os.environ.setdefault("ENABLE_DOCUMENT_WORKER", "false")
os.environ.setdefault("WARM_EMBEDDINGS_ON_STARTUP", "false")

from tender_intel.api.app import app as _application  # noqa: E402


class StripVercelApiPrefix:
    """Forward /api/* requests to the existing FastAPI routes as /*."""

    def __init__(self, application: Any) -> None:
        self.application = application

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> Any:
        if scope["type"] in {"http", "websocket"}:
            path = scope.get("path", "")
            if path == "/api" or path.startswith("/api/"):
                scope = dict(scope)
                scope["path"] = path[4:] or "/"

                raw_path = scope.get("raw_path")
                if raw_path:
                    raw = bytes(raw_path)
                    if raw == b"/api" or raw.startswith(b"/api/"):
                        scope["raw_path"] = raw[4:] or b"/"

                scope["root_path"] = "/api"

        return await self.application(scope, receive, send)


app = StripVercelApiPrefix(_application)
