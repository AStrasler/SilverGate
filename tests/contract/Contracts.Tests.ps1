# Pester 3+ entry point; the draft-2020-12 validator is development-only.
Describe 'SilverGate contract milestone' {
    It 'passes draft schemas, fixture integrity and hostile-input contracts' {
        if (-not $env:SILVERGATE_TEST_PYTHON) {
            throw 'Set SILVERGATE_TEST_PYTHON to a Python 3.12+ executable with requirements-test.txt installed.'
        }
        $testPath = Join-Path $PSScriptRoot 'check_contracts.py'
        & $env:SILVERGATE_TEST_PYTHON $testPath
        $LASTEXITCODE | Should Be 0
    }
}
