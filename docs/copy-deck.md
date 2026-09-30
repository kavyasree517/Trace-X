# Copy deck

## Document status
Standard specification for user-facing copy, notification text, and exported evidence language.

## Tone and style
All copy must use plain, neutral, professional English in sentence case. Emoticons, decorative Unicode glyphs, arrows, checkmark characters, exclamation marks, and promotional language are strictly prohibited. The system presents objective observations, derived measurements, and uncertainty boundaries without value judgements.

## Standing statement
This output is an investigative lead for human review. It is not a legal finding and does not accuse any person or organization.

## Demonstration notice
Demonstration mode. This result uses simulated data or synthetic labels and does not describe a real investigation.

## Approved phrases
- Potential exchange connection identified
- Verified label match
- Potential association
- No match found in current references
- Insufficient data
- No fund movement found for this address in the selected window
- Observed transfer
- Label source
- Pattern observed

## Prohibited phrases
The following phrases and concepts must not appear in any code, template, documentation, or user interface:
- criminal exchange
- fraudulent exchange
- scam wallet confirmed
- guilty
- proof of fraud
- fraud score
- risk percentage
- definitely
- confirmed scammer
- the exchange is responsible
- any statement of intent or knowledge attributed to an exchange or wallet owner

## Headline outcome templates

### potential_association
We checked address {address} on {chain} using data retrieved on {date}. Funds sent from this address appear to have moved through {hop_count} transfer(s) to an address labelled {entity} by {label_source}. This is a potential connection based on observed transfers and a label of {verification_level} verification. It does not show that the service knew of or took part in any wrongdoing.

### verified_label_match
We checked address {address} on {chain} using data retrieved on {date}. An observed transfer path reaches an address labelled {entity} in a source with {verification_level} verification. This describes where funds moved. It does not establish involvement or intent by the service.

### no_match_in_current_references
We checked address {address} on {chain} using data retrieved on {date}. We traced observed transfers within the selected limits and did not reach an address present in our current label references. This does not rule out a connection to a service that is not in our references.

### insufficient_data
We could not reach a conclusion for address {address} on {chain}. {reason}. Please review the limitations section.

### no_paths_found
No outgoing transfers were found for address {address} on {chain} in the selected time window.

## Caution statements

### Related report caution (mandatory)
These cases share the on-chain evidence shown below. Shared addresses can result from common services, exchange deposit infrastructure, or coincidence, and do not by themselves indicate common ownership or coordination.

### Signal note (mandatory)
This pattern can also result from legitimate activity.
