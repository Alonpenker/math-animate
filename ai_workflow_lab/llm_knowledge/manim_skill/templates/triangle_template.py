import numpy as np
from manim import *


class TriangleTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "right_base",
        "right_labeled",
        "right_hypotenuse_highlighted",
        "right_squares",
        "right_emphasized",
        "non_right_labeled",
        "non_right_emphasized",
    })

    def __init__(
        self,
        state: str,
        leg_a: float | None = None,
        leg_b: float | None = None,
    ):
        state = self._validate_state(state)
        default_a, default_b = self._default_dimensions(state)
        leg_a = default_a if leg_a is None else leg_a
        leg_b = default_b if leg_b is None else leg_b

        if state == "right_squares":
            parts = self._build_right_squares(leg_a=leg_a, leg_b=leg_b)
        elif state == "right_emphasized":
            parts = self._build_right_emphasized(leg_a=leg_a, leg_b=leg_b)
        elif state.startswith("right_"):
            parts = self._build_right_diagram(state=state, leg_a=leg_a, leg_b=leg_b)
        else:
            parts = self._build_non_right(state=state, width=leg_a, height=leg_b)
        super().__init__(*parts.submobjects, state=state)

    @staticmethod
    def _default_dimensions(state: str) -> tuple[float, float]:
        if state == "right_squares":
            return 2.8, 1.9
        if state in {"right_emphasized", "non_right_labeled", "non_right_emphasized"}:
            return 2.5, 1.7
        return 3.2, 2.2

    @classmethod
    def _build_right_diagram(
        cls,
        *,
        state: str,
        leg_a: float,
        leg_b: float,
    ) -> VGroup:
        right_vertex, a_vertex, b_vertex, center = cls._right_vertices(leg_a, leg_b)
        triangle = cls._triangle(right_vertex, a_vertex, b_vertex)
        right_angle = RightAngle(
            Line(right_vertex, a_vertex),
            Line(right_vertex, b_vertex),
            length=0.28,
            color=YELLOW,
        )
        labels = VGroup(
            cls._outside_label("a", right_vertex, a_vertex, center, BLUE_A, font_size=30, offset=0.34),
            cls._outside_label("b", right_vertex, b_vertex, center, TEAL_A, font_size=30, offset=0.34),
            cls._outside_label("c", a_vertex, b_vertex, center, RED_A, font_size=30, offset=0.34),
        )
        hypotenuse = Line(a_vertex, b_vertex, color=YELLOW, stroke_width=6)
        if state == "right_base":
            labels.set_opacity(0)
            hypotenuse.set_opacity(0)
        elif state == "right_labeled":
            hypotenuse.set_opacity(0)
        return VGroup(triangle, right_angle, labels, hypotenuse, VGroup())

    @classmethod
    def _build_right_squares(cls, *, leg_a: float, leg_b: float) -> VGroup:
        right_vertex, a_vertex, b_vertex, center = cls._right_vertices(leg_a, leg_b)
        triangle = cls._triangle(
            right_vertex,
            a_vertex,
            b_vertex,
            fill_opacity=0.25,
        )
        right_angle = RightAngle(
            Line(right_vertex, a_vertex),
            Line(right_vertex, b_vertex),
            length=0.25,
            color=YELLOW,
        )
        labels = VGroup(
            cls._outside_label("a", right_vertex, a_vertex, center, BLUE_A),
            cls._outside_label("b", right_vertex, b_vertex, center, TEAL_A),
            cls._outside_label("c", a_vertex, b_vertex, center, RED_A),
        )
        squares = VGroup(
            cls._outward_square(right_vertex, a_vertex, center, BLUE_E),
            cls._outward_square(right_vertex, b_vertex, center, TEAL_E),
            cls._outward_square(a_vertex, b_vertex, center, RED_E),
        )
        area_labels = VGroup(
            MathTex("a^2", font_size=28, color=BLUE_A).move_to(squares[0]),
            MathTex("b^2", font_size=28, color=TEAL_A).move_to(squares[1]),
            MathTex("c^2", font_size=28, color=RED_A).move_to(squares[2]),
        )
        return VGroup(triangle, right_angle, labels, squares, area_labels)

    @classmethod
    def _build_right_emphasized(cls, *, leg_a: float, leg_b: float) -> VGroup:
        right_vertex, a_vertex, b_vertex, center = cls._right_vertices(leg_a, leg_b)
        triangle = cls._triangle(right_vertex, a_vertex, b_vertex)
        marker = RightAngle(
            Line(right_vertex, a_vertex),
            Line(right_vertex, b_vertex),
            length=0.24,
            color=YELLOW,
        )
        labels = VGroup(
            cls._outside_label("a", right_vertex, a_vertex, center, BLUE_A),
            cls._outside_label("b", right_vertex, b_vertex, center, TEAL_A),
            cls._outside_label("c", a_vertex, b_vertex, center, RED_A),
        )
        diagram = VGroup(triangle, marker, labels)
        emphasis = SurroundingRectangle(diagram, color=GREEN_B, buff=0.18)
        return VGroup(diagram, emphasis)

    @classmethod
    def _build_non_right(
        cls,
        *,
        state: str,
        width: float,
        height: float,
    ) -> VGroup:
        left = np.array([-width / 2, -height / 2, 0.0])
        right = np.array([width / 2, -height / 2, 0.0])
        apex = np.array([width * 0.06, height / 2, 0.0])
        center = (left + right + apex) / 3
        triangle = cls._triangle(left, right, apex)
        labels = VGroup(
            cls._outside_label("c", left, right, center, RED_A),
            cls._outside_label("a", left, apex, center, BLUE_A),
            cls._outside_label("b", right, apex, center, TEAL_A),
        )
        diagram = VGroup(triangle, VGroup(), labels)
        if state == "non_right_labeled":
            return diagram
        emphasis = VGroup(
            SurroundingRectangle(diagram, color=RED_B, buff=0.18),
            Line(diagram.get_corner(UL), diagram.get_corner(DR), color=RED_B, stroke_width=5),
            Line(diagram.get_corner(DL), diagram.get_corner(UR), color=RED_B, stroke_width=5),
        )
        return VGroup(diagram, emphasis)

    @staticmethod
    def _right_vertices(
        leg_a: float,
        leg_b: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        right_vertex = np.array([-leg_a / 2, -leg_b / 2, 0.0])
        a_vertex = right_vertex + RIGHT * leg_a
        b_vertex = right_vertex + UP * leg_b
        center = (right_vertex + a_vertex + b_vertex) / 3
        return right_vertex, a_vertex, b_vertex, center

    @staticmethod
    def _triangle(*vertices: np.ndarray, fill_opacity: float = 0.28) -> Polygon:
        return Polygon(
            *vertices,
            stroke_color=WHITE,
            stroke_width=3,
            fill_color=GREY_BROWN,
            fill_opacity=fill_opacity,
        )

    @staticmethod
    def _outward_square(
        start: np.ndarray,
        end: np.ndarray,
        figure_center: np.ndarray,
        color: ManimColor,
    ) -> Polygon:
        segment = end - start
        normal = TriangleTemplate._outward_unit_normal(start, end, figure_center)
        normal *= np.linalg.norm(segment)
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

    @staticmethod
    def _outside_label(
        text: str,
        start: np.ndarray,
        end: np.ndarray,
        figure_center: np.ndarray,
        color: ManimColor,
        *,
        font_size: int = 28,
        offset: float = 0.3,
    ) -> MathTex:
        midpoint = (start + end) / 2
        normal = TriangleTemplate._outward_unit_normal(start, end, figure_center)
        return MathTex(text, font_size=font_size, color=color).move_to(
            midpoint + normal * offset
        )

    @staticmethod
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
