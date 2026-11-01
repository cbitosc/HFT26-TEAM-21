"""API routes package — registers all route modules under /api."""

from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.colleges import router as colleges_router
from app.api.routes.requests import router as requests_router
from app.api.routes.admin import router as admin_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.assessment import router as assessment_router
from app.api.routes.college import router as college_router
from app.api.routes.recruiter import router as recruiter_router

api_router = APIRouter()

# System / health
api_router.include_router(health_router, prefix="", tags=["System"])

# Authentication & profile
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Public colleges listing
api_router.include_router(colleges_router, prefix="/colleges", tags=["Colleges"])

# Verification requests (pending users submit their requests here)
api_router.include_router(requests_router, prefix="/requests", tags=["Verification Requests"])

# Platform admin operations
api_router.include_router(admin_router, prefix="/admin", tags=["Platform Admin"])

# Student portfolio upload, review & confirmation (Module 3)
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio"])

# Assessment Agent, Question Bank & Student Workspace (Modules 4, 5, 6)
api_router.include_router(assessment_router, prefix="/assessment", tags=["Assessment"])

# College Task Management (Module 11)
api_router.include_router(college_router, prefix="/college", tags=["College"])

# Recruiter Portal & Live Coding Interviews (Module 12)
api_router.include_router(recruiter_router, prefix="/recruiter", tags=["Recruiter"])
