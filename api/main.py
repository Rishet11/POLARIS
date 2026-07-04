import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import reconciliation, collections, portfolio, system

app = FastAPI(title="POLARIS Back Office API")

# Parse FRONTEND_ORIGIN from env, default to http://localhost:3000
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
allow_origins = [origin.strip() for origin in frontend_origin.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(reconciliation.router)
app.include_router(collections.router)
app.include_router(portfolio.router)
app.include_router(system.router)
