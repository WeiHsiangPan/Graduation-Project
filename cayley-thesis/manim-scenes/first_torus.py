"""First Manim scene: an embedded torus with two homology generators.

Preview from this directory:
    uv run manim -pql first_torus.py FirstTorus

The scene uses Text rather than MathTex, so LaTeX is not required.
"""

import numpy as np
from manim import (
    BLUE_D,
    BLUE_E,
    DEGREES,
    DOWN,
    FadeIn,
    Create,
    LEFT,
    ORANGE,
    ParametricFunction,
    Surface,
    TAU,
    TEAL_A,
    Text,
    ThreeDScene,
    UP,
    VGroup,
)


# Change these two values to adjust the torus, keeping R > r > 0.
MAJOR_RADIUS = 2.0
MINOR_RADIUS = 0.7
SURFACE_OPACITY = 0.65


def torus_point(u: float, v: float) -> np.ndarray:
    """Standard embedding of S^1 x S^1 in R^3 (periodic in u and v)."""
    R, r = MAJOR_RADIUS, MINOR_RADIUS
    return np.array([
        (R + r * np.cos(v)) * np.cos(u),
        (R + r * np.cos(v)) * np.sin(u),
        r * np.sin(v),
    ])


class FirstTorus(ThreeDScene):
    def construct(self):
        if not MAJOR_RADIUS > MINOR_RADIUS > 0:
            raise ValueError("An embedded ring torus requires R > r > 0.")

        self.camera.background_color = "#0B1220"
        self.set_camera_orientation(
            phi=62 * DEGREES,
            theta=-45 * DEGREES,
            zoom=0.95,
        )

        title = Text("Torus in 3D", font="Segoe UI", font_size=32).to_edge(UP)
        parameters = Text(
            f"R = {MAJOR_RADIUS:.1f}, r = {MINOR_RADIUS:.1f}  |  R > r > 0",
            font="Segoe UI", font_size=19,
        ).next_to(title, DOWN, buff=0.13)
        longitude_label = Text(
            "Longitude: around the central hole",
            font="Segoe UI", font_size=20, color=ORANGE,
        )
        meridian_label = Text(
            "Meridian: around the tube",
            font="Segoe UI", font_size=20, color=TEAL_A,
        )
        legend = VGroup(longitude_label, meridian_label)
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.13).to_corner(DOWN + LEFT)
        surface = Surface(
            torus_point,
            u_range=(0, TAU),
            v_range=(0, TAU),
            resolution=(32, 20),
            checkerboard_colors=[BLUE_D, BLUE_E],
            fill_opacity=SURFACE_OPACITY,
            stroke_width=0.35,
            stroke_opacity=0.30,
        )

        # Both curves lie exactly on the parameterized surface.
        longitude = ParametricFunction(
            lambda u: torus_point(u, np.pi / 2),
            t_range=(0, TAU, 0.04),
            color=ORANGE,
            stroke_width=6,
            use_smoothing=False,
        )
        meridian = ParametricFunction(
            lambda v: torus_point(-np.pi / 2, v),
            t_range=(0, TAU, 0.04),
            color=TEAL_A,
            stroke_width=6,
            use_smoothing=False,
        )

        self.add_fixed_in_frame_mobjects(title, parameters)
        self.play(FadeIn(surface), run_time=2)
        self.wait(0.5)
        self.play(Create(longitude), run_time=2)
        self.add_fixed_in_frame_mobjects(longitude_label)
        self.wait(0.5)
        self.play(Create(meridian), run_time=2)
        self.add_fixed_in_frame_mobjects(meridian_label)
        self.wait(1)

        self.begin_ambient_camera_rotation(rate=0.20)
        self.wait(8)
        self.stop_ambient_camera_rotation()
        self.move_camera(
            phi=48 * DEGREES,
            theta=-120 * DEGREES,
            run_time=2,
        )
        self.wait(2)

