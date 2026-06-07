import numpy as np
from manim import *


def make_squares_on_right_triangle(
    state="squares",
    leg_a: float = 2.8,
    leg_b: float = 1.9,
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
        fill_opacity=0.25,
    )
    right_angle = RightAngle(
        Line(right_vertex, a_vertex),
        Line(right_vertex, b_vertex),
        length=0.25,
        color=YELLOW,
    )
    side_labels = VGroup(
        _side_squares_outside_label("a", right_vertex, a_vertex, center, BLUE_A),
        _side_squares_outside_label("b", right_vertex, b_vertex, center, TEAL_A),
        _side_squares_outside_label("c", a_vertex, b_vertex, center, RED_A),
    )
    squares = VGroup(
        _side_squares_outward_square(right_vertex, a_vertex, center, BLUE_E),
        _side_squares_outward_square(right_vertex, b_vertex, center, TEAL_E),
        _side_squares_outward_square(a_vertex, b_vertex, center, RED_E),
    )
    area_labels = VGroup(
        MathTex("a^2", font_size=28, color=BLUE_A).move_to(squares[0]),
        MathTex("b^2", font_size=28, color=TEAL_A).move_to(squares[1]),
        MathTex("c^2", font_size=28, color=RED_A).move_to(squares[2]),
    )

    if state == "triangle":
        side_labels.set_opacity(0)
        squares.set_opacity(0)
        area_labels.set_opacity(0)
    elif state == "labeled":
        squares.set_opacity(0)
        area_labels.set_opacity(0)
    elif state != "squares":
        raise ValueError(f"Unknown side-squares state: {state}")

    return VGroup(triangle, right_angle, side_labels, squares, area_labels)


def _side_squares_outward_square(
    start: np.ndarray,
    end: np.ndarray,
    figure_center: np.ndarray,
    color: ManimColor,
) -> Polygon:
    segment = end - start
    normal = np.array([-segment[1], segment[0], 0.0])
    normal = normal / np.linalg.norm(normal) * np.linalg.norm(segment)
    midpoint = (start + end) / 2
    if np.dot(normal, midpoint - figure_center) < 0:
        normal *= -1
    return Polygon(
        start,
        end,
        end + normal,
        start + normal,
        stroke_color=color,
        stroke_width=3,
        fill_color=color,
        fill_opacity=0.38,
    )


def _side_squares_outside_label(
    text: str,
    start: np.ndarray,
    end: np.ndarray,
    figure_center: np.ndarray,
    color: ManimColor,
) -> MathTex:
    midpoint = (start + end) / 2
    segment = end - start
    normal = np.array([-segment[1], segment[0], 0.0])
    normal = normal / np.linalg.norm(normal)
    if np.dot(normal, midpoint - figure_center) < 0:
        normal *= -1
    return MathTex(text, font_size=28, color=color).move_to(midpoint + normal * 0.3)
