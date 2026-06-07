import numpy as np
from manim import *


def make_triangle_comparison(
    state="right",
) -> VGroup:
    if state in {"right", "right_emphasized"}:
        diagram = _triangle_comparison_right_triangle()
        emphasis = SurroundingRectangle(diagram, color=GREEN_B, buff=0.18)
        if state == "right":
            emphasis.set_opacity(0)
        return VGroup(diagram, emphasis)
    if state in {"non_right", "non_right_emphasized"}:
        diagram = _triangle_comparison_acute_triangle()
        emphasis = VGroup(
            SurroundingRectangle(diagram, color=RED_B, buff=0.18),
            Line(diagram.get_corner(UL), diagram.get_corner(DR), color=RED_B, stroke_width=5),
            Line(diagram.get_corner(DL), diagram.get_corner(UR), color=RED_B, stroke_width=5),
        )
        if state == "non_right":
            emphasis.set_opacity(0)
        return VGroup(diagram, emphasis)
    raise ValueError(f"Unknown triangle-comparison state: {state}")


def _triangle_comparison_right_triangle() -> VGroup:
    right_vertex = np.array([-1.25, -0.75, 0.0])
    a_vertex = np.array([1.25, -0.75, 0.0])
    b_vertex = np.array([-1.25, 0.95, 0.0])
    center = (right_vertex + a_vertex + b_vertex) / 3
    triangle = Polygon(
        right_vertex,
        a_vertex,
        b_vertex,
        stroke_color=WHITE,
        fill_color=GREY_BROWN,
        fill_opacity=0.28,
    )
    marker = RightAngle(
        Line(right_vertex, a_vertex),
        Line(right_vertex, b_vertex),
        length=0.24,
        color=YELLOW,
    )
    labels = _triangle_comparison_side_labels(right_vertex, a_vertex, b_vertex, center)
    title = Text("Right triangle", font_size=24, color=GREEN_B).next_to(
        triangle, DOWN, buff=0.55
    )
    return VGroup(triangle, marker, labels, title)


def _triangle_comparison_acute_triangle() -> VGroup:
    a_vertex = np.array([-1.25, -0.7, 0.0])
    b_vertex = np.array([1.25, -0.7, 0.0])
    c_vertex = np.array([0.15, 1.0, 0.0])
    center = (a_vertex + b_vertex + c_vertex) / 3
    triangle = Polygon(
        a_vertex,
        b_vertex,
        c_vertex,
        stroke_color=WHITE,
        fill_color=GREY_BROWN,
        fill_opacity=0.28,
    )
    labels = VGroup(
        _triangle_comparison_outside_label("c", a_vertex, b_vertex, center, RED_A),
        _triangle_comparison_outside_label("a", a_vertex, c_vertex, center, BLUE_A),
        _triangle_comparison_outside_label("b", b_vertex, c_vertex, center, TEAL_A),
    )
    empty_marker = VGroup()
    title = Text("Not a right triangle", font_size=24, color=RED_B).next_to(
        triangle, DOWN, buff=0.55
    )
    return VGroup(triangle, empty_marker, labels, title)


def _triangle_comparison_side_labels(
    first: np.ndarray,
    second: np.ndarray,
    third: np.ndarray,
    center: np.ndarray,
) -> VGroup:
    return VGroup(
        _triangle_comparison_outside_label("a", first, second, center, BLUE_A),
        _triangle_comparison_outside_label("b", first, third, center, TEAL_A),
        _triangle_comparison_outside_label("c", second, third, center, RED_A),
    )


def _triangle_comparison_outside_label(
    text: str,
    start: np.ndarray,
    end: np.ndarray,
    center: np.ndarray,
    color: ManimColor,
) -> MathTex:
    midpoint = (start + end) / 2
    segment = end - start
    normal = np.array([-segment[1], segment[0], 0.0])
    normal = normal / np.linalg.norm(normal)
    if np.dot(normal, midpoint - center) < 0:
        normal *= -1
    return MathTex(text, font_size=28, color=color).move_to(midpoint + normal * 0.3)
