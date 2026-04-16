"""Minimal FastAPI app for scan execution and latest-scan retrieval."""

from fastapi import FastAPI

from backend.api.routes.scans import router as scans_router


app = FastAPI(
    title="Options Trading App Backend",
    version="0.1.0",
    description=(
        "Minimal backend skeleton for running options scans and retrieving "
        "the most recent canonical ScanResult."
    ),
)

app.include_router(scans_router)


def create_app() -> FastAPI:
    """Application factory for tests and local development."""
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
