# First 3D Torus Animation

This project uses Manim Community. The first scene uses ordinary text, not
LaTeX, and draws a parameterized torus with a longitude and a meridian.

## Files

- `first_torus.py`: the scene to edit; its class is `FirstTorus`.
- `pyproject.toml`, `uv.lock`, `.python-version`: environment configuration.
- `src/manim_scenes/__init__.py`: the original package scaffold; not the scene.
- `.venv/`: the project environment; do not edit its files manually.
- `media/`: generated videos, still images, and render caches.

## Run in Windows Command Prompt

```bat
cd /d "C:\Users\user\Documents\GitHub\Graduation-Project\cayley-thesis\manim-scenes"
uv run manim -pql first_torus.py FirstTorus
```

`-p` opens the result in the default video player; `-ql` renders a fast
480p, 15 fps preview. Rendering without `-p` creates the same video without
opening a player:

```bat
uv run manim -ql first_torus.py FirstTorus
```

Expected preview file:

```text
media/videos/first_torus/480p15/FirstTorus.mp4
```

After approving the draft, render a high-quality version:

```bat
uv run manim -pqh first_torus.py FirstTorus
```

Save a still of the final scene:

```bat
uv run manim -ql -s first_torus.py FirstTorus
```

If `uv` is not visible in an older terminal, reopen the terminal. The direct
environment-based equivalent is:

```bat
.venv\Scripts\python.exe -m manim -pql first_torus.py FirstTorus
```

## What to inspect

1. The central hole stays open during camera rotation.
2. Orange is the longitude; teal is the meridian.
3. Both curves are drawn on the same surface and meet at one point.
4. Screen labels remain fixed while the camera moves.

The torus is intentionally translucent so rear portions are visible.
This is a demonstration of an already embedded torus, not a sphere-to-torus
homeomorphism or a solid torus. Its surface has H1(T^2; Z) = Z^2.

## First edits

Change `MAJOR_RADIUS`, `MINOR_RADIUS`, or `SURFACE_OPACITY` near the top
of `first_torus.py`. Keep `MAJOR_RADIUS > MINOR_RADIUS > 0`.
Camera angles use degrees; the automatic camera rotation uses radians
per second. Do not modify the topology by an arbitrary visual transform.

## Environment check

```bat
uv run manim checkhealth
```

LaTeX is only needed when introducing `Tex` or `MathTex` into a later scene.
An older shell may not expose project scripts on its PATH; `uv run` or
the direct project Python command avoids that issue.
