from typing import Literal

import numpy as np
from manim import *


def make_pythagorean_area_model(
    leg_a: float = 1.35,
    leg_b: float = 2.15,
    arrangement: Literal["c_square", "ab_squares"] = "c_square",
    include_side_labels: bool = True,
) -> VGroup:
    points = _square_points(leg_a=leg_a, leg_b=leg_b)
    if arrangement == "c_square":
        return _build_c_square_arrangement(points, include_side_labels)
    if arrangement == "ab_squares":
        return _build_ab_squares_arrangement(points)
    raise ValueError("arrangement must be 'c_square' or 'ab_squares'.")


def _square_points(*, leg_a: float, leg_b: float) -> dict[str, np.ndarray]:
    size = leg_a + leg_b

    def point(x: float, y: float) -> np.ndarray:
        return np.array([x - size / 2, y - size / 2, 0.0])

    return {
        "bottom_left": point(0, 0),
        "bottom_right": point(size, 0),
        "top_right": point(size, size),
        "top_left": point(0, size),
        "bottom_split": point(leg_b, 0),
        "right_split": point(size, leg_b),
        "top_split": point(leg_a, size),
        "left_split": point(0, leg_a),
        "a_bottom": point(leg_a, 0),
        "a_left": point(0, leg_a),
        "a_corner": point(leg_a, leg_a),
        "b_right_bottom": point(size, leg_a),
        "b_left_top": point(leg_a, size),
    }


def _build_c_square_arrangement(
    points: dict[str, np.ndarray],
    include_side_labels: bool,
) -> VGroup:
    outer = _outer_square(points)
    triangles = VGroup(
        _proof_triangle(points["bottom_left"], points["bottom_split"], points["left_split"]),
        _proof_triangle(points["bottom_right"], points["right_split"], points["bottom_split"]),
        _proof_triangle(points["top_right"], points["top_split"], points["right_split"]),
        _proof_triangle(points["top_left"], points["left_split"], points["top_split"]),
    )
    c_square = Polygon(
        points["bottom_split"],
        points["right_split"],
        points["top_split"],
        points["left_split"],
        stroke_color=GREEN_A,
        stroke_width=3,
        fill_color=GREEN_E,
        fill_opacity=0.42,
    )
    c_area_label = MathTex("c^2", font_size=34).move_to(c_square.get_center())
    model = VGroup(outer, triangles, c_square, c_area_label)
    if include_side_labels:
        model.add(_c_square_side_labels(points))
    return model


def _build_ab_squares_arrangement(points: dict[str, np.ndarray]) -> VGroup:
    outer = _outer_square(points)
    triangles = VGroup(
        _proof_triangle(points["a_bottom"], points["bottom_right"], points["b_right_bottom"]),
        _proof_triangle(points["a_bottom"], points["a_corner"], points["b_right_bottom"]),
        _proof_triangle(points["a_left"], points["a_corner"], points["b_left_top"]),
        _proof_triangle(points["a_left"], points["top_left"], points["b_left_top"]),
    )
    a_square = Polygon(
        points["bottom_left"],
        points["a_bottom"],
        points["a_corner"],
        points["a_left"],
        stroke_color=BLUE_A,
        stroke_width=3,
        fill_color=BLUE_E,
        fill_opacity=0.48,
    )
    b_square = Polygon(
        points["a_corner"],
        points["b_right_bottom"],
        points["top_right"],
        points["b_left_top"],
        stroke_color=TEAL_A,
        stroke_width=3,
        fill_color=TEAL_E,
        fill_opacity=0.48,
    )
    labels = VGroup(
        MathTex("a^2", font_size=30).move_to(a_square.get_center()),
        MathTex("b^2", font_size=30).move_to(b_square.get_center()),
    )
    return VGroup(outer, triangles, a_square, b_square, labels)


def _outer_square(points: dict[str, np.ndarray]) -> Polygon:
    return Polygon(
        points["bottom_left"],
        points["bottom_right"],
        points["top_right"],
        points["top_left"],
        stroke_color=WHITE,
        stroke_width=3,
    )


def _proof_triangle(*vertices: np.ndarray) -> Polygon:
    return Polygon(
        *vertices,
        fill_color=GREY_BROWN,
        fill_opacity=0.38,
        stroke_color=WHITE,
        stroke_width=2,
    )


def _c_square_side_labels(points: dict[str, np.ndarray]) -> VGroup:
    return VGroup(
        MathTex("a", font_size=28, color=BLUE_A).move_to(
            _midpoint(points["bottom_left"], points["left_split"]) + LEFT * 0.28
        ),
        MathTex("b", font_size=28, color=TEAL_A).move_to(
            _midpoint(points["bottom_left"], points["bottom_split"]) + DOWN * 0.28
        ),
        _label_outside_segment(
            "c",
            points["bottom_split"],
            points["left_split"],
            color=YELLOW,
        ),
    )


def _label_outside_segment(
    text: str,
    start: np.ndarray,
    end: np.ndarray,
    color: ManimColor,
) -> MathTex:
    segment = end - start
    normal = np.array([segment[1], -segment[0], 0.0])
    normal = normal / np.linalg.norm(normal)
    return MathTex(text, font_size=28, color=color).move_to(
        _midpoint(start, end) + normal * 0.32
    )


def _midpoint(start: np.ndarray, end: np.ndarray) -> np.ndarray:
    return (start + end) / 2


class PythagoreanAreaTemplate(Scene):
    def construct(self):
        model = make_pythagorean_area_model(arrangement="c_square")
        model.scale(1.1)
        self.play(FadeIn(model))
        self.wait()
