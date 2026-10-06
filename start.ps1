# Start the local demo using Python on PATH or ChatGPT Work Mode's bundled runtime.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPythonCommand = Get-Command python -ErrorAction SilentlyContinue
$taskBundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if ($taskPythonCommand) { $taskPython = $taskPythonCommand.Source }
elseif (Test-Path -LiteralPath $taskBundledPython) { $taskPython = $taskBundledPython }
else { throw 'Install Python 3.12 or newer, then run this script again.' }
if (-not (Test-Path -LiteralPath 'data/notebook.sqlite3')) {
    & $taskPython app.py seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& $taskPython app.py serve
