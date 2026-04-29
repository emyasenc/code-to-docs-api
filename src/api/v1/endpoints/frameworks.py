from fastapi import APIRouter, Depends
from src.api.dependencies import verify_api_key, rate_limit_dep

router = APIRouter()

@router.get("/frameworks")
async def get_frameworks(
    api_key: str = Depends(verify_api_key),
    _: str = Depends(rate_limit_dep)
):
    return {"frameworks": ["python", "fastapi", "django", "flask", "javascript", "react", "nextjs"]}