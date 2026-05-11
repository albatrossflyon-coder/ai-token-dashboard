param(
    [switch]$Json,
    [switch]$Once
)

$pythonCandidates = @(
    "C:\Users\albat\AppData\Local\Programs\Python\Python312\python.exe",
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    (Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $pythonCandidates) {
    Write-Error "Python was not found. Install Python or update the hardcoded path in run-copilot-dashboard.ps1."
    exit 1
}

$python = $pythonCandidates[0]
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Json) {
    & $python (Join-Path $repoRoot "delivery\cli.py") --agent copilot --json
    exit $LASTEXITCODE
}

$argsList = @((Join-Path $repoRoot "delivery\dashboard.py"), "--agent", "copilot")
if ($Once) {
    $argsList += "--once"
}

& $python @argsList
exit $LASTEXITCODE
