"""
FastAPI application factory for Intelligent Cloud Observability Platform.
"""

from fastapi import FastAPI

from icop.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Intelligent Cloud Observability Platform API",
        description="AI-Powered Cloud Observability, OpenTelemetry Collector & Reliability Agent",
        version="1.0.0",
    )
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
