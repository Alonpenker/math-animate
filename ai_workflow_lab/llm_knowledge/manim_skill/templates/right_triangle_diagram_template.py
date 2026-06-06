from typing import Literal

import numpy as np
from manim import *


def make_right_triangle_diagram(
    state: Literal["base", "labeled", "hypotenuse_highlighted"] = "labeled",
    leg_a: float = 3.2,
    leg_b: float = 2.2,
) -> VGroup:
    right_vertex = np.array([-leg_a / 2, -leg_b / 2, 0.0])
    a_vertex = right_vertex + RIGHT * leg_a
    b_vertex = right_vertex + UP * leg_b
    center = (right_vertex + a_vertex + b_vertex) / 3

    triangle = Polygon(
        right_vertex,
        a_vertex,
        b_vertex,
        stroke_color=WHITE,
        stroke_width=3,
        fill_color=GREY_BROWN,
        fill_opacity=0.28,
    )
    right_angle = RightAngle(
        Line(right_vertex, a_vertex),
        Line(right_vertex, b_vertex),
        length=0.28,
        color=YELLOW,
    )
    labels = VGroup(
        _outside_side_label("a", right_vertex, a_vertex, center, BLUE_A),
        _outside_side_label("b", right_vertex, b_vertex, center, TEAL_A),
        _outside_side_label("c", a_vertex, b_vertex, center, RED_A),
    )
    hypotenuse = Line(a_vertex, b_vertex, color=YELLOW, stroke_width=6)
    hypotenuse_label = VGroup()

    if state == "base":
        labels.set_opacity(0)
        hypotenuse.set_opacity(0)
    elif state == "labeled":
        hypotenuse.set_opacity(0)
    elif state != "hypotenuse_highlighted":
        raise ValueError(f"Unknown right-triangle state: {state}")

    return VGroup(triangle, right_angle, labels, hypotenuse, hypotenuse_label)


def _outside_side_label(
    text: str,
    start: np.ndarray,
    end: np.ndarray,
    figure_center: np.ndarray,
    color: ManimColor,
    *,
    font_size: int = 30,
    offset: float = 0.34,
) -> MathTex:
    midpoint = (start + end) / 2
    normal = _outward_unit_normal(start, end, figure_center)
    return MathTex(text, font_size=font_size, color=color).move_to(
        midpoint + normal * offset
    )


def _outward_unit_normal(
    start: np.ndarray,
    end: np.ndarray,
    figure_center: np.ndarray,
) -> np.ndarray:
    segment = end - start
    normal = np.array([-segment[1], segment[0], 0.0])
    normal = normal / np.linalg.norm(normal)
    if np.dot(normal, (start + end) / 2 - figure_center) < 0:
        normal *= -1
    return normal
