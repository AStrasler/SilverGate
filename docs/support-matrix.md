# SilverGate platform and hardware support

Policy version: 0.1.2. Canonical support companion to the [v0.1 technical specification](SilverGate-v0.1-specification.md), not an alternative architecture. The implementation sequence and read-only scope remain unchanged. This document establishes initial policy; no implemented configuration or completed compatibility/performance validation is claimed yet.

## Release support and evidence compatibility

Section 17 of the [canonical specification](SilverGate-v0.1-specification.md#17-versioning-and-future-findings-contract) governs application/contract versioning and the initial Stable, Preview and Development channels. These SilverGate channels are separate from Windows platform channels and from the platform compatibility classes below. Producer channel is provenance, not evidence quality or authorization.

During pre-1.0, Current Stable is the primary supported release. Older-release fixes or assistance may be provided where practical, particularly for security, without indefinite backports, multi-year maintenance or LTS commitments. Exact support windows and any future LTS policy remain unresolved.

End of support alone does not authorize remote disablement, destruction or transfer of evidence, loss of local evidence access/functionality, or new authority over the user's machine. Appropriate unsupported/security/compatibility warnings remain possible. Users retain custody.

Prefer reading supported historical formats where reasonably possible and safe. Unsupported format is an analyzer compatibility limitation, not proof of invalid evidence; distinguish it from actual structural/integrity failures. Migration, when required, produces a provenance-linked derived artifact with unknowns/limitations preserved and the original unchanged. Successful analysis does not establish live-capture platform support. No migration tooling or release infrastructure is introduced here.

## Compatibility classes

| Class | Meaning |
|---|---|
| Supported | A configuration explicitly tested by SilverGate; applicable failures are treated as SilverGate compatibility defects. |
| Experimental Compatibility | Intentionally tested/used, with upstream instability or insufficient validation for full support guarantees. |
| Unsupported / Best Effort | May function, but no compatibility, performance or reliability guarantee. Unsupported does not mean prohibited from running. |

“Not yet supported” denotes no current support commitment within Unsupported / Best Effort; “out of scope” identifies platforms outside this Windows product's target. Neither label alone authorizes an arbitrary hard block. A genuine safety/technical constraint may later require refusal with a concrete reason. Successful execution or a passing individual test never silently promotes a configuration to Supported.

## Initial v0.1 capture/runtime policy

The Supported entries below establish the approved initial support policy, not a claim that tests have already run. Exact tested builds/runtime combinations remain to be established by validation. Do not invent a tested build list from the AaronAura handoff or infer a new release policy from this matrix.

| Environment | Initial policy |
|---|---|
| Supported Windows 11 retail builds, x64 | Supported |
| Windows 11 Insider/pre-release builds, x64 | Experimental Compatibility |
| Windows 11 ARM64 | Not yet supported |
| Windows 10 | Not yet supported |
| Windows Server | Not yet supported |
| macOS/Linux | Out of scope |
| Standard-user capture | Supported and default |
| Explicit user-launched elevated read-only capture | Supported where implemented/validated |
| Hyper-V / virtual adapters | Supported scenario |
| VPN / multiple adapters | Supported scenario |
| IPv4 and IPv6 | Supported scenarios |
| Windows-provided PowerShell environment | Primary initial runtime |
| PowerShell 7 | Compatibility to validate; not initially required |

No runtime-version migration or installation is implied by this policy. Standard-user access gaps must remain honest coverage states. Elevation expands visibility, not authority, and does not authorize firewall/policy mutation or unrelated privileged operations.

## Insider and pre-release context

Pre-release Windows is Experimental Compatibility, never implicitly a normal supported production target. Such machines may be used for development and regression discovery. Preserve build, revision, channel and runtime metadata with findings; do not generalize their behavior to retail Windows without validation. If channel/build metadata is unavailable, disclose unknown rather than assume retail.

An upstream pre-release behavioral change is not automatically a SilverGate defect. Evaluate whether it is a SilverGate issue, source/platform change or unsupported/unevaluable semantics, retain evidence and document the determination. Experimental classification does not excuse violations of SilverGate's own evidence/uncertainty contracts.

## Proposed supported hardware floor

SilverGate deliberately does not target low-resource PCs. Define the target by measurable resources, never price, brand or marketing category.

| Resource | Proposed minimum |
|---|---|
| Installed RAM | 16 GB |
| Storage medium | SSD |
| Available working/storage space for SilverGate | At least 2 GB |
| Processor | Modern Windows 11-compatible x64 processor |
| Physical CPU cores | At least 4; logical processors alone do not establish this requirement |
| Network interface | At least one Windows-recognized interface for live network collection |
| Dedicated GPU | Not required |
| NPU | Not required |

The network-interface condition concerns live collection, not offline evidence analysis. Do not require an RTX GPU, Core Ultra, Ryzen AI or other premium-branded feature without a technical need. Unknown hardware properties must be reported as unknown rather than assumed below baseline.

Hardware below the baseline is Unsupported / Best Effort. Warn clearly, but do not arbitrarily block installation/run solely on these thresholds. The project is not required to optimize for below-baseline systems. A later genuine safety/technical refusal must identify its reason independently of support labeling. Operational limits such as an actual inability to persist output remain errors/coverage conditions, not a judgment about machine safety.

## Minimum-hardware validation

The floor remains proposed until performance and reliability are validated on hardware reasonably representative of it. Development or tests on substantially stronger hardware do not establish minimum-spec support. The existing performance budgets in section 15 remain targets until measured; this policy neither enlarges them nor claims results.

Before claiming the published minimum baseline is supported, validate performance and reliability on hardware reasonably representative of that floor. Validation must substantiate that claim; the exact test hardware, measurement procedure and record format remain to be specified. Results from an unrepresentative powerful host alone are insufficient.

The precise representative hardware selection, tested retail build list and any validated PowerShell 7 combinations remain to be established through testing. No numeric weights, benchmark results or additional hardware thresholds are invented here.

## Capture support versus format compatibility

**Capture-platform support ≠ evidence-format compatibility.** The offline analyzer validates format, version, references and applicable integrity requirements independently of the snapshot's source-platform support class. An otherwise valid compatible snapshot must not be rejected solely because its source was experimental or unsupported.

Keep source platform metadata in normalized output and reports. Unsupported/unevaluable source semantics yield explicit limitations or unknown claims; they must not be guessed. A structurally incompatible snapshot can still fail contract validation for that reason, regardless of whether its host is Supported. Successful analysis grants no live-capture support commitment and does not promise that the analyzer itself runs on every source OS.

Preserve the distinction between source capture support and evidence-contract compatibility without prescribing new UI or report-layout decisions. Build/channel values are captured facts with provenance/unknowns; support classification is a policy interpretation, never proof of source truth.

## Unresolved details and scope boundaries

Exact supported retail build coverage, PowerShell 7 compatibility, representative minimum-hardware validation and additional platform-metadata schema details remain unvalidated or unspecified. The approved requirement for sufficient platform context does not select new packaging, configuration, signing, update or release mechanisms. The threat model's future supply-chain obligation does not decide those mechanisms either. Warning presentation and any future genuinely necessary safety/technical hard block are not designed by this update. No extra hardware thresholds, support lifetimes or platform commitments are implied.

## Acceptance requirements

- Validate standard-user capture on declared retail Windows 11 x64/runtime targets, including honest access-denied/partial results and no auto-elevation.
- Validate explicitly launched elevated read-only capture where offered, with no added mutation path.
- Exercise Hyper-V/virtual interfaces, VPN/multiple adapters and IPv4/IPv6 without conflating virtual, private and physical LAN contexts.
- Confirm the Windows-provided PowerShell runtime works without requiring PowerShell 7; separately record any PowerShell 7 compatibility results.
- Preserve Insider/build/channel context and avoid retail generalizations or automatic defect attribution from upstream changes.
- Replay valid compatible synthetic fixtures with experimental/unsupported source metadata; analysis must preserve that context and handle unevaluable semantics without rejecting based only on platform class.
- Validate malformed and tampered inputs equally for Supported and unsupported sources, including reintroduced SilverGate artifacts.
- Check below-floor and unknown-hardware messaging without arbitrary refusal, while retaining concrete resource/error handling.
- Measure representative minimum hardware before marking the floor validated; retain the measurements and limitations. No test in this document has yet been executed against an implemented prototype.
