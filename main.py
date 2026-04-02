import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import asteroid_router, approach_router, threat_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asteroid_router, prefix="/api/v1")
app.include_router(approach_router, prefix="/api/v1")
app.include_router(threat_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Asteroid Watch API",
        "docs": "/docs",
        "endpoints": {
            "asteroids": "/api/v1/asteroids",
            "approaches": "/api/v1/approaches",
            "threats": "/api/v1/threats"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
