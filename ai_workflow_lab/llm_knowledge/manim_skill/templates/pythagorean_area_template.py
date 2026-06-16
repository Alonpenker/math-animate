import numpy as np
from manim import *


class PythagoreanAreaTemplate(VisualTemplate):
    VALID_STATES = frozenset({"c_square", "ab_squares"})

    def __init__(
        self,
        state: str,
        leg_a: float = 1.35,
        leg_b: float = 2.15,
        include_side_labels: bool = True,
    ):
        state = self._validate_state(state)
        points = self._square_points(leg_a=leg_a, leg_b=leg_b)
        if state == "c_square":
            arrangement = self._build_c_square_arrangement(
                points,
                include_side_labels,
            )
        elif state == "ab_squares":
            arrangement = self._build_ab_squares_arrangement(points)
        else:
            raise AssertionError("validated pythagorean state was not handled")
        super().__init__(*arrangement.submobjects, state=state)

    @staticmethod
    def _square_points(*, leg_a: float, leg_b: float) -> dict[str, np.ndarray]:
        size = leg_a + leg_b
        return {
            "bottom_left": PythagoreanAreaTemplate._point(0, 0, size),
            "bottom_right": PythagoreanAreaTemplate._point(size, 0, size),
            "top_right": PythagoreanAreaTemplate._point(size, size, size),
            "top_left": PythagoreanAreaTemplate._point(0, size, size),
            "bottom_split": PythagoreanAreaTemplate._point(leg_b, 0, size),
            "right_split": PythagoreanAreaTemplate._point(size, leg_b, size),
            "top_split": PythagoreanAreaTemplate._point(leg_a, size, size),
            "left_split": PythagoreanAreaTemplate._point(0, leg_a, size),
            "a_bottom": PythagoreanAreaTemplate._point(leg_a, 0, size),
            "a_left": PythagoreanAreaTemplate._point(0, leg_a, size),
            "a_corner": PythagoreanAreaTemplate._point(leg_a, leg_a, size),
            "b_right_bottom": PythagoreanAreaTemplate._point(size, leg_a, size),
            "b_left_top": PythagoreanAreaTemplate._point(leg_a, size, size),
        }

    @staticmethod
    def _point(x: float, y: float, size: float) -> np.ndarray:
        return np.array([x - size / 2, y - size / 2, 0.0])

    @classmethod
    def _build_c_square_arrangement(
        cls,
        points: dict[str, np.ndarray],
        include_side_labels: bool,
    ) -> VGroup:
        outer = cls._outer_square(points)
        triangles = VGroup(
            cls._proof_triangle(points["bottom_left"], points["bottom_split"], points["left_split"]),
            cls._proof_triangle(points["bottom_right"], points["right_split"], points["bottom_split"]),
            cls._proof_triangle(points["top_right"], points["top_split"], points["right_split"]),
            cls._proof_triangle(points["top_left"], points["left_split"], points["top_split"]),
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
        labels = VGroup(MathTex("c^2", font_size=34).move_to(c_square.get_center()))
        if include_side_labels:
            labels.add(cls._c_square_side_labels(points))
        hidden_second_region = c_square.copy().set_opacity(0)
        return VGroup(outer, triangles, c_square, hidden_second_region, labels)

    @classmethod
    def _build_ab_squares_arrangement(cls, points: dict[str, np.ndarray]) -> VGroup:
        outer = cls._outer_square(points)
        triangles = VGroup(
            cls._proof_triangle(points["a_bottom"], points["bottom_right"], points["b_right_bottom"]),
            cls._proof_triangle(points["a_bottom"], points["a_corner"], points["b_right_bottom"]),
            cls._proof_triangle(points["a_left"], points["a_corner"], points["b_left_top"]),
            cls._proof_triangle(points["a_left"], points["top_left"], points["b_left_top"]),
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

    @staticmethod
    def _outer_square(points: dict[str, np.ndarray]) -> Polygon:
        return Polygon(
            points["bottom_left"],
            points["bottom_right"],
            points["top_right"],
            points["top_left"],
            stroke_color=WHITE,
            stroke_width=3,
        )

    @staticmethod
    def _proof_triangle(*vertices: np.ndarray) -> Polygon:
        return Polygon(
            *vertices,
            fill_color=GREY_BROWN,
            fill_opacity=0.38,
            stroke_color=WHITE,
            stroke_width=2,
        )

    @classmethod
    def _c_square_side_labels(cls, points: dict[str, np.ndarray]) -> VGroup:
        return VGroup(
            MathTex("a", font_size=28, color=BLUE_A).move_to(
                cls._midpoint(points["bottom_left"], points["left_split"]) + LEFT * 0.28
            ),
            MathTex("b", font_size=28, color=TEAL_A).move_to(
                cls._midpoint(points["bottom_left"], points["bottom_split"]) + DOWN * 0.28
            ),
            cls._label_outside_segment(
                "c",
                points["bottom_split"],
                points["left_split"],
                color=YELLOW,
            ),
        )

    @classmethod
    def _label_outside_segment(
        cls,
        text: str,
        start: np.ndarray,
        end: np.ndarray,
        color: ManimColor,
    ) -> MathTex:
        segment = end - start
        normal = np.array([segment[1], -segment[0], 0.0])
        normal = normal / np.linalg.norm(normal)
        return MathTex(text, font_size=28, color=color).move_to(
            cls._midpoint(start, end) + normal * 0.32
        )

    @staticmethod
    def _midpoint(start: np.ndarray, end: np.ndarray) -> np.ndarray:
        return (start + end) / 2
