import math

import numpy as np
from manim import *


class TriangleTemplate(VisualTemplate):
    LEGACY_STATES = frozenset({
        "right_base",
        "right_labeled",
        "right_hypotenuse_highlighted",
        "right_squares",
        "right_emphasized",
        "non_right_labeled",
        "non_right_emphasized",
    })
    GENERIC_STATES = frozenset({
        "general_base",
        "general_labeled",
        "altitude",
        "median",
        "angle_bisector",
        "area",
        "angle_sum",
        "similarity_marked",
        "congruence_marked",
    })
    VALID_STATES = LEGACY_STATES | GENERIC_STATES
    TRIANGLE_TYPES = frozenset({"right", "scalene", "isosceles", "equilateral"})
    SIDES = ("AB", "BC", "CA")
    VERTICES = ("A", "B", "C")

    def __init__(
        self,
        state: str,
        leg_a: float | None = None,
        leg_b: float | None = None,
        *,
        triangle_type: str = "scalene",
        width: float = 3.2,
        height: float = 2.2,
        apex_offset: float = 0.15,
        vertex_labels: tuple[str, str, str] = ("A", "B", "C"),
        side_labels: tuple[str, str, str] = ("a", "b", "c"),
        active_vertex: str = "A",
        marked_sides: tuple[str, ...] = (),
        marked_angles: tuple[str, ...] = (),
        show_measure_labels: bool = True,
    ):
        state = self._validate_state(state)
        if state in self.LEGACY_STATES:
            parts = self._legacy_parts(state, leg_a, leg_b)
            super().__init__(*parts.submobjects, state=state)
            return

        self.triangle_type = self._validate_triangle_type(triangle_type)
        self.active_vertex = self._validate_vertex(active_vertex)
        self.marked_sides = self._validate_sides(marked_sides)
        self.marked_angles = self._validate_vertices(marked_angles)
        self.vertex_label_values = self._validate_labels(vertex_labels, "vertex_labels")
        self.side_label_values = self._validate_labels(side_labels, "side_labels")
        self.vertices = self._generic_vertices(self.triangle_type, width, height, apex_offset)
        self.center = sum(self.vertices.values()) / 3
        self.side_lines = {
            "AB": Line(self.vertices["A"], self.vertices["B"]),
            "BC": Line(self.vertices["B"], self.vertices["C"]),
            "CA": Line(self.vertices["C"], self.vertices["A"]),
        }
        self.triangle = self._triangle(*[self.vertices[name] for name in self.VERTICES])
        self.vertex_labels = self._vertex_labels()
        self.side_labels = self._side_labels()
        self.construction = self._construction(state)
        self.markers = self._markers(state)
        self.area_group = self._area_group(show_measure_labels)
        self.angle_sum_group = self._angle_sum_group(show_measure_labels)
        self._apply_generic_state(state)
        boundary = Rectangle(width=7.8, height=5.6).move_to(self.triangle).set_opacity(0)
        super().__init__(
            self.triangle,
            self.vertex_labels,
            self.side_labels,
            self.construction,
            self.markers,
            self.area_group,
            self.angle_sum_group,
            boundary,
            state=state,
        )

    def highlight_side(self, side: str) -> Animation:
        side = self._validate_side(side)
        if not hasattr(self, "side_lines"):
            raise ValueError("highlight_side is available on generic triangle states")
        return Circumscribe(self.side_lines[side], color=YELLOW, buff=0.08, fade_out=True)

    def highlight_angle(self, vertex: str) -> Animation:
        vertex = self._validate_vertex(vertex)
        if not hasattr(self, "vertices"):
            raise ValueError("highlight_angle is available on generic triangle states")
        return Indicate(self._angle_marker(vertex), color=YELLOW)

    def highlight_construction(self) -> Animation:
        if not hasattr(self, "construction") or self.construction.width < 1e-9:
            raise ValueError("this state has no construction to highlight")
        return Circumscribe(self.construction, color=YELLOW, buff=0.1, fade_out=True)

    def highlight_marked_parts(self) -> Animation:
        if not hasattr(self, "markers") or self.markers.width < 1e-9:
            raise ValueError("this state has no marked parts to highlight")
        return Indicate(self.markers, color=YELLOW)

    def highlight_area(self) -> Animation:
        if not hasattr(self, "area_group") or self.area_group.width < 1e-9:
            raise ValueError("this state has no area visual to highlight")
        return Circumscribe(self.area_group, color=YELLOW, buff=0.1, fade_out=True)

    def highlight_angle_sum(self) -> Animation:
        if not hasattr(self, "angle_sum_group") or self.angle_sum_group.width < 1e-9:
            raise ValueError("this state has no angle-sum visual to highlight")
        return Circumscribe(self.angle_sum_group, color=YELLOW, buff=0.1, fade_out=True)

    def _apply_generic_state(self, state: str) -> None:
        self.vertex_labels.set_opacity(0 if state == "general_base" else 1)
        self.side_labels.set_opacity(0 if state == "general_base" else 1)
        self.construction.set_opacity(1 if state in {"altitude", "median", "angle_bisector", "area"} else 0)
        self.markers.set_opacity(1 if state in {"similarity_marked", "congruence_marked"} else 0)
        self.area_group.set_opacity(1 if state == "area" else 0)
        self.angle_sum_group.set_opacity(1 if state == "angle_sum" else 0)

    def _construction(self, state: str) -> VGroup:
        if state not in {"altitude", "median", "angle_bisector", "area"}:
            return VGroup(VectorizedPoint(self.center))
        vertex = self.vertices[self.active_vertex]
        first_name, second_name = self._opposite_side_vertices(self.active_vertex)
        first, second = self.vertices[first_name], self.vertices[second_name]
        if state in {"altitude", "area"}:
            target = self._projection_on_line(vertex, first, second)
        elif state == "median":
            target = (first + second) / 2
        else:
            adjacent_first = np.linalg.norm(vertex - first)
            adjacent_second = np.linalg.norm(vertex - second)
            target = (
                adjacent_second * first + adjacent_first * second
            ) / (adjacent_first + adjacent_second)
        line = DashedLine(vertex, target, color=YELLOW, stroke_width=4)
        marker = (
            RightAngle(Line(target, first), Line(target, vertex), length=0.2, color=YELLOW)
            if state in {"altitude", "area"}
            else Dot(target, radius=0.055, color=YELLOW)
        )
        return VGroup(line, marker)

    def _markers(self, state: str) -> VGroup:
        if state not in {"similarity_marked", "congruence_marked"}:
            return VGroup(VectorizedPoint(self.center))
        sides = self.marked_sides or (("AB", "BC") if state == "congruence_marked" else ("AB",))
        angles = self.marked_angles or (("A", "B") if state == "similarity_marked" else ("A",))
        return VGroup(
            *[self._side_tick(side, index + 1) for index, side in enumerate(sides)],
            *[self._angle_marker(vertex, color=(YELLOW, ORANGE, GREEN_B)[index % 3])
              for index, vertex in enumerate(angles)],
        )

    def _area_group(self, show_measure_labels: bool) -> VGroup:
        if not show_measure_labels:
            return VGroup(VectorizedPoint(self.center))
        first_name, second_name = self._opposite_side_vertices(self.active_vertex)
        base = np.linalg.norm(self.vertices[first_name] - self.vertices[second_name])
        height = np.linalg.norm(
            self.vertices[self.active_vertex]
            - self._projection_on_line(
                self.vertices[self.active_vertex],
                self.vertices[first_name],
                self.vertices[second_name],
            )
        )
        label = MathTex(
            rf"A=\frac12({base:.2f})({height:.2f})={base * height / 2:.2f}",
            font_size=27,
            color=YELLOW,
        ).next_to(self.triangle, DOWN, buff=0.35)
        return VGroup(label)

    def _angle_sum_group(self, show_measure_labels: bool) -> VGroup:
        markers = VGroup(*[
            self._angle_marker(vertex, color=(YELLOW, ORANGE, GREEN_B)[index])
            for index, vertex in enumerate(self.VERTICES)
        ])
        if not show_measure_labels:
            return markers
        values = [self._angle_degrees(vertex) for vertex in self.VERTICES]
        label = MathTex(
            rf"{values[0]:.0f}^\circ+{values[1]:.0f}^\circ+{values[2]:.0f}^\circ=180^\circ",
            font_size=27,
            color=YELLOW,
        ).next_to(self.triangle, DOWN, buff=0.35)
        return VGroup(markers, label)

    def _vertex_labels(self) -> VGroup:
        return VGroup(*[
            MathTex(label, font_size=27).move_to(
                self.vertices[name] + self._unit(self.vertices[name] - self.center) * 0.34
            )
            for name, label in zip(self.VERTICES, self.vertex_label_values)
        ])

    def _side_labels(self) -> VGroup:
        colors = (BLUE_A, TEAL_A, RED_A)
        return VGroup(*[
            self._outside_label(label, line.get_start(), line.get_end(), self.center, color)
            for (side, line), label, color in zip(self.side_lines.items(), self.side_label_values, colors)
        ])

    def _side_tick(self, side: str, count: int) -> VGroup:
        line = self.side_lines[side]
        direction = self._unit(line.get_end() - line.get_start())
        normal = np.array([-direction[1], direction[0], 0.0])
        midpoint = line.get_center()
        return VGroup(*[
            Line(
                midpoint + direction * (index - (count - 1) / 2) * 0.12 - normal * 0.11,
                midpoint + direction * (index - (count - 1) / 2) * 0.12 + normal * 0.11,
                color=YELLOW,
                stroke_width=4,
            )
            for index in range(count)
        ])

    def _angle_marker(self, vertex: str, color: ManimColor = YELLOW) -> Angle:
        previous_name, next_name = {
            "A": ("B", "C"),
            "B": ("C", "A"),
            "C": ("A", "B"),
        }[vertex]
        return Angle(
            Line(self.vertices[vertex], self.vertices[previous_name]),
            Line(self.vertices[vertex], self.vertices[next_name]),
            radius=0.27,
            color=color,
        )

    def _angle_degrees(self, vertex: str) -> float:
        previous_name, next_name = {
            "A": ("B", "C"),
            "B": ("C", "A"),
            "C": ("A", "B"),
        }[vertex]
        first = self._unit(self.vertices[previous_name] - self.vertices[vertex])
        second = self._unit(self.vertices[next_name] - self.vertices[vertex])
        return math.degrees(math.acos(float(np.clip(np.dot(first, second), -1, 1))))

    @classmethod
    def _generic_vertices(cls, triangle_type: str, width: float, height: float, apex_offset: float):
        if not all(isinstance(value, (int, float)) and value > 0 for value in (width, height)):
            raise ValueError("width and height must be positive numbers")
        if not isinstance(apex_offset, (int, float)) or not -0.45 <= apex_offset <= 0.45:
            raise ValueError("apex_offset must be between -0.45 and 0.45")
        a = np.array([-width / 2, -height / 2, 0.0])
        b = np.array([width / 2, -height / 2, 0.0])
        if triangle_type == "right":
            c = np.array([-width / 2, height / 2, 0.0])
        elif triangle_type in {"isosceles", "equilateral"}:
            c = np.array([0.0, height / 2, 0.0])
        else:
            c = np.array([width * apex_offset, height / 2, 0.0])
        if triangle_type == "equilateral":
            c[1] = a[1] + width * math.sqrt(3) / 2
        return {"A": a, "B": b, "C": c}

    @staticmethod
    def _opposite_side_vertices(vertex: str):
        return {"A": ("B", "C"), "B": ("C", "A"), "C": ("A", "B")}[vertex]

    @staticmethod
    def _projection_on_line(point, start, end):
        segment = end - start
        return start + np.dot(point - start, segment) / np.dot(segment, segment) * segment

    @classmethod
    def _validate_triangle_type(cls, value: str) -> str:
        if value not in cls.TRIANGLE_TYPES:
            raise ValueError("triangle_type must be right, scalene, isosceles, or equilateral")
        return value

    @classmethod
    def _validate_vertex(cls, value: str) -> str:
        if value not in cls.VERTICES:
            raise ValueError("vertex must be A, B, or C")
        return value

    @classmethod
    def _validate_vertices(cls, values) -> tuple[str, ...]:
        if not isinstance(values, (list, tuple)):
            raise ValueError("marked_angles must be a list or tuple")
        return tuple(cls._validate_vertex(value) for value in values)

    @classmethod
    def _validate_side(cls, value: str) -> str:
        if value not in cls.SIDES:
            raise ValueError("side must be AB, BC, or CA")
        return value

    @classmethod
    def _validate_sides(cls, values) -> tuple[str, ...]:
        if not isinstance(values, (list, tuple)):
            raise ValueError("marked_sides must be a list or tuple")
        return tuple(cls._validate_side(value) for value in values)

    @staticmethod
    def _validate_labels(values, name: str) -> tuple[str, str, str]:
        if (
            not isinstance(values, (list, tuple))
            or len(values) != 3
            or any(not isinstance(value, str) or not value for value in values)
        ):
            raise ValueError(f"{name} must contain three non-empty strings")
        return tuple(values)

    @staticmethod
    def _unit(vector):
        return vector / np.linalg.norm(vector)

    @classmethod
    def _legacy_parts(cls, state: str, leg_a: float | None, leg_b: float | None) -> VGroup:
        default_a, default_b = cls._default_dimensions(state)
        leg_a = default_a if leg_a is None else leg_a
        leg_b = default_b if leg_b is None else leg_b
        if state == "right_squares":
            return cls._build_right_squares(leg_a=leg_a, leg_b=leg_b)
        if state == "right_emphasized":
            return cls._build_right_emphasized(leg_a=leg_a, leg_b=leg_b)
        if state.startswith("right_"):
            return cls._build_right_diagram(state=state, leg_a=leg_a, leg_b=leg_b)
        return cls._build_non_right(state=state, width=leg_a, height=leg_b)

    @staticmethod
    def _default_dimensions(state: str) -> tuple[float, float]:
        if state == "right_squares":
            return 2.8, 1.9
        if state in {"right_emphasized", "non_right_labeled", "non_right_emphasized"}:
            return 2.5, 1.7
        return 3.2, 2.2

    @classmethod
    def _build_right_diagram(cls, *, state: str, leg_a: float, leg_b: float) -> VGroup:
        right_vertex, a_vertex, b_vertex, center = cls._right_vertices(leg_a, leg_b)
        triangle = cls._triangle(right_vertex, a_vertex, b_vertex)
        right_angle = RightAngle(Line(right_vertex, a_vertex), Line(right_vertex, b_vertex), length=0.28, color=YELLOW)
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
        triangle = cls._triangle(right_vertex, a_vertex, b_vertex, fill_opacity=0.25)
        right_angle = RightAngle(Line(right_vertex, a_vertex), Line(right_vertex, b_vertex), length=0.25, color=YELLOW)
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
        marker = RightAngle(Line(right_vertex, a_vertex), Line(right_vertex, b_vertex), length=0.24, color=YELLOW)
        labels = VGroup(
            cls._outside_label("a", right_vertex, a_vertex, center, BLUE_A),
            cls._outside_label("b", right_vertex, b_vertex, center, TEAL_A),
            cls._outside_label("c", a_vertex, b_vertex, center, RED_A),
        )
        diagram = VGroup(triangle, marker, labels)
        return VGroup(diagram, SurroundingRectangle(diagram, color=GREEN_B, buff=0.18))

    @classmethod
    def _build_non_right(cls, *, state: str, width: float, height: float) -> VGroup:
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
        return VGroup(
            diagram,
            VGroup(
                SurroundingRectangle(diagram, color=RED_B, buff=0.18),
                Line(diagram.get_corner(UL), diagram.get_corner(DR), color=RED_B, stroke_width=5),
                Line(diagram.get_corner(DL), diagram.get_corner(UR), color=RED_B, stroke_width=5),
            ),
        )

    @staticmethod
    def _right_vertices(leg_a: float, leg_b: float):
        right_vertex = np.array([-leg_a / 2, -leg_b / 2, 0.0])
        a_vertex = right_vertex + RIGHT * leg_a
        b_vertex = right_vertex + UP * leg_b
        return right_vertex, a_vertex, b_vertex, (right_vertex + a_vertex + b_vertex) / 3

    @staticmethod
    def _triangle(*vertices: np.ndarray, fill_opacity: float = 0.28) -> Polygon:
        return Polygon(*vertices, stroke_color=WHITE, stroke_width=3, fill_color=GREY_BROWN, fill_opacity=fill_opacity)

    @staticmethod
    def _outward_square(start, end, figure_center, color):
        segment = end - start
        normal = TriangleTemplate._outward_unit_normal(start, end, figure_center) * np.linalg.norm(segment)
        return Polygon(start, end, end + normal, start + normal, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.38)

    @staticmethod
    def _outside_label(text, start, end, figure_center, color, *, font_size=28, offset=0.3):
        midpoint = (start + end) / 2
        normal = TriangleTemplate._outward_unit_normal(start, end, figure_center)
        return MathTex(text, font_size=font_size, color=color).move_to(midpoint + normal * offset)

    @staticmethod
    def _outward_unit_normal(start, end, figure_center):
        segment = end - start
        normal = np.array([-segment[1], segment[0], 0.0])
        normal = normal / np.linalg.norm(normal)
        if np.dot(normal, (start + end) / 2 - figure_center) < 0:
            normal *= -1
        return normal
