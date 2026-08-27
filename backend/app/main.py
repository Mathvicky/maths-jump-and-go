from fastapi import FastAPI

app = FastAPI(
    title="Math's Jump & Go API",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "Math's Jump & Go API",
        "status": "running",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
