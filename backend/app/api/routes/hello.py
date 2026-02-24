from fastapi import APIRouter

from app.schemas.hello import HelloResponse

router = APIRouter(prefix="/hello", tags=["hello"])


@router.get("/", response_model=HelloResponse)
async def hello() -> HelloResponse:
    return HelloResponse(message="Hello, World!")
