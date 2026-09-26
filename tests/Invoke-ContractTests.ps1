[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$PythonPath)
$ErrorActionPreference = 'Stop'
$previousPython = $env:SILVERGATE_TEST_PYTHON
try {
    $env:SILVERGATE_TEST_PYTHON = $PythonPath
    Import-Module Pester -ErrorAction Stop
    $testPath = Join-Path $PSScriptRoot 'contract\Contracts.Tests.ps1'
    $result = Invoke-Pester -Script $testPath -PassThru
    if ($result.FailedCount -gt 0) { exit 1 }
} finally {
    $env:SILVERGATE_TEST_PYTHON = $previousPython
}
