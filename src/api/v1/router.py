# src/api/v1/router.py
from fastapi import APIRouter
from src.api.v1.endpoints import generate, health, stats, frameworks

router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(generate.router, tags=["Generation"])
router.include_router(stats.router, tags=["Stats"])
router.include_router(frameworks.router, tags=["Frameworks"])