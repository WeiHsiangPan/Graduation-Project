param([switch]$Render)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
Push-Location -LiteralPath $projectRoot
try {
    python cayley-thesis/experiments/example7_rebuild.py
    if ($LASTEXITCODE -ne 0) { throw 'Example 7 reconstruction failed.' }
    python -m unittest discover -s cayley-thesis/experiments -p test_example7_rebuild.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Example 7 tests failed.' }
    $manimPython = Join-Path $projectRoot 'cayley-thesis\manim-scenes\.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $manimPython)) { throw 'Existing Manim environment required for cross-check.' }
    & $manimPython cayley-thesis/experiments/example7_rebuild.py --cross-check
    if ($LASTEXITCODE -ne 0) { throw 'Independent implementation disagrees.' }
    if ($Render) {
        & $manimPython -m manim -qm --verbosity WARNING --media_dir cayley-thesis/reports/week1-example7-demo/media cayley-thesis/manim-scenes/example7_pipeline.py Example7Pipeline
        if ($LASTEXITCODE -ne 0) { throw 'Example 7 render failed.' }
        $movie = Join-Path $PSScriptRoot 'media\videos\example7_pipeline\720p30\Example7Pipeline.mp4'
        Copy-Item -LiteralPath $movie -Destination (Join-Path $PSScriptRoot 'Example7Pipeline.mp4') -Force
    }
    Write-Output 'PASS: both inputs reconstructed; tests and four cross-check cases passed.'
} finally {
    Pop-Location
}
