# Development dependencies

No third-party source is copied into the runtime and no runtime package is introduced at this stage. Contract tests use the following pinned packages, excluded from version control in `.test-deps/`:

| Package | Version | Declared license | Purpose |
|---|---|---|---|
| jsonschema | 4.26.0 | MIT | Draft 2020-12 validation in development tests |
| attrs | 26.1.0 | MIT | Validator dependency |
| jsonschema-specifications | 2025.9.1 | MIT | JSON Schema specifications for validator |
| referencing | 0.37.0 | MIT | Offline schema registry |
| rpds-py | 2026.6.3 | MIT | Referencing dependency |
| typing-extensions | 4.16.0 | PSF-2.0 | Dependency typing support |

Licenses above were checked against installed package metadata. The installed packages retain their own license files. These dependencies justify schema testing, not production telemetry, AI, or network access. Any future redistribution requires preserving applicable notices. Tests also use the existing Windows PowerShell/Pester installation; nothing is vendored from it. No simplewall or White-Knight source has been used.
