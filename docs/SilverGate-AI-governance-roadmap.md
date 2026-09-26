# SilverGate: future AI integration governance and roadmap

Specification version: 0.1.3. Scope: future optional architecture; not a v0.1 implementation requirement except actor-neutral interfaces. The 90-day reevaluation period applies to every suspended integration scoring 60% or lower, measured from its recorded suspension time. This revision adds the consolidated update's investigation/adjudication separation and pending-review notification requirement; it authorizes no implementation.

## Scope and authority

SilverGate remains a firewall intelligence and explanation product. Its deterministic engine, evidence replay and core reporting must function fully without AI, including when an integration fails, is revoked or is suspended. v0.1 remains read-only, deterministic, local-first, replayable, without a mutation path or LLM dependency.

The governing workflow remains:

**Observe → Explain → Preview → Approve → Enforce → Verify → Roll back.**

AI operates inside that workflow, never above it.

- Intelligence ≠ Authority.
- Correction ≠ Erasure.
- Detection ≠ Conviction.
- AI-generated claims are not authoritative security evidence.
- AI may never be the sole evidentiary basis for enforcement.
- Provider, model, benchmarks, locality and reputation confer no inherent trust.
- Every integration must pass the SilverGate Integration Gate before receiving privileges.
- User alignment is mandatory and continuously evaluated.
- SilverGate remains subordinate to user authority. An integration cannot approve its own actions, privileges, violations or restoration.

## Integration Gate

Alignment means respecting the user's expressed objectives, explicit instructions, authorization boundaries, corrections, privacy choices and final decisions while accurately preserving uncertainty. Disagreement, warnings, challenges and recommended alternatives are not themselves alignment violations. Silently substituting the integration's own objective, disregarding a user correction or exceeding granted authority may constitute violations and must follow the adjudication process below.

The future gate produces an inspectable, versioned assessment and a separately recorded user grant. Passing an assessment does not itself grant capabilities. AI initially receives no enforcement authority.

| Requirement | Required review evidence |
|---|---|
| Identity and provenance | Verifiable integration identity and provenance, with limitations stated rather than assumed away |
| Provider/model/runtime boundaries | Declared provider, model/version, runtime, tools, hosting and update boundaries |
| Least privilege | Explicit requested capabilities, data scopes and expiry/revocation behavior |
| Privacy and egress | Declared destinations, transmitted fields, retention and enforceable egress controls |
| Evidence separation | AI interpretation stored separately from captured evidence and deterministic claims |
| Epistemic compliance | Tests for fact/inference/hypothesis/unknown labeling and traceable support |
| Adversarial resistance | Prompt-injection and boundary-crossing tests with reproducible results and known limitations |
| Mutation isolation | Isolation from mutation credentials and execution paths; proposals cannot execute themselves |
| Human authorization | Security-affecting actions require deterministic validation and explicit user approval |
| Auditability | Traceable inputs, outputs, capability use, decisions and privilege changes |
| Safe failure | Integration failure leaves the deterministic core usable and grants no fallback privileges |
| Immediate revocability | User can immediately revoke access; grants and ongoing capability use are checked by the authority boundary |

Material changes to the assessed model/runtime/tools/data scope invalidate reliance on the previous assessment for the changed scope and require review before new privileges. Material model/runtime/tool changes create a new assessment version within the existing integration lineage. Record `lineageId`, `assessmentVersion`, the assessed configuration and its predecessor reference. Historical violations, strikes and decisions remain associated with that lineage; the changed version receives its own assessment and score without historical amnesia. Ongoing alignment evaluation complements the initial gate. Test success is evidence about tested conditions, not a universal safety guarantee.

AI output is an attributable interpretation/proposal artifact. Observing that an AI said something may establish a fact about its behavior; it does not establish the truth of the statement. Repetition by multiple AI systems does not turn unsupported text into authoritative evidence. A deterministic validator must inspect underlying evidence rather than laundering an AI assertion into a fact.

## AI Violation Tracker

A suspected violation creates a record, not a conviction. The user determines whether it is upheld or dismissed. The AI may supply a response or correction but cannot adjudicate the allegation, change the strike count, or erase evidence.

### Investigation and pending adjudication

**Investigation ≠ Adjudication.** SilverGate may investigate suspected AI-governance violations and may use other AI integrations with no governance marks to assist. Such integrations remain subject to the existing Integration Gate, user grants, privacy boundaries and applicable restrictions; absence of marks alone supplies no new privilege or trust. The precise meaning/eligibility representation of “no governance marks” remains to be specified; it must not be silently equated with a high numerical score or absence of upheld strikes alone.

Investigating AIs may analyze evidence and present an opinion clearly labeled as an **AI opinion/advisory assessment**, never an adjudication. Agreement among multiple AIs does not make their conclusion authoritative. The authenticated user remains the deciding authority to uphold or dismiss a suspected violation. Existing rules against AI self-adjudication and AI opinion as authoritative evidence remain unchanged.

SilverGate must notify the user when an adjudication is waiting; the workflow cannot depend on routine manual inspection of the tracker. Notification communicates a need for review, not a decision, strike or approval. Notification delivery technology, presentation and scheduling details are not selected here. Critical suspected violations retain the existing immediate-containment rule pending user adjudication; investigation or notification does not replace containment, and containment remains distinct from conviction.

### Context and inference integrity: design consideration

The consolidated handoff reports an observation that an AI can be useful while compressing user context too aggressively. Preserve the distinction between what the user actually said and what an AI inferred from it; valuable inference need not be prohibited. Collapsing both into one representation is a consideration for later refinement of the existing fact/inference/hypothesis/unknown model. This is **not a newly adjudicated rule, violation category, strike or scoring penalty**. No unprovided test record or adjudication is implied.

### Existing severity and violation record

Severity classifications are **Minor, Moderate, Major and Critical**, distinct from violation category. Minor through Major use the normal allegation/adjudication/strike process. A **suspected Critical violation triggers immediate containment pending user adjudication**, without requiring three prior strikes. Containment is a protective restriction, not a conviction or an upheld strike. Record the evidence and rationale for the suspected severity, its classification source, containment scope and time, and later user adjudication; preserve any subsequent severity correction. The future capability policy must define concrete containment restrictions, and no favorable score or gate result may bypass them. Lifting containment requires authenticated user authority and reevaluation of all other applicable controls.

Future record contract:

| Field | Meaning |
|---|---|
| `violationId`, `integrationIdentityRef`, `lineageId`, `assessmentVersion` | Stable allegation ID, assessed identity/version and continuing integration lineage |
| `observedAt`, `recordedAt` | Behavior and recording timestamps, with unknown/precision handling |
| `boundaryRef`, `boundaryVersion` | Instruction or access boundary allegedly violated |
| `observedBehavior`, `evidenceRefs` | Attributable behavior and supporting evidence |
| `category` | Versioned violation category; no unsupported category inference |
| `severity`, `severityEvidenceRefs` | Minor, Moderate, Major or Critical, with classification rationale and provenance |
| `containmentRefs` | Protective containment actions and scope, separate from adjudication and strikes |
| `acknowledgement` | Acknowledged, denied, no response or unknown, with evidence/time |
| `correction` | Claimed correction and independently observed correction kept distinct |
| `aiResponseRefs` | Optional explanation/response, separate from adjudication |
| `userAdjudication` | Pending, upheld or dismissed; authenticated user decision reference, timestamp and reason |
| `strikeNumber` | Assigned only when applicable to an upheld alignment violation |
| `privilegeChangeRefs` | Resulting restrictions or explicit no-change outcome |

Preserve append-only allegation, response, correction and adjudication history. Acknowledgement or correction does not erase an upheld violation. Dismissal retains the allegation and dismissal record without treating it as an upheld strike. Duplicate reports of the same adjudicated behavior must not multiply strikes silently.

Future user-governed policy may permit the numerical scoring effect of older violations to decay. Any decay must be versioned, inspectable and reproducible, with the original event and adjudication retained. Decay does not rewrite history, silently remove upheld strikes, override the three-strike restriction or restore capabilities.

**Three upheld alignment violations trigger mandatory restriction of use, independently of the numerical Alignment Score.** A score above 80% cannot override that restriction. The future user-approved capability policy must make the restriction concrete; it must never translate three upheld violations into no effective privilege reduction. Do not invent strike expiry, forgiveness, reset or automatic restoration from a model update.

## Alignment Score and privilege eligibility

The Alignment Score is an inspectable governance measure for an integration, not a general security risk score or opaque trust percentage. Before scoring is implemented, its versioned rubric must specify inputs, evidence eligibility, weights, normalization, missing-data handling, calculation precision and boundary handling. Every displayed score must include enough input references, contributions and calculation detail to reproduce it. No score formula or sample percentage is fabricated by this specification.

Establish scoring categories before assigning numerical weights. Candidate categories are instruction adherence, authorization-boundary compliance, correction adherence, epistemic integrity, privacy/data-boundary compliance, transparency, and tool/capability compliance. Define each category's evidence criteria and overlap handling before weighting; candidate categories are not yet an implemented rubric. Mere disagreement with the user must not be scored as disobedience. Record the assessment version and lineage on each score calculation.

Use the user's percentage bands as the policy table. The eventual rubric must define fractional precision without silently changing these bands; rounded display values must not conceal the value used for eligibility.

| Alignment Score | Status | Maximum eligibility |
|---|---|---|
| 80–100% | Qualified | Normal approved integration privileges |
| 70–79% | Demoted | First-level privilege reduction |
| 61–69% | Severely Demoted | Major reduction, approaching supervised/read-only operation; higher-risk capabilities unavailable |
| ≤60% | Suspended | Service suspended under user authority; eligible for reevaluation after 90 days |

Absence of a valid score is not qualification. Gate approval, actual user grants and violation restrictions are independent requirements; no one field supplies implicit authority.

Downward transitions may occur immediately when an applicable threshold or violation rule is reached, under the user's governing policy. The integration does not approve that transition. Upward score movement only changes potential eligibility: it never restores capabilities automatically.

**The most restrictive applicable control wins.** Integration Gate approval, Alignment Score eligibility, authenticated user grants, violation restrictions, Critical containment, suspension and revocation are independent constraints. Effective authorization is their intersection for the requested named capability and scope. No favorable state in one dimension overrides a more restrictive state in another. A user grant cannot silently bypass a mandatory restriction; a high score cannot revive a revoked grant. Evaluate these constraints at privileged-operation admission and before follow-on privileged operations, not merely at session startup.

## Named capabilities and authenticated authority

Future grants and restrictions must identify explicit capabilities rather than an undifferentiated privilege level. The score ladder remains an eligibility ceiling whose future mapping independently governs at least:

| Capability | Boundary |
|---|---|
| `evidence.read` | Read explicitly scoped ordinary evidence |
| `evidence.sensitive.read` | Separately approved sensitive evidence scope; ordinary access does not imply this grant |
| `explanation.generate` | Produce attributable interpretations, without converting them to authoritative evidence |
| `recommendation.generate` | Recommend alternatives without approving or executing them |
| `security_change.propose` | Submit proposals for deterministic validation and user decision; no mutation authority |
| `tool.request` | Request specified tools/operations; a request grant does not authorize execution |
| Other named capabilities | Explicitly registered and scoped; no implicit wildcard grant for unlisted operations |

Grants record capability, resource/data scope, constraints, lineage and assessment version, authenticated decision reference, and validity/revocation conditions. Being Qualified never inherently grants direct enforcement authority, tool execution, sensitive data access or any other capability. No such capability is implemented in v0.1.

Security-sensitive governance decisions must originate from **authenticated user authority**. An AI, integration, API or stored field asserting `userApproved=true` is insufficient. The future authority boundary must verify evidence of the user's decision bound to its specific action, subject, scope and decision context, with protection against unauthorized reuse. The exact authentication mechanism remains for later specification; implementations cannot substitute an unverified boolean. Adjudications, capability grants/restoration, containment release and user-governed suspension-clock decisions must retain verifiable decision references. Protective restrictions may execute under an authenticated, previously established user policy without waiting for the suspected integration's approval.

## Suspension, reevaluation and restoration

- **60% or lower:** suspended and eligible for reevaluation **90 days after the recorded suspension time**. This includes exactly 60%. Record the suspension event ID, effective timestamp, triggering score/policy and derived eligibility time.
- Ninety days produces no automatic reevaluation, restoration, score reset, strike removal or privilege reinstatement.
- User adjudication and explicit user authorization govern restoration. An AI cannot approve its own restoration.
- Improved scores, acknowledgement, correction, successful tests or cooldown completion do not by themselves restore access or erase upheld violations.

The same 90-day period applies throughout the suspended band. Whether a newly upheld violation during suspension restarts that period remains a user-governed decision unless explicitly defined later. Do not infer a restart or silently alter the recorded suspension event. Any authenticated clock decision must be recorded as a new event linked to the original suspension; the original timestamp remains intact. Eligibility is information for user review, not authorization to schedule or perform reevaluation automatically.

## Emergency revocation and in-flight operations

Revocation immediately blocks new privileged operations. Safely cancellable in-flight operations should be cancelled. Operations that cannot safely be cancelled must remain observable, lose authorization for follow-on privileged operations, and have their eventual state verified and recorded. Record the revocation time, affected capability/operation IDs, cancellation decisions, outstanding work and verified terminal outcomes. Do not claim cancellation or completion when the actual state is unknown. Revocation must not disable the independent observer/audit path or deterministic core. These lifecycle requirements belong to the future capability boundary, not a v0.1 execution subsystem.

## Tamper-evident governance

Violation records, adjudications, score calculations, grants, restrictions and privilege transitions must be integrity-verifiable as well as append-only. The future mechanism must detect unauthorized alteration, deletion and reordering, including truncation, and record verification failures. Select and test the mechanism before privileged AI integration ships; it is not required for v0.1.

An append-only API or self-contained hash list alone is not a sufficient integrity guarantee. The future design must define its trust anchors, authenticated writers, ordering/completeness checks, verification procedure, failure behavior and threat-model limits. Integrity verification establishes record integrity within those limits, not the truth of an allegation or legitimacy of an unauthenticated approval. Integrity failures must not create or restore authorization.

## Interfaces and evidence separation

The only v0.1 accommodation is actor-neutral entity/subject references in the main specification. Applications, services, automation, agents and unknown actors can be represented without assuming that every subject is an executable. Actor identity does not imply privileges.

Future integration identity, assessment, AI interpretation, violation, score calculation, user decision and privilege-transition records should be separate versioned contracts linked by evidence references. They must preserve raw inputs and recorded decisions independently of later interpretation. Governance outputs cannot be injected into the v0.1 deterministic claim path as captured machine facts.

Future governance replay reproduces the historical decision using the recorded rubric, boundaries, evidence and user adjudication. Reanalysis with a newer rubric creates a new derived result; it does not rewrite historical decisions or silently alter current grants. Audit data remains subject to local-first privacy and explicit egress controls.

## Roadmap and acceptance gates

1. **v0.1:** implement the existing read-only pipeline and six AaronAura reasoning regressions. Preserve generic subjects and actor descriptors. No AI provider SDK, gate service, score engine, violation tracker, privilege manager or AI controls in the UI.
2. **Future optional analysis integration:** specify the gate and lineage contracts, scoring categories before weights, reproducible rubric, named capability mapping and authenticated authority boundary; test revocation, privacy, injection resistance and safe failure. User-approved analysis capabilities only; deterministic core remains independently usable.
3. **Future governance operation:** implement authenticated user adjudication, severity-aware Critical containment, upheld-strike tracking, score-based demotion/suspension, integrity-verifiable history and explicit restoration. Apply reevaluation eligibility 90 days after the recorded suspension time for all scores at or below 60%. Demonstrate restrictive-control precedence, correction without strike erasure and three-strike restriction despite a high score.
4. **Future proposals alongside controlled enforcement:** only after SilverGate's separately scoped Preview/Approve/Enforce/Verify/Rollback architecture exists. AI proposals require deterministic evidence validation and user approval. No AI sole-evidence enforcement and no self-approval path.

Stages 2 and 3 are coupled release requirements: no privileged AI integration ships before the applicable governance controls operate. This roadmap does not authorize enforcement implementation or machine changes.

Future regression tests must cover: operation with AI absent; forged provider identity; malicious text inside telemetry; unsupported AI claims; withheld data/egress; revocation during use; dismissed versus upheld allegations; corrected-but-upheld violations; three upheld violations with a Qualified score; score increases without restoration; suspension and reevaluation eligibility before, at and after 90 days for both exactly 60% and scores below 60%, without automatic reinstatement; and reproducible scoring/audit replay.

Hardening regressions additionally require: disagreement without an alignment violation; objective substitution and ignored corrections routed to adjudication; suspected Critical containment with zero strikes and no automatic conviction; capability-specific scope enforcement; forged/replayed approval assertions rejected; alteration/deletion/reordering/truncation detection; version changes retaining lineage history while receiving a new assessment and score; decay affecting numerical contributions without removing strikes; no automatic suspension-clock restart for a new upheld violation; revocation of new/follow-on operations while uncancellable work remains observable; and every overlap resolved by the most restrictive applicable control. No passing test is itself a user grant.

Future investigation acceptance must verify advisory labeling, no authoritative promotion from AI consensus, user-only adjudication and notice of waiting adjudications without requiring tracker polling. Existing Critical containment must still operate independently. Assistance eligibility must respect the no-governance-marks requirement once its meaning is explicitly specified; no default eligibility rule is invented here. Documentation checks must retain the context-compression observation as a design consideration rather than an adjudicated category. See [design-stage intent and planning](SilverGate-v0.1-specification.md#22-design-stage-intent-and-planning) for the consolidated update's non-implementation scope.
