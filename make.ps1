<#
    LittleVitals task runner for Windows / PowerShell.
    Usage:  .\make.ps1 <target>      e.g.  .\make.ps1 build
    Targets: setup fixtures deps build test docs serve lint ci clean
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('setup', 'fixtures', 'deps', 'build', 'test', 'docs', 'serve', 'lint', 'ci', 'clean')]
    [string]$Target = 'build'
)

$ErrorActionPreference = 'Stop'
$DbtFlags = @('--project-dir', 'littlevitals_dbt', '--profiles-dir', 'littlevitals_dbt')
$Dbt = Join-Path $PSScriptRoot '.venv\Scripts\dbt.exe'
if (-not (Test-Path $Dbt)) { $Dbt = 'dbt' }   # fall back to PATH

switch ($Target) {
    'setup'    { python -m venv .venv; & '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt }
    'fixtures' { python data\sample\generate_sample_data.py }
    'deps'     { & $Dbt deps @DbtFlags }
    'build'    { & $Dbt deps @DbtFlags; python data\sample\generate_sample_data.py; & $Dbt build @DbtFlags }
    'test'     { & $Dbt test @DbtFlags }
    'docs'     { & $Dbt docs generate @DbtFlags }
    'serve'    { & $Dbt docs generate @DbtFlags; & $Dbt docs serve @DbtFlags }
    'lint'     { & '.\.venv\Scripts\sqlfluff.exe' lint littlevitals_dbt\models }
    'ci'       { & $Dbt deps @DbtFlags; & $Dbt build @DbtFlags --target ci }
    'clean'    { & $Dbt clean @DbtFlags }
}
