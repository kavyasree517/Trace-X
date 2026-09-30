"""Label lookup endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.core.security import canonicalize_address

router = APIRouter(prefix="/labels", tags=["Labels"])


class LabelLookupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str
    chain: str
    match_found: bool
    labels: list[dict[str, str]]
    message: str


@router.get("/{chain}/{address}", response_model=LabelLookupResponse)
async def lookup_address_label(chain: str, address: str) -> LabelLookupResponse:
    try:
        canonical_addr = canonicalize_address(address)
    except ValueError:
        return LabelLookupResponse(
            address=address,
            chain=chain,
            match_found=False,
            labels=[],
            message="Invalid address format",
        )

    return LabelLookupResponse(
        address=canonical_addr,
        chain=chain,
        match_found=False,
        labels=[],
        message="No match found in current references",
    )
