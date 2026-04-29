# src/main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.config import get_settings
from src.api.v1.router import router as v1_router
from src.core.exceptions import CodeToDocsError, RateLimitExceeded

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

@app.exception_handler(CodeToDocsError)
async def code_to_docs_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "message": str(exc)}
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "RATE_LIMIT_EXCEEDED", "message": str(exc)}
    )

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.VERSION}