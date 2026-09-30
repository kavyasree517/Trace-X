# Behavioral signals methodology

## Overview
Behavioral signals identify structural and temporal transfer patterns commonly associated with laundering topologies, such as rapid forwarding, fan-out splitting, and peel chains. All signals are qualitative indicators tagged as `inferred` or `derived`.

## Mandatory disclosure
Every behavioral signal emitted by the system is accompanied by the standing note:
"This pattern can also result from legitimate activity."

## Signal catalog
1. `rapid_pass_through`: Outgoing transfer occurring within configured threshold seconds (e.g. 300 seconds) of value arrival.
2. `fan_out_splitting`: Single incoming transaction followed by out-degree of 3 or more within a short duration.
3. `fan_in_merging`: Consolidation of 3 or more incoming paths into a single recipient address.
4. `peel_chain_pattern`: Linear sequence of transactions where a small amount is peeled off to a service and the majority sent to a change address.
5. `equal_value_repetition`: Repetitive transfers of identical asset quantities within a continuous interval.
6. `new_address_chain`: Sequential forwarding through addresses with zero prior transaction history.
7. `asset_hopping`: Conversion between disparate tokens or wrappers across decentralized liquidity protocols.

## Signal levels
Signals report descriptive pattern strength rather than fraud probability:
- `not_observed`: No evidence of the pattern in analyzed paths.
- `observed_low`: Minor or isolated manifestation.
- `observed_moderate`: Consistent structural presence across multiple hops.
- `observed_high`: Primary structural characteristic of the fund movement.
