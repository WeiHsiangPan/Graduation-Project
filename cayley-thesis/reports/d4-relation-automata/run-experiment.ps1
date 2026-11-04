$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
Push-Location -LiteralPath $projectRoot
try {
    python cayley-thesis/experiments/relation_automata.py
    if ($LASTEXITCODE -ne 0) { throw 'DFA experiment or certificate verification failed.' }
    python -m unittest discover -s cayley-thesis/experiments -p test_relation_automata.py -v
    if ($LASTEXITCODE -ne 0) { throw 'DFA correctness tests failed.' }
    $drawingPython = Join-Path $projectRoot 'cayley-thesis\manim-scenes\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $drawingPython) {
        & $drawingPython cayley-thesis/experiments/draw_relation_automata.py
        if ($LASTEXITCODE -ne 0) { throw 'Optional diagram generation failed.' }
    }
    Write-Output 'PASS: DFA results, finite/infinite certificates and BFS comparisons saved.'
} finally {
    Pop-Location
}
