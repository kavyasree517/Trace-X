"""Transaction schemas conforming to P6 data fields."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.enums import EvidenceTag, TransferKind


class TransactionItem(BaseModel):
    """P6 Edge representation retaining full blockchain facts."""

    model_config = ConfigDict(extra="forbid")

    chain: str
    tx_hash: str
    log_index: int
    block_number: int
    block_timestamp: datetime
    sender: str
    receiver: str
    asset_id: str
    asset_symbol: str
    asset_decimals: int | None
    amount_raw: int
    amount_decimal: Decimal | None
    transfer_kind: TransferKind
    status: str
    source: str
    retrieved_at: datetime
    evidence_tag: EvidenceTag = EvidenceTag.OBSERVED
