# SilverGate

Observe. Explain. Decide.

Development checkout for the read-only Windows firewall evidence project. The design baseline is [specification v0.1.8](docs/SilverGate-v0.1-specification.md), [AI governance v0.1.3](docs/SilverGate-AI-governance-roadmap.md), and the [support policy](docs/support-matrix.md). The documents are copied byte-for-byte from the approved project checkpoint.

## Implementation status

Step 1 has an initial implementation: 22 draft-2020-12 schemas, six sanitized historical fixture/expectation pairs, synthetic evidence/derived examples, and 31 passing contract checks. There is no live collector, correlation engine, report command, installer, AI integration or enforcement functionality yet. The six historical expectation files are regression requirements for the upcoming engine, not evidence that those explanations have been generated/tested by an engine.

Validation on 2026-09-26: the direct development contract suite passed all 31 checks. The Windows-provided PowerShell/Pester entry point could not run because the machine's execution policy disables scripts; no policy was changed or bypassed. PowerShell runtime compatibility is therefore not verified. The local checkout points to AStrasler/SilverGate; no files have been pushed or published. The bundled Git lacks its HTTPS transport helper.

The implementation sequence remains:

1. Schemas, fixtures and contract tests.
2. Offline normalization, correlation and explanation.
3. Bounded read-only collectors and serialization.
4. Local report and evidence navigation.
5. Manual AaronAura capture, coverage/performance validation and replay.

## Contract tests

Use Python 3.12+ with `requirements-test.txt` in a development environment. This validator is a test dependency, not a SilverGate runtime requirement. The intended application runtime remains Windows-provided PowerShell.

```powershell
python -m pip install --target .test-deps -r requirements-test.txt
python tests/contract/check_contracts.py
$env:SILVERGATE_TEST_PYTHON = (Get-Command python).Source
Invoke-Pester tests/contract/Contracts.Tests.ps1
```

The test suite resolves schemas from local files only. It never queries Windows networking, sends telemetry, downloads schemas, executes observed strings, or mutates machine configuration. See [contract implementation notes](docs/contract-implementation.md) for serialization choices and limits.

No official release or minimum-hardware support claim is made. MIT is the intended license; the copyright holder remains to be established before publication, as required by the specification. No source from simplewall or White-Knight is included.
