from fastapi import APIRouter

router = APIRouter()

@router.get("/stats")
async def get_stats():
    """Get API usage statistics"""
    return {
        "total_requests": 0,
        "total_tokens_generated": 0,
        "uptime": "99.9%"
    }