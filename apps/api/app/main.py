from fastapi import FastAPI

app = FastAPI(
    title="DataTrust API",
    description="API for data quality validation.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Report whether the API process is responding,
    """
    return {"status": "ok"}
