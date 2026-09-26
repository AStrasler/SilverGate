# SilverGate v0.1 technical specification

**Observe. Explain. Decide.**

Status: proposed implementation contract based on the accepted architecture. Specification version: 0.1.8. No implementation or machine configuration change is included in this document.

## 1. Scope and architecture

SilverGate v0.1 explains Windows Firewall permissions and observed application networking. Windows Firewall and Windows Filtering Platform remain the enforcement foundation. SilverGate has no enforcement, remediation, policy-writing, service-installation, audit-enabling, packet-injection, probing, or rollback execution functionality in this release. Local output-file writes are its only intended persistent changes.

The entry point is a manually invoked snapshot collection, followed by an independently runnable offline analysis and report pipeline:

`Collectors → immutable evidence snapshot → normalization → conservative correlation → deterministic claims → local HTML report`

Collection and interpretation are separate modules and separate commands. Analysis uses captured snapshot evidence, explicit engine/ruleset versions and any explicitly recorded semantics-affecting configuration; it must not query the current machine, network, clock-dependent reputation services, or mutable external knowledge. Reanalysis writes new derived output and never rewrites the source snapshot or historical analysis. Presentation preferences cannot change evidence claims.

**One engine, multiple interfaces.** CLI, future GUI, reports and other presentation layers derive from the same evidence model, schemas, normalization, correlation, explanation rules and epistemic model. Interface parity applies to meaning, not necessarily capability at every release. Long-term GUI and CLI are first-class interfaces; v0.1 retains CLI/PowerShell plus local HTML reports as an implementation-order decision, not a permanent CLI-first product commitment. No future GUI is designed here. The core user journey is **Capture → Save → Analyze → Explain → Report**; section 19 defines the approved workflow, configuration and evidence-lifecycle requirements.

Implementation direction: PowerShell modules for Windows collection and the initial engine, JSON contracts, Pester tests, and self-contained HTML with minimal local JavaScript for filtering. Validate NetSecurity/NetTCPIP compatibility on the supported Windows/PowerShell combination before declaring runtime support. Prefer structured CIM values over formatted console output. No runtime LLM dependency. No native service, driver, database server, web server, or browser listener is required.

The Windows-provided PowerShell environment is the primary initial runtime; PowerShell 7 compatibility must be validated and is not initially required. The canonical [platform and hardware support policy](support-matrix.md) defines support classes, source-platform metadata and release validation. Successful execution alone does not expand support. The formal threat model in section 18 applies across the existing pipeline without adding active defense or enforcement.

White-Knight is independently usable and unavailable for source inspection. Its PowerShell orientation, conceptual v1.2 version, and intended MIT license are project-context facts only. No reusable White-Knight code is assumed. A versioned findings export is the future integration boundary; an adapter is not required for v0.1.

Future optional AI integrations are governed by [AI integration governance and roadmap](SilverGate-AI-governance-roadmap.md). Core functionality must remain fully usable without AI. v0.1 adds no AI integration, score, tracker, privilege machinery or mutation path; only the actor-neutral interface provisions below prevent architectural lock-in.

## 2. Repository and directory structure

Repository/product name: `SilverGate`. This specification lives outside read-only synced `sources/`. The eventual repository should be a separate development checkout; creating that checkout is not part of this specification.

```text
SilverGate/
  README.md
  LICENSE                         # MIT; establish copyright holder before publishing
  THIRD-PARTY-NOTICES.md
  docs/
    SilverGate-v0.1-specification.md
    support-matrix.md
  schemas/
    evidence/1.0.0.schema.json
    normalized/1.0.0.schema.json
    claims/1.0.0.schema.json
    findings/1.0.0.schema.json
    collector-records/             # versioned per collector
  src/
    SilverGate.Collection/         # the only module allowed to query Windows
    SilverGate.Model/
    SilverGate.Correlation/
    SilverGate.Explanation/
    SilverGate.Reporting/
    SilverGate.Contracts/
  commands/
    Capture-SilverGateSnapshot.ps1
    Analyze-SilverGateSnapshot.ps1
    Export-SilverGateReport.ps1
  report-assets/                   # bundled; no remote resources
  tests/
    unit/
    contract/
    integration/
    fixtures/aaronaura-historical/
    fixtures/synthetic/
  samples/                        # synthetic or explicitly sanitized only
  artifacts/                      # gitignored development artifacts; not the default Evidence Library path
```

Module dependency direction follows the pipeline. Model/correlation/explanation/reporting cannot import Collection. The supported command surface has no mutating system operation. No simplewall source is copied; dependencies require license review before inclusion.

Every dependency must justify its existence. Minimize external dependencies, especially at privileged or security-sensitive boundaries. Section 20 defines approved future distribution, provenance, dependency-governance and update principles without selecting technologies or extending v0.1 implementation.

## 3. Evidence snapshot schema

Use JSON Schema draft 2020-12 for implementation contracts. The normative fields below define what those schema files must validate; this specification does not claim the executable schemas already exist. Objects reject undeclared properties except a namespaced `extensions` object. IDs are opaque strings unique within a snapshot; timestamps use UTC RFC 3339; durations use integer milliseconds; ports are integers 0–65535; PIDs are nonnegative integers. Enumerations are closed within a major schema version.

Snapshot manifest required fields:

| Field | Type / constraint |
|---|---|
| `schemaVersion` | Semantic version of evidence contract, initially `1.0.0` |
| `snapshotId` | UUID, immutable |
| `origin` | `live_capture`, `historical_transcription`, or `synthetic` |
| `producer` | `{name, version, collectorSetVersion}` |
| `captureWindow` | `{startedAt, endedAt}` for capture/transcription time, not necessarily historical event time |
| `host` | `{scopeId, reportedName, osVersion, runtimeVersion}`; unknown values represented explicitly; additional platform-context representation remains to be specified as described below |
| `sources` | Array of source descriptors described below |
| `collectorRuns` | Array of run/coverage records |
| `records` | Array of immutable evidence records |
| `privacy` | `{policyVersion, omissions, redactions}` |
| `integrity` | Content hashes of evidence payloads and declared canonicalization version |

Source descriptor: `{sourceId, kind, label, sourceHash, originalObservationWindow, precision}`. Kind is `windows_query`, `user_handoff`, or `synthetic_fixture`. Historical timestamps may be unknown; retain known date/interval precision without manufacturing exact times. Full original handoff text need not be embedded in every snapshot; preserve permitted excerpts and a source hash for traceability.

Record sufficient OS, architecture, runtime, build and retail/pre-release channel context to interpret evidence on its actual source platform. Preserve reported values and their provenance; missing information remains explicitly unknown under the existing evidence conventions. Do not infer retail status from missing Insider metadata or invent historical build/runtime details. The exact additional field names, layout and acquisition mechanisms remain to be specified when materializing the evidence schema; this update does not prescribe new platform enums or configuration mechanisms. Preserve section 17 compatibility/versioning requirements.

Imported snapshots, including SilverGate-generated artifacts reintroduced as inputs, must pass applicable structural, compatibility, evidence-reference and integrity validation before acceptance for analysis or Evidence Library use. No producer name grants a validation exemption. Integrity mismatch or invalid required structure prevents analysis of that input with explicit diagnostics, not a safe/dangerous judgment. Valid format compatibility is evaluated independently of source capture-platform support; preserve experimental/unsupported platform context and qualify unevaluable semantics rather than rejecting solely on source OS/build. Platform labels do not replace schema-version validation.

Each evidence record requires `{recordId, collectorRunId, sourceId, recordType, recordSchemaVersion, observedWindow, payload, fieldStates}`. `observedWindow` is `{start, end, precision}` with nullable bounds when unknown. For a live query, it spans that query, not the entire user session. `payload` retains source-returned semantic values before interpretation: do not replace `Any`, `NotConfigured`, wildcard addresses, numeric enums, SIDs, or rule names with friendly judgments. Preserve original and translated enum values separately when translation is needed.

`fieldStates` maps unavailable or omitted field paths to `{state, reasonCode}`. States: `unknown`, `inaccessible`, `unsupported`, `not_collected`, `redacted`, `not_applicable`, `conversion_failed`. A null value requires a field-state entry. Empty arrays mean successfully observed empty collections only. An absent field is permitted only when optional in that record schema; it must not silently mean false.

Raw means a declared, versioned projection of source properties serialized without interpretive alteration, not an unrestricted memory or registry dump. Collector schemas document included and intentionally omitted fields. Serialization must handle 64-bit values without JavaScript precision loss (decimal strings where necessary), bounded strings, and explicit conversion errors. JSON source data is never executable input.

Required record families:

- `firewall_rule`, `firewall_filter`, `firewall_profile`: policy store, source metadata, enabled/action/direction/profile, conditions and associations. Include disabled rules, allow rules, and block rules.
- `process`: PID, creation time where available, image path, parent PID as reported; exclude full command line by default.
- `tcp_connection`, `udp_endpoint`: owner, local endpoint, available remote endpoint/state, creation metadata if supplied. UDP endpoint data does not manufacture peers or packet counts.
- `interface`, `ip_address`, `route`, `network_profile`: family, interface identity/index, prefix/scope, routes and metrics, profile attachment.
- `file_identity`, `signature`: file metadata, hash when collected, signer details and validation status, validation mode and limitations.
- `package`, `service`, `integration_registration`: targeted identity and dependency evidence, with explicit acquisition scope.
- `historical_assertion`: handoff excerpt, its stated observation or interpretation, and what original evidence is unavailable.

Preserve enough source fields to evaluate application/package/service identity, protocol, local/remote ports and addresses, interface conditions, profile, enabled state, action, direction, and security conditions. If a Windows condition cannot be represented or evaluated, retain its raw value and produce `indeterminate`; do not silently drop it.

Integrity hashes detect later byte/content changes relative to a manifest; they do not authenticate the machine, user, or truth of telemetry. Define canonical JSON serialization and hashing in contract tests. Keep the final manifest hash outside its own hashed body.

## 4. Normalized entity schema

Derived output requires `{schemaVersion, analysisId, inputSnapshotIds, inputHashes, engineVersion, rulesetVersion, normalizerVersion, entities, relationships, coverage}`. Initial v0.1 analyzes one snapshot per analysis; the plural input-reference fields preserve extensibility without implementing comparison. Semantic snapshot comparison/diff and multi-snapshot reasoning are deferred beyond the initial core milestone; their semantics are not defined here. Never automatically merge unrelated hosts or historical/live data. Any configuration that legitimately changes analytical semantics must be preserved in analysis provenance sufficiently to explain and replay the result; its exact representation remains to be specified rather than inferred from presentation settings.

Every entity has `{entityId, entityType, attributes, evidenceRefs, fieldStates}`. Evidence references use `{snapshotId, recordId, jsonPointer}` and must resolve. Derived IDs are deterministic from input identity and normalization version.

Subjects are entity references, not necessarily executable applications. Actor-capable entities may include the optional descriptor `actor: {kind, identityRefs}`, with `kind` drawn from `application`, `service`, `automation`, `agent`, or `unknown`; `identityRefs` references evidence-backed entities. This descriptor grants no privileges or trust. An agent may run through an application/service, but those identities must not be conflated. v0.1 populates only evidence-supported kinds and does not implement agent discovery. Missing actor metadata is unspecified, not implicitly `application`. Existing `subjectIds` and relationship endpoints remain generic entity IDs, including in findings exports. Unknown future enum values continue to follow the compatibility rules in section 17.

| Entity | Identity and essential attributes |
|---|---|
| Application | Executable/package/service identity; display label is not identity. Keep versions/file identities distinct under an explicit application grouping. |
| Executable | Original path, normalized comparison path, hash if available, file metadata, signature result. Same path does not establish unchanged contents. |
| ProcessInstance | Host scope + PID + creation time when available. Without creation time, scope to the query interval and mark joins weaker. |
| SocketObservation | Record-scoped endpoint/state/owner observation; not a persistent socket identity across snapshots. |
| FirewallPermission | Rule/store identity plus collected condition set and enabled/action/direction values; preserve conflicting store views. |
| Interface / NetworkContext | Interface and family scoped addresses, prefixes, profiles, routes, and observation interval. |
| PeerEndpoint | Address + IPv6 zone/interface scope where applicable + observed context. IP and MAC do not prove stable device identity. |
| Package / Service / Feature | Identity and registration/association evidence; feature labels may be inferred. |

Relationship schema: `{relationshipId, type, from, to, epistemicStatus, strength, evidenceRefs, limitations}`. Types include `process_of`, `owns_endpoint`, `registered_with`, `package_of`, `service_in_process`, `candidate_permission_for`, `observed_peer`, `possible_feature_dependency`. Strength is `direct`, `corroborated`, or `heuristic`, and is not a security score.

Do not infer a specific hosted service from an `svchost` PID containing multiple services. Parent PID alone does not establish a durable parent process instance. Preserve ambiguity when identity or timing is insufficient.

## 5. Evidence-claim schema and epistemic status

Required claim fields:

```json
{
  "claimId": "claim-example",
  "subjectIds": ["application-example"],
  "predicate": "permission_scope_exceeds_observed_endpoints",
  "epistemicStatus": "inference",
  "strength": "corroborated",
  "value": {"dimension": "localPort", "comparison": "strict_superset"},
  "evidenceRefs": [
    {"snapshotId": "snapshot-example", "recordId": "rule-example", "jsonPointer": "/payload/localPort"},
    {"snapshotId": "snapshot-example", "recordId": "socket-example", "jsonPointer": "/payload/localPort"}
  ],
  "premiseClaimIds": [],
  "ruleId": "comparison.port-scope.v1",
  "scope": {"snapshotIds": ["snapshot-example"], "observationWindow": null},
  "limitations": ["A bounded observation does not establish every port the application needs."],
  "unknownReason": null,
  "templateId": "permission.port-scope.v1"
}
```

This is an illustrative claim, not an AaronAura observation. Production claims require resolvable IDs and either a known observation interval or an explicit unknown-time limitation.

Epistemic statuses:

- **Fact:** a directly supported, properly scoped observation or registration. A handoff fact is phrased as “the handoff records…” rather than promoted to live telemetry.
- **Inference:** a conclusion from identified premises under a named rule, with limitations.
- **Hypothesis:** a plausible explanation with explicit supporting evidence and missing confirmation; never used as an established premise for a stronger conclusion.
- **Unknown:** unresolved value with a reason and missing evidence description. This is a first-class claim, not an exception to suppress.

Strength describes evidential support only. Unknown claims use `strength: null`. Signed publisher, known provenance, user feature usage, dependency footprint, and restriction impact remain separate dimensions. Do not collapse them into a risk score. Contradictory evidence is retained and surfaced; newer data does not silently rewrite older facts.

## 6. Collector interface and execution

Proposed interface: `Invoke-SilverGateCollector -Context <CaptureContext> → CollectorResult`. Context contains snapshot/run IDs, deadline, cancellation, selected collection scope, privacy policy, and bounded work limits. The coordinator creates timing metadata and persists results. Collectors have no access to the interpretation engine.

CollectorResult requires `{collectorId, version, recordSchemaVersion, status, startedAt, endedAt, durationMs, records, errors, coverage, metrics}`. Status values: `success`, `empty`, `partial`, `inaccessible`, `unsupported`, `failed`, `timed_out`, `cancelled`, `not_requested`. `success` requires nonempty results; `empty` requires a completed supported query with zero results. A partial result retains usable records and detailed missing scope.

| Collector | Source / scope | Scheduling and cost |
|---|---|---|
| Firewall | ActiveStore rules/profiles and associated filters; PersistentStore definitions separately | Once per capture; bounded bulk work, no query per socket |
| Process | CIM process inventory and creation metadata | Once close to endpoint capture; record race windows |
| Endpoints | TCP connections and UDP endpoints | Once each; sequential timestamps retained |
| Network context | Interfaces, addresses, profiles, route table | Once per capture; family/interface scoped |
| Executable identity | Relevant executable paths from processes and rules | Deduplicate paths/file identities; bounded cached enrichment |
| Package/service | Relevant package identities and service mapping | Inventory once where needed; targeted enrichment |
| Integration | Explicitly selected registrations for dependency cases | Opt-in targeted scope; no recursive registry archaeology |

Parallelism is bounded. Process/endpoint/network captures should be close in time, but no atomic snapshot is promised. If process identity changes or vanishes during enrichment, report that mismatch; do not attribute the new process's identity to the earlier endpoint.

Default execution does not auto-elevate. Record the caller's collection capabilities; inaccessible fields remain inaccessible. Any future user-launched elevated read-only capture must still exclude all mutation operations. Do not enable firewall logging, event auditing, or ETW sessions as a side effect of collecting v0.1 data. Existing event-log data is an optional later collector, not required for the baseline milestone.

Standard-user capture is the supported default. Explicit user-launched elevated read-only capture is supported where implemented and validated: elevation expands visibility, not authority. It never implicitly permits mutation or unrelated privileged operations. Missing coverage remains explicit in either mode; collectors must not demand elevation merely to suppress honest unknowns.

Section 21 consolidates the privilege invariants and future elevated collection boundary. It does not require a helper or additional collection in v0.1. The primary application, analysis, report generation and Evidence Library interaction remain standard-user wherever practical.

## 7. Correlation rules

1. Match endpoints to process instances using owner PID and compatible capture/creation times. PID-only associations are explicitly weaker; ambiguous matches remain unresolved.
2. Join executable identity by normalized Windows path comparison and available file identity; retain original path, environment expansion context, and unresolved aliases. Never merge solely by filename.
3. Evaluate candidate permissions using all collected conditions. Per-condition result is `match`, `no_match`, `indeterminate`, or `not_applicable`; retain evidence and reason for each.
4. A definitive mismatch excludes that rule for the evaluated scenario. Unresolved conditions prevent “all conditions matched.” Disabled rules remain visible as dormant definitions but are not enabled candidates.
5. Evaluate listener scenarios separately from flows. For a listener with no peer, remote address/user/machine constraints cannot be fully tested. For a TCP connection with unknown initiation direction, do not assign inbound/outbound rule applicability as fact.
6. An all-condition candidate remains a candidate. Rule precedence, policy, IPsec, service restrictions, other WFP providers, routing and upstream controls can affect the actual result. v0.1 does not identify the authorizing rule or prove reachability from candidate matching.
7. Package-scoped rules must retain package restrictions when Program is Any. Generic permissions must not become unconditionally attributed application-specific rules.
8. Compare permission versus observation dimension by dimension: protocol, local port, remote endpoint, profile/interface. Require explicit permission and observation references, compatible scope and collection coverage. No observations yields `insufficient_observation`, not an empty-set argument for unnecessary permission.
9. Distinct observed ports support “multiple ports observed.” “Dynamically selected ports” requires explicit supporting historical evidence or controlled repeated-session evidence; high port numbers alone do not establish dynamic selection.
10. A registration proves integration exists; it does not prove current use or that a restriction will break it. Restriction impact is `unknown` or evidence-qualified; v0.1 generates no proposed policy change.

## 8. Network-context classification

Store separate dimensions rather than one overconfident LAN/Internet label:

- `bindingScope`: loopback-only, specific-interface-address, wildcard-v4, wildcard-v6, unknown.
- `addressClass`: loopback, link-local, private-v4, unique-local-v6, global-unicast, multicast, broadcast, unspecified, other-reserved, unknown.
- `pathContext`: same-host, on-link, routed-private, virtual-network, external-route, ambiguous, unknown.
- `activityKind`: TCP-listener, TCP-state-observation, UDP-bound-endpoint, independently-evidenced-traffic.
- `initiationDirection`: inbound, outbound, unknown, with its own evidence requirement.
- `reachability`: not-assessed in v0.1 unless explicitly supplied independent historical evidence establishes a narrowly scoped observation.

Use address parsing, actual interface prefixes, relevant route selection and interface context. For equal/ambiguous routes or missing routing evidence, retain ambiguity. Private address space does not establish on-link membership. An on-link route indicates local topology, not trusted identity. A global address routed through a VPN is not proof of a physical Internet path. Do not use TCP `AppliedSetting=Internet` as destination geography or path classification.

Treat IPv6 zone IDs, IPv4-mapped IPv6, multiple interfaces, VPNs, Hyper-V and disconnected profiles explicitly. A wildcard IPv6 bind does not prove IPv4 acceptance. Loopback classification uses the address family’s loopback semantics; wildcard addresses are not loopback.

Protocol hints based on port numbers are labeled hypotheses unless stronger evidence exists. A UDP 5353 binding may be consistent with mDNS; it does not itself establish a multicast destination, emitted packet, or Spotify Connect activity. Special firewall address keywords remain symbolic when Windows semantics/context cannot be resolved safely.

## 9. Rule provenance

Provenance object: `{category, epistemicStatus, strength, evidenceRefs, alternatives, limitations}`. Categories: `windows_user_consent`, `installer`, `windows_component`, `package_capability`, `administrator`, `policy`, `unknown`.

- A `Query User` rule-name pattern supports a consent-origin inference, not proof of who approved it or when.
- Package identity plus capability/rule evidence can support package-capability provenance. Rule naming alone is weaker.
- PolicyStoreSource and source type establish reported store/source context, not necessarily human creator identity.
- A GUID name does not identify an installer. Local/PersistentStore does not prove manual administrator creation.
- Publisher/signature identity and provenance are independent. Do not infer creation history from the current executable signature.

Preserve raw rule names/store fields for inspection. If evidence conflicts, show competing interpretations and unresolved provenance.

## 10. Deterministic explanation generation

Use a versioned registry of predicates, preconditions and text templates. Each template lists required claims, minimum support, uncertainty wording, and prohibited implications. Generated sentences link to their exact claims and underlying record fields. Text generation cannot invent feature names, identities, user intent, or causal impact.

Examples of permitted wording:

- “A TCP listener was observed on a loopback address during this snapshot.”
- “This enabled rule permits any local TCP port within its other conditions. The snapshot observed these local ports: …”
- “No matching process was observed during this completed process collection. This does not establish that the component is unused.”
- “The handoff records dynamic port use; this capture does not independently establish port selection behavior.”
- “I don't know which physical device owns this address.”

Do not say “safe,” “malicious,” “obsolete,” “unused,” “Internet-exposed,” or “this rule allowed this connection” based solely on broad permissions, signatures, missing activity, wildcard binds, or candidate matches. Do not say no activity was observed if relevant collection failed; explain the coverage gap instead.

Stable inputs, engine version and ruleset version produce identical semantic output and ordered report content. Generation timestamps and output paths are explicitly excluded from semantic reproducibility comparisons. Template changes require ruleset version changes and regression review.

## 11. Errors and coverage

Error record: `{errorId, code, collectorId, affectedScope, fieldPaths, message, retryable, evidenceRefs}`. Use stable codes such as `ACCESS_DENIED`, `SOURCE_UNAVAILABLE`, `TIME_LIMIT`, `PROCESS_EXITED`, `IDENTITY_CHANGED`, `UNSUPPORTED_VALUE`, `SERIALIZATION_ERROR`, `INVALID_INPUT`. Sanitize diagnostics; do not leak command lines or secrets in error text.

Coverage record: `{requestedScope, completedScope, missingScope, interval, completeness, limitations}`. Completeness is `complete_for_declared_query`, `partial`, or `none`; a completed snapshot query is not complete observation of activity between snapshots.

Claims depending on missing evidence become unknown or explicitly qualified. Failed enrichment must not erase successful core collection. Invalid snapshot structure or unresolved required evidence references causes analysis failure with diagnostics rather than a reassuring report. Optional unsupported collectors produce a coverage warning and usable partial report.

The intelligence engine fails honest: inaccessible, unsupported, unavailable, malformed or failed evidence never silently becomes either safe or dangerous. Diagnostic rejection of malformed input is not a malware finding about its producer. Any future fail-closed action boundary is separate from this epistemic rule.

## 12. Local HTML report

One self-contained HTML file, derived from normalized output and claims. No server, remote scripts, fonts, analytics, images, fetch calls, or active external resources. All source strings are escaped as untrusted text; raw JSON embedding must resist closing-script injection. Enforce a restrictive content security policy consistent with bundled assets. Never execute executable paths, rule strings, links, or snapshot content.

Report structure:

1. Header: SilverGate, tagline, machine scope, capture interval, origin, analysis versions and coverage. Historical/synthetic origin is prominent on every affected view.
2. Application index: name/path identity, observed process state, listener/endpoint summaries, permission count, unresolved evidence count. No scary aggregate risk score.
3. Application detail: separate “Permissions” and “Observed during this snapshot” panels; TCP listeners, TCP connection states, UDP bindings and independent traffic evidence kept distinct.
4. Explanation panel: deterministic statements with fact/inference/hypothesis/unknown labels and “Why?” expansion.
5. Permission detail: raw scope, store/provenance, condition evaluation, enabled/disabled state, and candidate-match limitations.
6. Evidence/dependency view: supporting records, registration relationships and limitations, including conflicting claims.
7. Coverage diagnostics and version/integrity information.

Filters operate on embedded cached state. Keyboard navigation and readable non-color status labels are required. No enforcement button, disabled enforcement placeholder, modification command, or automatic refresh that recollects Windows data.

Preserve source-platform context with findings and distinguish capture support from format compatibility. The placement and presentation of this information are not decided by this update; missing metadata remains unknown.

## 13. AaronAura acceptance fixtures

All six initial fixtures are **historical transcriptions** of the supplied handoff. They are not raw exports and must not invent missing original rules, GUIDs, event timestamps, packet records or hashes. Their observation time precision reflects what the handoff actually supplies. Exact IPs/PIDs may exist in private local fixtures; committed/public fixtures use documented synthetic substitutions while retaining equality/relationship structure.

Each fixture contains an evidence snapshot, expected structured claims, forbidden claims, expected coverage gaps, and a source/provenance note. Separate synthetic collector-shaped fixtures exercise parsing of complete Windows records; never relabel transcribed narrative as native collector output.

| Fixture | Required conclusions | Forbidden conclusions |
|---|---|---|
| Spotify | Historical loopback listener at 7768, wildcard IPv4 listener at 57621, reported discovery/dynamic-port behavior, Public inbound TCP/UDP rules, consent-origin inference, .23 identity unknown. Scope comparison cites both permission and observation evidence. | Using every port; malicious because Any; current PIDs/ports from history; UDP packets proven by bindings; .23 identified as Chromecast; dynamic selection proved by one high port. |
| Smart Connect | Historical active component relationships, .21 incoming listener interaction and VaultPlugin outbound .23 interaction as handoff-supported direction; loopback and external connections distinguished. | New-snapshot direction deduced from endpoint numbers; physical peer identity known; every broad rule necessary or safe. |
| Adobe Native Client | Reported package identity and internetClientServer capability explain capability-rule context; Program=Any does not discard package scope. | Unrestricted permission for every program; signature/capability proves optimal policy. |
| Lync/UcMapi | Reported serviced signed Office components, no sockets observed in the historical interval, extensive registration/integration footprint, rule creator unknown. | Obsolete, malicious, removable, never starts, or dependencies proven to be actively used. |
| Hyper-V | Intentional installed infrastructure and virtual-interface context; VM removal does not imply removal of Hyper-V dependency. | Infrastructure unnecessary; virtual/private traffic automatically equivalent to physical LAN; recommending disablement. |
| File & Printer Sharing | Historical selected Public inbound rules disabled; definitions remain; no global SMB disablement follows; outbound NAS use is a user requirement, not observed NAS traffic. | 139/445 impossible to reach; Private/Domain rules disabled; SMB stack absent; future NAS already contacted. |

Add negative variants to each applicable fixture: failed process inventory, inaccessible signature, absent rule filters, stale or ambiguous identity, unknown profiles, contradictory evidence. Removing support must downgrade/withdraw claims, never leave the same confident explanation.

## 14. Unit and integration test strategy

Contract tests validate every fixture, null/field-state behavior, evidence-reference resolution, version compatibility, bounded input handling, and snapshot hash validation. Parser tests include unknown enums and malformed filter values. Normalization tests cover Windows path handling, package identity, PID reuse, shared service hosts and capture races.

Correlation tests exercise tri-state condition matching, disabled rules, block/allow coexistence, unknown direction, missing filter data and profile/interface ambiguity. Classification tests cover loopback, wildcard, IPv6 scopes, mapped addresses, multicast, private routed destinations, VPN and Hyper-V. Explanation tests assert structured predicates and evidence dependencies; exact wording is asserted only where wording carries a safety-critical distinction.

Metamorphic tests: reorder input records without changing conclusions; remove a premise and require uncertainty; change a peer address without manufacturing identity; change an allow to disabled and withdraw enabled-candidate claims. Fixtures must not train special-case hardcoded exceptions for the six product names.

Replay integration: analyze the same immutable fixture with networking and Windows-query entry points unavailable. Verify deterministic output and unchanged source hashes. Reanalysis with a newer engine creates separately attributable derived output, preserving the original snapshot and historical analysis. Validate each output against its expected claims/provenance without requiring a product semantic comparison/diff engine in v0.1.

Report integration: validate escaping with hostile app names/paths, offline operation, evidence links, keyboard access, historical banners, and absent mutation controls. Test renders with large but bounded inventories and partial failures.

AaronAura integration is a separately invoked read-only capture after implementation: verify actual host identity, query coverage, per-collector timing and limits; inspect all six cases present at that time. Missing applications or changed activity are valid outcomes, not automatic regression failures. Compare live results with historical expectations only where the live evidence supports the same conditions. Do not open apps, change profiles, create firewall rules, or reproduce network traffic automatically.

Release gate: six historical reasoning fixtures and their uncertainty variants pass; offline replay is deterministic; no Windows-query dependency exists in analysis; mutation surface checks pass; report traceability and coverage are verified; performance is measured and limitations documented. This specification itself does not claim those tests have run.

Threat-model regressions must exercise command/prompt/markup-like values in process names, paths, rules, packages, registry-derived fields, filenames, network values and imported records. They must remain data, never change rules/templates or execute code, and never alone trigger a maliciousness conclusion. Validate report escaping and bounded processing using those inputs. Reimported SilverGate artifacts receive the same checks as external inputs; test altered payloads, incompatible structure, missing references and integrity failures. Hash validity must not generate an authenticity/truth claim. Removing evidence or replacing it with a collection error must yield unknown/qualified claims, never safe/dangerous defaults. Microsoft-origin and signed-source fixtures must satisfy the same evidentiary requirements as other sources.

Platform acceptance must follow the canonical support policy: standard-user coverage, validated elevated read-only behavior, Hyper-V/virtual interfaces, VPN/multiple adapters, IPv4/IPv6 and Windows-provided PowerShell. Test experimental build/channel preservation, unknown metadata, and offline analysis of valid compatible snapshots from unsupported source platforms. No passing replay promotes live-capture support. Verify below-baseline warnings without arbitrary hard blocks. Validate representative minimum hardware before advertising that floor as supported; high-end development-machine measurements alone do not meet this gate.

Workflow/lifecycle acceptance criteria are in section 19. They distinguish core pipeline checks from future-UX requirements and do not add an implementation phase, comparison engine or storage-management subsystem to the current sequence.

## 15. Performance boundaries

Initial engineering budgets below are targets to validate on AaronAura, not measured guarantees:

They also require validation on hardware reasonably representative of the proposed floor in [support-matrix.md](support-matrix.md) before minimum-spec support is claimed. The hardware floor does not increase these budgets or mandate optimizing for configurations below it.

| Boundary | Initial policy |
|---|---|
| Collection scheduling | Manual only; zero idle background activity |
| Collector concurrency | Maximum 2; executable enrichment maximum 2 workers |
| Core query budget | 15 seconds per collector; 60-second total capture soft deadline |
| Enrichment budget | At most 200 distinct relevant executables per capture; report skipped scope |
| Cancellation | Stop scheduling immediately; isolate potentially blocking providers in terminable workers |
| Capture storage | 50 MiB serialized snapshot target/hard configured output cap; no silent truncation |
| Analysis input | Default 50 MiB per snapshot; maximum 100,000 evidence records per snapshot, JSON nesting depth 32, and 1 MiB per string; multi-snapshot replay-set limits are deferred with comparison |
| Local history | Existing capacity budget: at most 10 snapshots and 500 MiB total; refuse new persistence when full and explain available user-controlled options. This is not retention expiration or authorization to delete/overwrite artifacts. |
| Offline processing | Target under 5 seconds for one maximum-default snapshot; peak working set target under 300 MiB |

Record elapsed time, record counts, serialized bytes, cache hits, skipped scope and timeout status. If size/work limits are reached, persist a valid partial snapshot within the cap or fail cleanly; never label truncated data complete. Enforce the same structural caps during capture serialization and analysis parsing, and test them against adversarial input. Limit correlation to 1,000,000 condition evaluations per analysis; exhausting that budget produces explicit partial correlation coverage, never a no-match conclusion for unevaluated candidates. Capacity and processing budgets do not permit automatic cleanup, expiration or silent replacement of existing evidence.

Avoid per-rule-per-socket Windows queries. Normalize once, index by protocol/application/package/service, then evaluate shortlisted candidates with bounded comparisons. Cache identity enrichment using file identity/version metadata and invalidate on change; preserve collection time and do not imply a cached signature was checked now. Evidence replay never consumes a live cache.

Signature validation must not trigger network retrieval by default. Implement and test a cache-only/offline trust policy, or report validation unsupported/unknown when the chosen API cannot guarantee it. Record signer extraction separately from chain/revocation validation. Existing Windows access side effects such as ordinary OS caching are outside the claim of zero configuration changes.

## 16. Privacy boundaries

Local-only capture, analysis and reporting; no telemetry, external DNS/reverse-DNS lookup, OUI service, geolocation, reputation lookup or package download in the runtime pipeline. Do not collect packet payloads, credentials, browser history, full command lines or unrestricted registry dumps. Application paths, usernames, addresses and process history are sensitive even without payloads.

Default captures use a predictable local Evidence Library: SilverGate's organization/indexing concept for files on user-controlled storage, not project-operated storage or maintainer custody. The exact default path remains unresolved. Keep evidence outside version control; users retain custody and may explicitly export/copy artifacts elsewhere. Do not automatically upload or synchronize the library to any remote destination. Warn if a selected location is known to be synchronization-backed; do not promise no cloud storage when an external synchronization mechanism may transfer it. Use normal user-only access controls where available and report inability to establish the intended storage boundary; no system policy changes are needed. Sections 19 and 20 govern lifecycle and custody without prescribing a storage backend.

**Not everything available to observe needs to be observed.** Collection and processing require a defined role in the operation the user requested. The documented firewall/network-analysis purpose supports its relevant evidence, not blanket authorization for unrelated surveillance or indefinite collection. This principle does not introduce a new fixed retention period or collector policy. Future update validation is separately scoped in section 20 and does not alter v0.1's no-telemetry/no-upload behavior.

Exports are explicit file operations. A sanitized copy is a new derived artifact with its own hash, redaction manifest and references to its parent; it never overwrites raw evidence. Consistent pseudonyms must preserve relationships needed for tests, while clearly changing identity claims. Reports inherit snapshot sensitivity. No automatic sharing or transmission to White-Knight.

## 17. Versioning and future findings contract

### Application versions and release provenance

**0.x permits evolution, not chaos.** Use semantic-version-style application numbering `MAJOR.MINOR.PATCH`. During pre-1.0, MINOR versions may include necessary, intentional and documented breaking evolution reflected in applicable compatibility/version information. PATCH versions ordinarily carry compatible fixes, security corrections or similarly bounded changes rather than intentional feature-contract breakage. No additional numbering rules are established here.

**Application versions and data-contract versions are independent.** Application version alone does not identify every schema or behavioral contract. Preserve applicable evidence, normalized, claim, normalization, correlation/reasoning and report-format/version information sufficient to interpret and replay derived output. This document's specification revision is not an application release or proof of implemented compatibility.

The only initial conceptual channels are:

| Channel | Meaning |
|---|---|
| Stable | Normal supported release carrying current project compatibility/support commitments |
| Preview | Deliberate broader evaluation of sufficiently integrated upcoming functionality, without Stable's compatibility/support commitment |
| Development | Active-development builds with no normal support or stability promise |

**Release channel is provenance, not evidence quality.** Preserve producer version/channel where available; consider them for compatibility and known defects, not automatic truthfulness, invalidity, maliciousness or quality judgments. Unknown historical channel remains unknown. SilverGate channel is distinct from Windows retail/Insider platform context. Exact metadata representation remains to be specified within the applicable contracts. No additional channels or distribution mapping is selected.

### Contract compatibility, migrations and replay

Version separately: evidence schema, each collector record schema, normalized schema, claims schema, findings schema, producer, collector set, normalizer, engine, ruleset/templates, privacy policy and canonicalization algorithm. Product v0.1 may use contract v1.0.0; these numbers serve different purposes.

Within a contract major version, additions are permitted only through declared optional fields/extensions and must not alter existing semantics. Unknown enum values or required semantics fail compatibility checks rather than being guessed. Breaking changes increment the major version. Offline migrations create new artifacts with parent hashes and migration version; originals remain immutable.

Future findings export envelope:

`{schemaVersion, exportId, producer, inputSnapshots, analysisVersion, hostScopeId, findings, coverage, privacy}`

Each finding requires `{findingId, subjectIds, predicate, epistemicStatus, value, evidenceRefs, limitations, observationWindow, explanation}`. Include origin and provenance through referenced claims/records. Findings carry no executable commands, remediation requests, approval tokens or assumptions about White-Knight internals. An exported subset must include enough referenced evidence or explicit unavailable-reference indicators to remain honest and inspectable.

Finding identity is stable for the same semantic conclusion and evidence under the same version; analysis/export instance IDs are separate. Future consumers must negotiate contract support and retain uncertainty. A finding is information, never authorization to modify the machine.

**Prefer reading historical evidence over rewriting it.** Where reasonably possible and safe, newer versions should continue interpreting supported older evidence formats. This is separate from live-capture platform support and is not an indefinite compatibility guarantee.

**Migration never destroys or silently mutates original evidence.** A required newer representation is a derived artifact with provenance back to its unchanged original, preserving limitations and unknowns. Existing migration version/parent-hash requirements above remain applicable. No migration tooling, automatic conversion or UX is implemented by this architecture decision.

**Unsupported format ≠ invalid evidence.** A version this analyzer cannot interpret is an analyzer compatibility limitation, distinct from structural/integrity failure and not proof of false, corrupted or invalid evidence. Compatibility rejection must identify that distinction rather than mislabeling unavailable validation as a failed integrity check. Unsupported input need not be analyzed, but its evidence ownership and local accessibility remain unchanged.

Reanalysis with newer reasoning creates a new derived result, preserving historical results and provenance. Where a historical reasoning environment cannot be reproduced, disclose that limitation instead of claiming exact replay.

### Maturity, deprecation and security communication

**1.0 represents a meaningful stability commitment.** Reach 1.0 only when the core Observe → Explain → Decide contract is sufficiently stable for reasonable reliance on documented interfaces, evidence compatibility commitments, security boundaries, installation/update model and support policy. Elapsed development time or a desirable version number is insufficient. 1.0 does not mean completion or an end to evolution; its exact checklist remains unresolved.

**Deprecation is notice, not disappearance.** When practical, explain what is deprecated, why, any replacement/migration path, and the earliest version/release boundary for removal. Deprecation cannot silently rewrite or destroy evidence. Security emergencies may justify accelerated disabling/removal when necessary, with the security reason and affected versions/capabilities explained; this does not authorize remote disablement merely because support ended.

**SilverGate applies its epistemic standards to itself.** Security release communication states, to the extent established, affected versions, affected component/security boundary, fixed version, required user action and possible impact on evidence integrity, confidentiality, authorization or other relevant properties. Unknown impact stays UNKNOWN rather than reassuring or catastrophic speculation. No vulnerability-scoring bureaucracy or advisory infrastructure is selected.

### Support lifetime and authority

During pre-1.0, **Current Stable is the primary supported SilverGate release**. Older-version fixes/assistance may be offered where practical, especially for security, without indefinite backports, multi-year maintenance or LTS promises. **No accidental LTS commitment.** Exact windows and future LTS policy require explicit decisions; see the canonical [support policy](support-matrix.md).

**End of support ≠ remote disablement or loss of user ownership/local functionality.** Unsupported-release warnings and recommendations may be appropriate, but support status alone cannot remotely disable an installed copy, delete evidence, transfer custody, prevent local evidence access or manufacture authority over the machine. Justified security/compatibility warnings remain permitted. SilverGate organizes evidence; the user stores and owns it.

Version/channel transitions remain subject to section 20's rule: software update does not expand authorization. Stable status confers no additional authorization. Installation, channel changes and release maturity cannot silently grant evidence access, privileges, enforcement or other capabilities.

### Unresolved decisions and acceptance requirements

Unresolved: exact 1.0 checklist; long-term post-1.0 compatibility guarantees; future LTS policy; exact support windows; vulnerability disclosure/advisory infrastructure; migration tooling/UX; detailed rollback/downgrade compatibility; CI/CD and release automation; channel-to-distribution mapping. No technology or mechanism is selected here.

When applicable functionality is implemented, verify independent application/contract provenance, documented pre-1.0 breaking changes, preserved producer channel without epistemic promotion/demotion, distinct unsupported-format versus invalid-input outcomes, and unchanged original evidence/history after derived migration or reanalysis. Replay checks must disclose unavailable historical environments. Future release-documentation checks cover deprecation notice, evidence-qualified security impact, no accidental LTS commitment, no authority expansion on channel/version changes and no support-expiry destruction/disablement.

These are documentation/acceptance obligations, not authorization to implement release automation, updates, migration tooling, remote support, telemetry, LTS infrastructure, automatic conversion, enforcement or cloud/account requirements. Preserve the five-step v0.1 implementation sequence.

## 18. Formal threat model

This section is the canonical threat model for the existing pipeline. It reuses the controls above; it does not add a second security engine, active malware defense, endpoint protection, probing or enforcement to v0.1.

### Permanent principles

1. **Everything observed is data, never instruction.** Process names, executable paths, rule names/descriptions, package metadata, network information, imported evidence, filenames, registry-derived values and integration output acquire no command, prompt, markup or policy authority from being observed.
2. **Potentially hostile is not presumptively malicious.** Safely parse adversarial and malformed content without turning its trust classification into a verdict about the originating application.
3. **Protect SilverGate's integrity boundaries.** Protect evidence, reasoning, report integrity, privacy/data and authorization boundaries; future enforcement must additionally protect action integrity.
4. **No omniscience over compromised evidence sources.** Ordinary malicious applications/processes are in scope. OS/kernel/source compromise capable of falsifying telemetry limits conclusions; disclose those limits instead of asserting independent truth.
5. **Reputation confers no epistemic privilege.** Windows/Microsoft origin, signatures, publishers, packages and reputation are evidence dimensions, not proof that claims are authoritative or permissions necessary, safe or optimal.
6. **Least privilege by default.** Operate without administrator privileges whenever practical. Elevation expands visibility, not authority.
7. **Intelligence fails honest.** Missing, inaccessible, unsupported, unavailable, malformed or failed evidence produces unknown or appropriately qualified conclusions, never silent safe/dangerous defaults.
8. **Validate imported evidence.** Apply applicable structural, compatibility and integrity checks even to artifacts previously generated by SilverGate.
9. **SilverGate is inside the threat model.** Its code, dependencies, builds, releases, updates, packages and distribution require explicit supply-chain protections; the SilverGate name is not a trust anchor.
10. **User authority remains above automation.** Automation cannot manufacture authorization. Future protective operations may use previously authenticated and explicitly approved user policy; inference, AI output or a boolean cannot supply new authority.

### Assets, boundaries, sources and controls

| Protected asset / boundary | Sources or attacker/input classes | Threats mitigated and corresponding controls |
|---|---|---|
| Evidence integrity: Windows queries → collector → immutable snapshot | Windows networking/firewall/CIM, files/signatures, packages, services, targeted registry registrations; ordinary malicious local applications, racing processes, malformed provider values | Preserve original projected values, capture intervals, identities, coverage and errors (sections 3, 4, 6, 11); avoid incorrect joins and disclose source limitations. Immutability/hashes detect changes relative to recorded hashes, not source truth. |
| Import integrity: file boundary → validated model | User-supplied, copied, modified, synthetic, historical and reintroduced SilverGate artifacts; accidental corruption and adversarial import authors | Structural/version/reference/integrity validation, safe serialization, resource limits and explicit diagnostics (sections 3, 14, 15, 17). Never execute imported text or treat its declared producer as authentication. |
| Reasoning integrity: evidence → entities → claims | Every observed value, including apparently reputable metadata or instruction-like text | Fixed versioned normalization/correlation/templates, traceable premises and epistemic states (sections 4–11). Input content cannot redefine templates, predicates, policy or authorization. |
| Report integrity: derived data → HTML/browser | Hostile names, paths, descriptions, markup and embedded JSON values | Context-appropriate escaping, closing-script resistance, restrictive CSP, bundled resources, no external fetches and no execution of source paths/links (section 12). |
| Availability and privacy: collectors/storage/report | Large/deep inputs, excessive inventories, secret-bearing errors, unintended export/egress | Bounded work, cancellation and explicit partial coverage (sections 6, 11, 15); scoped collection, local storage, sanitized diagnostics, explicit exports and no runtime cloud dependency (section 16). |
| Authorization integrity: user intent → operation boundary | Forged approval fields, misleading data, integration output, confused elevated collection or automation | No v0.1 mutation surface; explicit capture context and least privilege (sections 1, 6). Future security-sensitive operations require authenticated user authority; refer to the existing AI roadmap without implementing or expanding it here. |
| SilverGate code/build/distribution integrity | Compromised source repositories, dependencies, build environments, release artifacts, signing/provenance systems, update metadata/infrastructure and distribution channels | Reuse existing module separation, dependency/license review and tests. Section 20 establishes release-authority, provenance, proportional validation and authorization principles. Technical packaging, signing, update and supply-chain mechanisms remain unresolved; no scanner, generalized monitoring or release infrastructure is authorized by this threat model. |
| Future action integrity: approved proposal → execution/result | Substituted action targets/parameters, replayed approvals, execution failures | Outside v0.1. The future Preview → Approve → Enforce → Verify → Roll back design must bind authenticated authorization to the actual action and retain verifiable outcomes. This is a threat obligation, not authorization to build enforcement now. |

### Assumptions and explicit limits

- The deterministic engine relies on its executed code/runtime and the fidelity of captured sources. Malicious applications supplying hostile metadata remain in scope, but an attacker controlling the OS/kernel or underlying evidence provider may falsify observations SilverGate cannot independently verify. Report this source-trust limitation; do not claim comprehensive compromise detection.
- Capture is non-atomic and incomplete over time. Events between snapshots, inaccessible sources and unsupported semantics may remain unseen. No guaranteed malware detection, packet visibility, reachability proof, authorizing-rule reconstruction or causality inference follows from collection.
- Snapshot hashes support integrity checking against the supplied manifest. An attacker able to replace both content and hashes can forge a consistent artifact. Neither hashes nor signatures establish telemetry truth; authenticity and protected history require separately specified trust mechanisms.
- v0.1 does not promise resistance to an attacker with arbitrary write/control over its runtime, code or output storage. Supply-chain and stronger storage/distribution protections remain explicit engineering obligations, not assumed guarantees. Source and dependency identity alone is insufficient.
- Valid experimental/unsupported-platform evidence is not inherently false or invalid. Confidence and evaluability depend on the evidence, schemas, semantics and disclosed coverage. Capture support and evidence compatibility are distinct.
- No active defense, system remediation, probing, enforcement or new AI subsystem is introduced. Existing privacy, bounded processing and deterministic reasoning remain authoritative. Remaining mechanism choices are documented as future work, not silently resolved.

## 19. Product workflow, configuration and evidence lifecycle

### Immediate usefulness and interface consistency

SilverGate should be useful without a configuration/setup ceremony before the first capture. The default live-capture path is **standard-user + read-only**. Before collection, interfaces should eventually be capable of communicating intended collection, evidence destination, relevant limitations and what SilverGate will not do. This communication must remain consistent with no Windows Firewall/network configuration modification, no logging/auditing enabled as a side effect, no upload, no reputation lookup and no telemetry. This does not select a prompt, wizard, confirmation ceremony or future GUI layout.

The core journey is **Capture → Save → Analyze → Explain → Report**. Partial coverage is legitimate: inaccessible, unsupported, failed, timed-out and otherwise unavailable evidence uses the existing coverage/error model. A partial snapshot may be valid and useful; a collector failure does not automatically invalidate the entire capture. Structural/integrity failure remains distinct from partial coverage and must not yield invented or reassuring conclusions.

All interfaces consume the same reasoning results. Presentation may differ, and release capabilities may differ, without silently changing evidentiary meaning or status. No parallel GUI/CLI reasoning implementation is permitted.

### Small configuration model and defaults

Approved conceptual categories are **Privacy, Collection, Display and Advanced**. Do not invent settings to populate them. Configuration may change what SilverGate collects or displays; it must not silently change what evidence means. Legitimate semantics-affecting configuration must be captured in analysis provenance sufficient for explanation/replay. Presentation-only preferences cannot alter underlying claims. Configuration schema, persistence and controls remain unresolved.

Future configuration UX provides **Restore SilverGate Defaults**, with a preview of the settings to change. Restoring defaults must not silently delete or modify original snapshots, saved reports, evidence history, Windows Firewall state or Windows network configuration. This is a future UX requirement, not an instruction to implement reset behavior in v0.1.

### Managed Evidence Library and identity

The Evidence Library is SilverGate's local organization/indexing concept for default captures on user-controlled storage. **SilverGate organizes evidence. The user stores and owns it.** Software writing files does not transfer custody to SilverGate, SilverKnight95 or the maintainer. No project-operated hosting, remote storage, account, database server or automatic synchronization is implied. Its exact path, internal storage layout and indexing implementation remain unresolved. The repository's development `artifacts/` directory does not establish the library's default path. Section 20 clarifies user custody and preservation during uninstall.

Authoritative snapshot identity is immutable and separate from a human-readable display label. A user may eventually label a snapshot “Before Adobe Update” and later rename that label without modifying snapshot identity or captured evidence. Mutable label storage is not prescribed here. Each capture is a distinct artifact; similar source machine, settings or timestamps never authorize overwriting another capture.

Preserve the relationships:

- **Original Snapshot → Analysis → Report**
- **Original Snapshot → Sanitized Export**, when requested

Reports and sanitized copies are derived artifacts, not original evidence. Reanalysis creates new analytical output rather than modifying an original snapshot or historical analysis. Preserve original/derived links and provenance, with meaningful capture/analysis statuses and failures retained rather than erasing previous states. This requirement does not specify a new audit-storage mechanism.

### Evidence Passport

The Evidence Passport is a compact human-readable snapshot identity/provenance summary, not a security/risk score. Its information model supports applicable label, immutable snapshot ID, source machine identity, capture timestamp, OS/build/platform context, capture privilege level, coverage state, schema version, SilverGate/producer version, local-capture/import origin, integrity-validation state, detected modification/integrity information and evidence limitations. Unavailable values remain unknown. Exact UI and field layout are unresolved.

Local capture versus import describes artifact acquisition/custody; it must not overwrite the existing `live_capture`, `historical_transcription` or `synthetic` evidence-origin classification. Importing a historical fixture never turns it into a live capture. The representation of this additional custody context remains to be specified. A valid hash does not establish source truth or complete modification history; retain the limitations in section 18.

### Validation, retention and deliberate deletion

Imports must pass applicable structure, schema/version and integrity checks before acceptance for analysis/library use. Previously generated SilverGate artifacts receive no exemption. All artifact contents remain untrusted data; validation failures cannot silently become reassuring results. No quarantine, repair or import-deduplication mechanism is selected here.

**Evidence remains under user custody until the user explicitly deletes it.** Do not introduce automatic age-based deletion or arbitrary retention expiration. If usage becomes significant, SilverGate may report usage and let the user decide what to retain. Existing section 15 capacity budgets do not authorize deleting old evidence to admit a new capture.

Future deletion UX identifies affected dependent/derived artifacts and requires deliberate confirmation. Evidence must not be artificially undeletable. Exact deletion/dependency semantics, including handling retained dependent artifacts, remain unresolved; do not infer cascading deletion or an automatic cleanup service.

### Explicit exports and sanitized copies

Treat **Export Original Evidence** and **Create Sanitized Copy** as distinct conceptual operations. A sanitized copy is derived; the original remains unchanged. Preserve section 16's explicit user-controlled export, redaction provenance, hashes/manifests and parent references. Future sanitization UX previews removals, transformations and redactions before creation. This update adds no redaction rules and does not select export formats or controls.

### Lifecycle and future comparison

The conceptual lifecycle is **Capture → Identify → Preserve → Validate → Analyze → Explain → Export when requested → Delete when explicitly requested**. It is not a rigid state machine and does not require optional export or deletion. Library management cannot rewrite evidence to simplify lifecycle presentation.

Snapshot comparison is a future capability beyond the initial v0.1 core milestone. Preserve stable snapshot identity and provenance relationships so future before/after reasoning need not mutate history. No semantic comparison rules or diff engine are defined or implemented here. Replaying one snapshot under a new engine remains part of v0.1; comparing resulting claims as a product capability is deferred.

### Acceptance requirements and unresolved details

Core-stage checks, when the corresponding pipeline is implemented:

- Verify the standard-user/read-only default and core Capture → Save → Analyze → Explain → Report journey without mandatory setup or new collection side effects.
- Verify that partial coverage survives saving/analysis/reporting with explicit limitations, separately from structural or integrity rejection.
- Verify interface outputs preserve identical claim meaning and epistemic status for the same analysis; display-only preferences do not change claims. If semantics-affecting configuration exists, replay includes its provenance.
- Verify distinct capture identity and no silent overwrite; reanalysis preserves original evidence and historical analytical output with derived provenance links.
- Validate imports equally regardless of producer or prior SilverGate generation, and distinguish import custody from evidence origin.
- Verify existing storage limits do not automatically delete, expire or replace evidence. A managed local destination must not introduce upload/synchronization or require an account.
- Verify applicable Passport information is evidence-backed, with unknowns and integrity limitations preserved, whenever that summary is exposed; no Passport UI is required by this update.

Deferred feature acceptance, applied only when those features are explicitly implemented: label changes preserve immutable evidence; Restore Defaults previews setting changes and preserves protected artifacts/system state; deletion previews affected dependents and requires deliberate confirmation; sanitized-copy preview matches the explicitly chosen transformations and leaves originals unchanged. These criteria do not authorize implementing the future UX now.

Unresolved: exact library path/layout/backend; configuration settings/schema/persistence; future GUI and Passport presentation; display-label storage; deletion/dependency semantics; detailed export UX and additional sanitization policy; comparison semantics; custody-context representation. No additional product or mechanism decisions are implied. The platform/hardware policy, threat-model principles and AI-governance roadmap remain unchanged.

## 20. Distribution, provenance, updates and user data custody

This section records approved permanent principles and future capabilities. It authorizes no packaging, signing, updating, installation, rollback, release infrastructure, supply-chain tooling, telemetry, remote storage or synchronization implementation. v0.1 remains read-only, deterministic, local-first and replayable, with its existing implementation sequence.

### Canonical distribution authority and SilverKnight95 lineage

Official SilverGate releases must have a clearly identifiable canonical distribution authority and eventually provide cryptographically verifiable release provenance attributable to the **SilverKnight95 project identity**. Project identity and release authenticity must not depend solely on a repository URL or current repository owner. Forks, mirrors, repackaged builds and third-party distributions are not automatically malicious, but using SilverGate code or its name does not make them official.

**Cryptographically verifiable, visually unobtrusive.** SilverKnight95 attribution/provenance should be available for deliberate inspection through build/provenance/about information, signatures, attestations, release metadata or equivalent technical surfaces; it need not dominate ordinary UI or branding. Do not conceal required security, legal, licensing or OS publisher information. Future implementation must account for identity requirements imposed by its selected technology/OS, without assuming how the project identity maps to legally required publisher identity.

No signing technology is selected: Authenticode, certificate infrastructure, Sigstore, GitHub attestations and key-management architecture remain unresolved alternatives, not approved implementation choices.

### Integrity, build provenance and dependencies

**Hashes support integrity verification; hashes do not independently establish release authority.** Publish/use cryptographic hashes where appropriate. A matching digest supports byte-integrity checking against that digest; it does not prove SilverKnight95 authorized the artifact. A checksum file beside a download is not sufficient release authentication.

Official releases should eventually expose traceability across **source revision → dependencies → build environment/process → resulting artifact → release provenance/authentication**. Development builds and official artifacts are distinct; a workstation build is not automatically official. Reproducible builds are desirable where practical, but neither implemented nor mandatory until feasibility and requirements are evaluated.

Every dependency must justify its existence. Future dependency governance accounts for exact/versioned identity where appropriate, provenance, compatible licensing, vulnerability/security maintenance, transitive dependencies and eventual SBOM or equivalent transparency. Do not incorporate source incompatible with SilverGate's chosen license. No SBOM format, scanner or supply-chain service is selected. These obligations do not authorize generalized monitoring infrastructure.

### Updates and authority

**Software update ≠ authorization expansion.** Installation/update approval does not authorize new capabilities, privileges, data access or enforcement authority. A previously read-only installation cannot silently acquire mutation authority. New security-sensitive capabilities or increased authority require applicable explicit user authorization separately from installing software. Update approval is not a reusable general-purpose authorization token.

Treat **checking availability**, **obtaining/downloading**, **approving installation** and **installing** as separate conceptual operations. Future UX may combine steps only while retaining clear authorization boundaries. No silent background self-replacement by default, particularly once security-sensitive capabilities exist. No v0.1 updater is required or authorized here.

Update metadata/responses remain untrusted data under section 18. **Defend the boundary you actually need. Do not manufacture surveillance authority in the name of defending it.** **Security validation must be scoped to the operation being validated.** An update check may collect/transmit only information reasonably necessary for availability, compatibility and relevant security status. Current SilverGate version or architecture/platform context may eventually be justified; exact fields and protocol require explicit future design.

An update check grants no authority to collect/transmit browsing/activity history, unrelated Evidence Library contents, broad application inventories, network-neighbor inventories, behavioral telemetry, persistent hardware fingerprints or unrelated machine evidence. This is not permission to build telemetry. The same proportionality principle applies beyond updates: not everything technically observable has a defined role in the requested operation.

### User ownership and custody

**SilverGate organizes evidence. The user stores and owns it.** **Local-first does not mean SilverGate stores your data. It means SilverGate works with data stored under your control.** SilverGate may organize/index snapshots, reports, provenance and derived artifacts and write files to a user-controlled location selected/defaulted under future product design. This technical behavior neither grants maintainer access nor transfers custody to SilverGate/SilverKnight95.

This architecture provides no evidence hosting, project-operated cloud storage, remote Evidence Library custody, automatic synchronization, backup service, automatic evidence upload or maintainer-operated evidence retention. Normal local operation and evidence storage require no SilverGate or SilverKnight95 account.

Users remain responsible for their storage location/security, backup and synchronization choices, retention and deletion. User-selected OneDrive, Dropbox, NAS/network storage, removable media or other external storage remains the user's custody decision. Preserve the existing warning when a selected location is known to be synchronization-backed; SilverGate may also warn when off-device transfer is reasonably identifiable. Such warnings do not give SilverGate control of or responsibility for the external service. They do not establish official capture/storage compatibility guarantees for every external system.

Tools to organize, validate, sanitize, export or deliberately delete evidence do not transfer custody. Preserve sections 3, 16 and 19's immutable identity, validation, provenance, derived artifacts, explicit exports and user-controlled deletion. No exact library path, layout or storage/indexing mechanism is selected.

### Installation, uninstallation and Windows protections

Installation/uninstallation should be seamless, straightforward, predictable and understandable. Installation must not quietly weaken Windows security, modify Firewall policy outside explicitly approved future functionality, change DNS/network configuration, enable unrelated logging/auditing, add unexplained services/persistence or unrelated browser components, or grant authority beyond what the user understands and authorizes. Communicate security-relevant installation behavior clearly.

Uninstallation distinguishes **software**, **configuration** and **user-owned evidence**. **Uninstalling SilverGate ≠ authorization to destroy the Evidence Library.** Never silently delete evidence on uninstall. If deletion is offered, it requires an explicit understandable user choice with consequences communicated beforehand, consistent with the existing deliberate-deletion principles. Uninstall must not imply that SilverGate/SilverKnight95 retains a remote copy. Exact installer, filesystem layout and uninstall behavior beyond these principles remain unresolved.

**SilverGate must not require users to weaken Windows security in order to trust SilverGate.** Documentation/installation must not advise disabling or broadly weakening Defender, SmartScreen, UAC, certificate validation or comparable controls merely to install/run SilverGate. Address legitimate objections through the underlying packaging, signing, compatibility or distribution problem instead of normalizing bypasses. No bypass procedure is specified or authorized.

### Future rollback and unresolved mechanisms

Preserve software rollback/downgrade as a future capability, distinct from future firewall-change rollback. Its design must account for older known-vulnerable or incompatible releases; version regression is not irrelevant. User authority remains controlling within whatever explicit security boundaries are later approved. Do not invent a downgrade prohibition, override, rollback engine or mechanics now.

Explicitly unresolved:

- Exact signing technology; certificate/key ownership and custody; SilverKnight95's relationship to legally required publisher identity.
- Build/release infrastructure; reproducible-build requirements; SBOM format/tooling; installer/package technology.
- Update transport/protocol, metadata schema, privacy fields and cadence.
- Rollback mechanics and vulnerable-version downgrade policy.
- Evidence Library filesystem layout, default user-controlled location and indexing/storage implementation.
- Configuration behavior and evidence deletion/dependency semantics beyond approved principles.

### Future acceptance requirements and documentation checks

Apply these checks when corresponding future capabilities are explicitly implemented; they do not expand the v0.1 sequence:

- Verify official-release authority is not established by name, repository owner/URL or matching checksum alone; development/third-party artifacts are distinguished without unsupported maliciousness judgments.
- Verify deliberately inspectable SilverKnight95 release provenance and source-to-artifact traceability, without hiding required publisher/legal/security information or claiming unimplemented reproducibility.
- Verify justified dependencies and transparency/maintenance/licensing coverage without presupposing a scanner, SBOM format or service.
- Verify update approval cannot expand authority or act as a general authorization token; discovery/download/approval/installation boundaries remain clear and no default silent replacement occurs.
- Validate hostile update input and operation-scoped data handling without unrelated evidence access, surveillance or telemetry.
- Verify library descriptions and operations preserve user custody, no project hosting/access/backup claims, no account requirement, and no automatic evidence transfer. Preserve warnings for known synchronization-backed locations.
- Verify installation communicates security-relevant behavior, does not quietly change unrelated security/network state, and never requires weakening Windows protections to establish trust.
- Verify uninstall preserves evidence unless the user explicitly chooses deletion with understood consequences; it does not imply project retention of a remote copy.
- Verify future rollback considers older-version vulnerabilities/compatibility under an explicitly approved policy rather than treating version regression as immaterial.

Documentation checks must retain the unresolved-mechanism list, existing threat/privacy boundaries and unchanged AI-governance roadmap. No updater, installer implementation, signing infrastructure, release service, telemetry, project hosting/synchronization, background monitoring, supply-chain scanner, rollback engine, enforcement or new privileged component is added to v0.1.

## 21. Privilege and elevation architecture

This section consolidates the existing least-privilege, authority and coverage rules into the approved future elevation direction. It is documentation only: no elevated helper, IPC, Windows service, privilege broker, UAC integration, enforcement or additional collector functionality is required by this update.

### Privilege invariants

- **Elevation expands visibility, not authority.**
- **Declining elevation reduces coverage, not user authority.**
- **Privilege affects evidence availability, not evidentiary authority.**
- **Elevation approval is scoped, temporary, and non-transferable.**
- **Previous elevation ≠ future authorization.**
- **Read elevation ≠ modification authority.**
- **The privileged boundary is never a general-purpose command proxy.**
- **Standard-user operation remains a complete supported SilverGate workflow.**

These apply with the existing principles that user authority remains above automation and software updates do not expand authorization. Authorization is tied to the actual approved operation, not inferred from unrelated approval, analysis results or a Windows token's technical capabilities.

### Standard-user workflow and optional elevation

The primary application, analysis engine, reports, Evidence Library interaction and future ordinary GUI/CLI operation should remain standard-user processes wherever practical. The complete v0.1 path remains **Standard user → Capture → Save → Analyze → Explain → Report**. Additional elevated evidence may improve coverage but is not a prerequisite for core usefulness. Do not redesign the product around running SilverGate as Administrator.

Before requesting elevation, future UX explains why elevated read access is useful and which evidence remains unavailable without it. Continuing without optional elevation is supported when safe and technically possible. Declining is not an error or user misconfiguration; represent unavailable evidence using existing coverage semantics without inventing a new failure state.

No silent elevation, UAC bypass, consent-circumventing token manipulation, weakened security controls or equivalent shortcuts. Requests must correspond to understandable user-requested operations. Normal Windows security boundaries remain authoritative.

### Narrow, temporary collection boundary

Where evidence genuinely requires elevated reads, the preferred future direction is:

**Standard-user SilverGate → explicit elevated collection request → read-only elevated collector → evidence returned → elevated collector terminates.**

This favors narrowly scoped collection over elevating the whole application; it neither decides that a helper is necessary nor selects process topology. Elevation is temporary and operation-bound. One approved operation establishes no indefinite Administrator access or permission for later/unrelated operations. Avoid persistent elevated processes unless separately approved future architecture demonstrates a compelling requirement; exact lifetime details remain unresolved.

Future privileged operations must be explicitly defined/versioned capabilities with bounded inputs and outputs. Standard-user components cannot submit arbitrary command strings, scripts or equivalent unrestricted execution to the elevated component. No final operation identifiers or IPC schema are established here.

Elevated observational collection remains read-only even when its token could write. Approval does not authorize firewall rules/policy changes, network configuration changes, service or registry modification, enabling auditing/logging, enforcement, or unrelated privileged operations. The boundary must not become an implicit future write channel.

### Evidence quality, coverage and minimization

Privilege level is provenance/context, not an epistemic endorsement: elevated evidence is not inherently more truthful, authoritative, safe or relevant. Preserve fact/inference/hypothesis/unknown distinctions and the Evidence Passport's applicable privilege context without inventing unavailable provenance.

**Elevated collection still fails honest.** Successful elevation does not establish complete coverage. Every collector reports its actual existing outcome, including partial, inaccessible, unsupported, failed, timed out or cancelled. Never assume evidence must have been available merely because the process was elevated. Preserve section 6/11 result and coverage contracts.

Not everything available to observe needs to be observed. Elevated reads gather evidence for the defined collector/request, not everything Administrator access makes available. Security validation remains scoped to the operation being validated; elevation grants no surveillance authority.

### Validate both sides of the boundary

Future standard/elevated communication must establish that both sides are communicating with the expected SilverGate component and authorized operation. Names, executable filenames, window titles and unverified identity assertions are insufficient alone. Inputs entering the elevated boundary remain untrusted until validated; returned evidence/results undergo applicable structure, provenance and integrity validation under sections 3 and 18.

Exact authentication, Windows identity/token checks, operation-binding representation and IPC remain unresolved. No named pipes, RPC, sockets, COM or other technology is chosen.

### Capability separation and future authority

Standard evidence reads and elevated evidence reads are conceptually distinct from future security-change proposals and execution. These are separation concepts, not final capability identifiers or implementation of AI governance. No observational permission, elevated-read permission, update approval or analytical conclusion silently converts to modification authority.

Future modification/enforcement authority must be independently designed, scoped, authenticated, explicitly approved, auditable and separable from observational elevation. This update does not design enforcement or authorize future writes through an elevated collector.

### Unresolved decisions

Preserve as unresolved: exact elevated process topology; whether a helper is ultimately required; executable/component boundaries; IPC technology; component authentication; authorization-token/operation-binding representation; elevated collector lifetime details; Windows identity/token validation; helper installation implications; future write/enforcement privilege architecture; final capability identifiers. No implementation assumption fills these gaps.

### Acceptance requirements and scope checks

For the existing core workflow, verify standard-user capture through reporting remains viable with honest partial coverage, no automatic elevation and no elevated prerequisite. Analysis and reports must not promote evidence credibility based on capture privilege.

When future optional elevated collection is explicitly implemented, verify:

- Explanation precedes the request; declining permits the supported standard-user path without being labeled an error or misconfiguration.
- Approval is limited to the requested operation and cannot be reused for unrelated/later privileged activity; collection is temporary under its approved lifecycle.
- No arbitrary command/script proxy, UAC bypass, mutation capability or unrelated collection is exposed.
- Both boundary participants and the authorized operation are validated; hostile request/result content cannot acquire authority through identity labels.
- Elevated success still preserves actual partial/failure/cancellation outcomes and source-trust limitations.
- Returned evidence undergoes applicable validation; increased access never implies authorization expansion or increased epistemic authority.

These criteria do not add a helper, service, broker, IPC subsystem, AI privilege handling, additional collector, persistence, mutation or enforcement to v0.1. The existing implementation sequence, platform/support policy and AI-governance roadmap remain unchanged.

## 22. Design-stage intent and planning

This section records the consolidated design update following specification v0.1.7. SilverGate is currently being designed and planned. Discussion of desired behavior is not an imminent production decision, and this update authorizes no implementation. The established five-step sequence remains the implementation plan rather than an instruction to start it in this documentation pass.

### Preserve design intent through implementation

The intended progression is **Define desired behavior → preserve the design intent → implement → make necessary implementation-level refinements**. Legal, privacy, security and technical concerns should inform design, not automatically discard a desired feature merely because it adds complexity. During a separately authorized implementation, minor necessary legal/security/privacy refinements may be made without unnecessarily overturning the design or violating existing approved boundaries. A genuine incompatibility requiring substantive design change must return to the user for a decision, not be silently rewritten.

**Candidate wording, not an approved invariant:** “Design intent ≠ implementation authorization.” The explicit no-implementation instruction for this update applies independently of whether that candidate is later approved. Do not promote the candidate into the permanent-invariant lists.

### Future terms and acceptance planning

SilverGate will eventually need terms appropriate to its distribution model and selected software license. The current design intent is reasonable liability protection with clear, upfront information rather than obscured important terms. This records product intent, not a legal conclusion or drafted terms.

The acceptance concept being explored is **Terms presented → user accepts → one-time acceptance receipt transmitted → receipt pathway is no longer used for that purpose**. The purpose of the receipt is to document acceptance, not telemetry or an ongoing relationship with SilverKnight95. The accompanying notice should plainly describe what is transmitted and why. The concept does not transfer Evidence Library custody or turn SilverGate into a cloud service.

Actual legal wording, interaction with the chosen license, receipt fields, transport, receipt storage and implementation remain unresolved and require validation as the design approaches implementation. No receiver, account, delivery/retry mechanism, persistence scheme, failure policy or acceptance gate is selected here. The desired concept is preserved; it is not implemented or treated as an exception to v0.1's current no-upload/no-telemetry behavior. Any eventual implementation must reconcile its bounded receipt transmission with existing privacy/authority commitments; a substantive incompatibility returns to the user instead of silently expanding scope or deleting the concept.

**Candidate wording, not a frozen invariant:** “Acceptance of Terms ≠ authorization of capabilities.” Preserve its candidate status pending approval. Existing approved rules already require separately applicable authorization for capabilities; documenting this candidate does not weaken or replace them.

### AI-governance relationship

The [AI governance roadmap](SilverGate-AI-governance-roadmap.md#investigation-and-pending-adjudication) now records investigation assistance by other AI integrations with no governance marks, clearly advisory opinions, non-authoritative AI consensus, authenticated user adjudication and user notification when review is pending. Existing Critical containment and alignment/restriction rules remain authoritative. Context compression that merges user statements and AI inferences is recorded as an observed design consideration, not an adjudicated rule or new violation category. Neither addition creates an AI dependency in the deterministic core or authorizes governance implementation.

### Adoption and visibility

Public adoption is unknown. Marketing/visibility may eventually help attract users but is not the immediate design driver. The immediate standard is that the user is comfortable with SilverGate's design and behavior before asking others to trust or use it. Marketing follows sufficient confidence; low or uncertain adoption does not require premature architecture changes. No marketing system, campaign, metric or release gate is specified.

### Documentation checks and unresolved decisions

Verify that normative governance requirements, exploratory acceptance intent, observed design considerations and candidate principles remain distinguishable. Do not present receipt planning as implemented transmission, context-compression concerns as an upheld violation, or candidate wording as an approved invariant. Future governance checks are recorded in the roadmap; no runtime test or feature is added by this section.

Unresolved details include the meaning of no governance marks for investigation eligibility, notification delivery details, candidate-principle approval, terms/legal/license validation and receipt fields/transport/storage/implementation. The existing Observe → Explain → Preview → Approve → Enforce → Verify → Roll back model, v0.1 read-only scope, custody, privilege, supply-chain, platform/hardware, common GUI/CLI engine, deterministic evidence model and AI-independent core remain unchanged.

## Implementation sequence

1. Materialize schemas, historical/synthetic fixtures and contract tests.
2. Implement offline normalization, correlation and explanation against fixtures.
3. Implement bounded read-only collectors and serialization.
4. Produce the local report and evidence navigation.
5. Run a manual AaronAura capture, test coverage/performance, and replay it through the engine.

The first milestone succeeds when SilverGate can explain permissions and observed behavior with traceable evidence, preserve unknowns and coverage gaps, and pass the six reasoning regressions. Enforcement design begins only after that milestone, in a separately scoped release.
