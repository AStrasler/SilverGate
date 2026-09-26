# Step 1 implementation notes

This implements the schema/fixture/test stage of specification v0.1.8. It does not amend product policy or implement future architecture. Contracts are development drafts with version 1.0.0 as specified, not published stability promises.

## Materialized choices

- Schema identifiers use `https://silvergate.invalid/schemas/` purely as stable names. The test registry resolves them locally and does not fetch URLs.
- Separate schemas cover the evidence envelope, each of 16 record families, normalized output, claim sets, future findings envelopes and fixture expectations. Strict properties prevent unrecognized data from being silently assigned semantics. Namespaced extension objects do not grant authority.
- Additional host metadata uses `platform` fields for OS family, architecture, build, release channel, runtime edition and capture privilege level. Existing host version strings are preserved. Missing values use field states rather than manufactured platform context.
- Collector-run records reference the shared snapshot records by ID. Counts, membership, IDs, associations, null states and integrity are cross-record constraints checked by the test oracle, not solely JSON Schema.
- Normalized attributes currently use ordered name/value records with explicit null/field-state support. This is a transport envelope, not a completed normalization algorithm. Claims carry dimension/comparison values; the predicate registry is step 2. No semantic configuration setting exists; its recorded object is currently empty.

## Canonicalization and hashes

`sg-json-v1` serializes JSON with ordinal object-key ordering, no whitespace, ASCII JSON escaping, lowercase Unicode hex escapes, and array order preserved. Numeric values are integers within the exact ±(2^53−1) range; larger source values must be decimal strings. Floats, non-finite numbers, duplicate keys and invalid Unicode are rejected rather than silently normalized. Null and boolean remain their JSON types. This is a SilverGate-specific versioned profile, not a claim to implement RFC 8785.

Each record hash covers the complete record, including its evidence source, interval and field states. The manifest hash covers the entire snapshot except `integrity.manifestHash`; record hashes remain in that body. SHA-256 detects inconsistency against the manifest, not authenticity or truth. Replacing both content and hashes can produce a consistent unauthenticated artifact.

The Python contract oracle is development-only. Its checks specify constraints for the future bounded PowerShell-compatible runtime importer; passing them does not imply that runtime import or resource-isolated collection exists. Executable schema format checks and cross-record checks are both required. Unsupported evidence versions are a distinct compatibility exception.

Null-state requirements apply to unknown/omitted source fields and observation intervals. Deliberate nullable contract slots (e.g. unknown-claim strength, optional observation window, unmeasured serialized byte count) carry meaning defined by their surrounding contract rather than pretending to be captured source facts.

## Fixtures and privacy

All six AaronAura fixtures are sanitized narrative transcriptions from the supplied handoff, not raw Windows output. Original query files are unavailable. They retain unknown observation times and mark their fixed authoring timestamp as a fixture marker, not the time of original activity. Source hashes are explicitly unavailable; newly computed snapshot hashes are hashes of these new fixture artifacts only.

Machine/user paths, PIDs and MAC addresses are omitted. Peer addresses are represented by peer-A/peer-B consistently across cases. Product names, relevant observed ports and public package identities retain explanatory context. No device identity is invented. These sanitized fixtures are suitable for review without publishing raw machine history. Expected claims are handoff-derived acceptance requirements, not engine output; removal variants require future reasoning to downgrade or withdraw unsupported claims.

Synthetic fixtures are intentionally invented collector-shaped data, including hostile-looking strings. They cannot be mistaken for live AaronAura capture. Test mutation occurs in memory and leaves fixture files unchanged.

## Remaining work

The runtime validator, predicate rules, derived-output semantic joins, all collectors and reports remain subsequent steps. No live capture has occurred. No repository publication, copyright attribution, default Evidence Library location, AI governance mechanism, signing, installer or release automation is decided here.
