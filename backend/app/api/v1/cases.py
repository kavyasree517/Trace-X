"""Case API endpoints stub."""

from fastapi import APIRouter

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("")
async def list_cases_stub() -> dict[str, str]:
    return {"message": "Case management initialized. Submit queries via POST /cases."}
