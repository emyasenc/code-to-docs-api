from fastapi import APIRouter

router = APIRouter()

@router.get("/frameworks")
async def get_frameworks():
    """Get list of supported frameworks"""
    return {
        "frameworks": [
            "python",
            "fastapi",
            "django",
            "flask",
            "javascript",
            "react",
            "nextjs"
        ]
    }