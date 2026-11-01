from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import api_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Portfolio-Driven Adaptive Coding & Technical Assessment Platform API",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS) for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Mount API routes under /api
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint providing basic API information and navigation links.
    """
    return {
        "name": settings.app_name,
        "tagline": "Portfolio-Driven Adaptive Coding & Technical Assessment Platform",
        "version": settings.version,
        "status": "online",
        "health_check": f"{settings.api_prefix}/health",
        "documentation": "/docs",
        "message": "Welcome to the SkillProof AI API Foundation."
    }
