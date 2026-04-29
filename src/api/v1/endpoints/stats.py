from fastapi import APIRouter, Depends
from src.api.dependencies import verify_api_key, rate_limit_dep

router = APIRouter()

@router.get("/stats")
async def get_stats(
    api_key: str = Depends(verify_api_key),
    _: str = Depends(rate_limit_dep)
):
    return {"total_requests": 0, "total_tokens_generated": 0, "uptime": "99.9%"}