$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
Push-Location -LiteralPath $projectRoot
try {
    $experimentPython = Join-Path $projectRoot 'cayley-thesis\manim-scenes\.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $experimentPython)) { throw 'Existing Manim environment required for NumPy and Pillow.' }
    & $experimentPython cayley-thesis/experiments/example7_six_choices.py --cross-check
    if ($LASTEXITCODE -ne 0) { throw 'Six-choice experiment or cross-check failed.' }
    & $experimentPython -m unittest discover -s cayley-thesis/experiments -p test_example7_six_choices.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Six-choice tests failed.' }
    & $experimentPython cayley-thesis/experiments/draw_six_choice_comparison.py
    if ($LASTEXITCODE -ne 0) { throw 'Diagram generation failed.' }
    Write-Output 'PASS: six choices saved; cross-check and tests passed; comparison diagram updated.'
} finally {
    Pop-Location
}
