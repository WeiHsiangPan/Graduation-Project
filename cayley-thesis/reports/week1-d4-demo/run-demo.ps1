param([switch]$Render)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
Push-Location -LiteralPath $projectRoot
try {
    python cayley-thesis/experiments/verify_run.py cayley-thesis/experiments/results/20261031T175148_814309Z
    if ($LASTEXITCODE -ne 0) { throw 'Saved experiment verification failed.' }
    python cayley-thesis/experiments/build_d4_lesson.py
    if ($LASTEXITCODE -ne 0) { throw 'D4 trace replay failed.' }
    if ($Render) {
        $manimPython = Join-Path $projectRoot 'cayley-thesis\manim-scenes\.venv\Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $manimPython)) { throw 'Existing Manim virtual environment is missing.' }
        & $manimPython -m manim -qm --verbosity WARNING --media_dir cayley-thesis/reports/week1-d4-demo/media cayley-thesis/manim-scenes/d4_pipeline.py D4Pipeline
        if ($LASTEXITCODE -ne 0) { throw 'Manim render failed.' }
        $movie = Join-Path $PSScriptRoot 'media\videos\d4_pipeline\720p30\D4Pipeline.mp4'
        Copy-Item -LiteralPath $movie -Destination (Join-Path $PSScriptRoot 'D4Pipeline.mp4') -Force
    }
    Write-Output 'PASS: D4 saved certificates and exact search traces checked.'
} finally {
    Pop-Location
}
