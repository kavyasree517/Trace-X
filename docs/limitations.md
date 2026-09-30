# Technical and operational limitations

## Standing statement
This output is an investigative lead for human review. It is not a legal finding and does not accuse any person or organization.

## Scope of coverage
1. Chain scope: Version 0.1.0 supports Ethereum mainnet only. Analysis traces native ETH and standard ERC-20 transfers (USDT, USDC, DAI).
2. Internal transactions: Contract-internal ETH transfers depend on trace node availability and may not be exhaustively captured when using basic explorer endpoints.
3. Non-standard token events: Tokens that do not emit standard Transfer events or that apply custom fee structures may experience value tracing continuity degradation.
4. Token swaps and decentralized exchanges: Swapping one asset for another breaks single-asset value tracing. The path records a `swap_asset_change` break reason unless decoded by a dedicated protocol adapter.
5. Privacy protocols and mixers: Interactions with Tornado Cash, Railgun, or similar protocols break continuity. The system records a `mixer_interaction` or `privacy_protocol` break and abstains from guessing recipient addresses.
6. Cross-chain bridges: Movements across bridges break single-chain graph expansion and are marked as `bridge_interaction`.
7. Chain head reorganization: Transactions within 64 blocks of the chain head are considered preliminary and subject to potential reorganization.
8. Label freshness and coverage: Entity labels represent historical observations. Addresses not present in the current reference registry yield an explicit `no_match_in_current_references` status rather than proof of non-involvement.
