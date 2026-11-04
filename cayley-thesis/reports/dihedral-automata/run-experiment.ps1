$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
Push-Location -LiteralPath $projectRoot
try {
    python cayley-thesis/experiments/dihedral_automata.py
    if ($LASTEXITCODE -ne 0) { throw 'Dihedral experiment or verification failed.' }
    python -m unittest discover -s cayley-thesis/experiments -p test_dihedral_automata.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Dihedral tests failed.' }
    $drawingPython = Join-Path $projectRoot 'cayley-thesis\manim-scenes\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $drawingPython) {
        & $drawingPython cayley-thesis/experiments/draw_dihedral_automata.py
        if ($LASTEXITCODE -ne 0) { throw 'Diagram generation failed.' }
    }
    Write-Output 'PASS: budgets, minima, matched-length controls and cost records saved.'
} finally {
    Pop-Location
}
