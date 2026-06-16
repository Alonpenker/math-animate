import math

from manim import *


class VectorTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "single",
        "components",
        "addition",
        "subtraction",
        "scalar_multiple",
        "dot_product",
        "projection",
    })

    def __init__(
        self,
        state: str,
        *,
        vector_a: tuple[float, float],
        vector_b: tuple[float, float] | None = None,
        scalar: float = 2,
        vector_a_label: str = "a",
        vector_b_label: str = "b",
        result_label: str = "r",
        show_grid: bool = True,
        show_coordinate_labels: bool = True,
        x_range: tuple[float, float, float] = (-5, 6, 1),
        y_range: tuple[float, float, float] = (-5, 6, 1),
    ):
        state = self._validate_state(state)
        self.vector_a = self._validate_vector(vector_a, "vector_a")
        self.vector_b = self._validate_optional_vector(vector_b)
        if state in {"addition", "subtraction", "dot_product", "projection"} and self.vector_b is None:
            raise ValueError(f"{state} state requires vector_b")
        if not isinstance(scalar, (int, float)):
            raise ValueError("scalar must be numeric")
        self.scalar = scalar
        self.labels = {"a": vector_a_label, "b": vector_b_label, "result": result_label}
        self.show_coordinate_labels = show_coordinate_labels
        if show_grid:
            self.axes = NumberPlane(
                x_range=list(x_range),
                y_range=list(y_range),
                x_length=7,
                y_length=5.2,
                axis_config={"color": GREY_B, "stroke_width": 2},
                background_line_style={"stroke_opacity": 0.22},
            )
        else:
            self.axes = Axes(
                x_range=list(x_range),
                y_range=list(y_range),
                x_length=7,
                y_length=5.2,
                axis_config={"color": GREY_B, "stroke_width": 2},
            )
        axes_group = VGroup(self.axes)

        self.vector_groups = {
            "a": self._vector_bundle((0, 0), self.vector_a, vector_a_label, TEAL_B),
            "b": VGroup(),
            "result": VGroup(),
            "projection": VGroup(),
        }
        self.components = self._components_bundle(self.vector_a)
        self.detail = VGroup()
        self._configure_state(state)
        boundary = Rectangle(width=9.6, height=6).move_to(self.axes).set_opacity(0)
        template_parts = [
            axes_group,
            self.vector_groups["a"],
        ]
        template_parts.extend(
            group
            for group in (
                self.vector_groups["b"],
                self.vector_groups["result"],
                self.vector_groups["projection"],
            )
            if group.submobjects
        )
        template_parts.append(self.components)
        if self.detail.submobjects:
            template_parts.append(self.detail)
        template_parts.append(boundary)
        super().__init__(
            *template_parts,
            state=state,
        )

    def reveal_components(self) -> Animation:
        if self.state != "components":
            raise ValueError("reveal_components is only available in components state")
        return AnimationGroup(self.components.animate.set_opacity(1))

    def reveal_resultant(self) -> Animation:
        if self.state not in {"addition", "subtraction"}:
            raise ValueError("reveal_resultant requires addition or subtraction state")
        return AnimationGroup(self.vector_groups["result"].animate.set_opacity(1))

    def set_scalar(self, target_scalar: float) -> Animation:
        if self.state != "scalar_multiple":
            raise ValueError("set_scalar is only available in scalar_multiple state")
        if not isinstance(target_scalar, (int, float)):
            raise ValueError("target_scalar must be numeric")
        self.scalar = target_scalar
        target = self._vector_bundle(
            (0, 0),
            self._scale(self.vector_a, target_scalar),
            rf"{target_scalar:g}{self.labels['a']}",
            ORANGE,
        )
        return Transform(self.vector_groups["result"], target)

    def reveal_dot_product(self) -> Animation:
        if self.state != "dot_product":
            raise ValueError("reveal_dot_product is only available in dot_product state")
        return AnimationGroup(self.detail.animate.set_opacity(1))

    def highlight_projection(self) -> Animation:
        if self.state != "projection":
            raise ValueError("highlight_projection is only available in projection state")
        return Circumscribe(self.vector_groups["projection"], color=YELLOW, buff=0.12, fade_out=True)

    def highlight_vector(self, role: str) -> Animation:
        if role not in self.vector_groups:
            raise ValueError("vector role must be a, b, result, or projection")
        target = self.vector_groups[role]
        if not target.submobjects:
            raise ValueError(f"{role} vector is not visible in this state")
        if target.width < 1e-9 and target.height < 1e-9:
            raise ValueError(f"{role} vector is not visible in this state")
        return Circumscribe(target, color=YELLOW, buff=0.12, fade_out=True)

    def _configure_state(self, state: str) -> None:
        self.components.set_opacity(0)
        if state in {"addition", "subtraction"}:
            active_b = self.vector_b if state == "addition" else self._scale(self.vector_b, -1)
            result = self._add(self.vector_a, active_b)
            self.vector_groups["b"] = self._vector_bundle(
                self.vector_a,
                active_b,
                self.labels["b"] if state == "addition" else rf"-{self.labels['b']}",
                ORANGE,
            )
            self.vector_groups["result"] = self._vector_bundle(
                (0, 0),
                result,
                self.labels["result"],
                GREEN_B,
            ).set_opacity(0)
        elif state == "scalar_multiple":
            self.vector_groups["a"].set_opacity(0.35)
            self.vector_groups["result"] = self._vector_bundle(
                (0, 0),
                self._scale(self.vector_a, self.scalar),
                rf"{self.scalar:g}{self.labels['a']}",
                ORANGE,
            )
        elif state == "dot_product":
            self.vector_groups["b"] = self._vector_bundle((0, 0), self.vector_b, self.labels["b"], ORANGE)
            angle = Angle(
                Line(self.axes.c2p(0, 0), self.axes.c2p(*self.vector_a)),
                Line(self.axes.c2p(0, 0), self.axes.c2p(*self.vector_b)),
                radius=0.52,
                color=YELLOW,
            )
            value = self._dot(self.vector_a, self.vector_b)
            formula = MathTex(
                rf"{self.labels['a']}\cdot {self.labels['b']}={value:g}",
                font_size=28,
                color=YELLOW,
            ).move_to(self.axes.get_corner(UR) + LEFT * 0.8 + DOWN * 0.35)
            self.detail = VGroup(angle, formula)
            self.detail.set_opacity(0)
        elif state == "projection":
            projection = self._projection(self.vector_a, self.vector_b)
            self.vector_groups["b"] = self._vector_bundle((0, 0), self.vector_b, self.labels["b"], ORANGE)
            self.vector_groups["projection"] = self._vector_bundle(
                (0, 0),
                projection,
                rf"\operatorname{{proj}}_{{{self.labels['b']}}}{self.labels['a']}",
                GREEN_B,
            )
            guide = DashedLine(
                self.axes.c2p(*self.vector_a),
                self.axes.c2p(*projection),
                color=GREY_A,
            )
            self.detail = VGroup(guide)

    def _vector_bundle(self, start, vector, label: str, color: ManimColor) -> VGroup:
        end = self._add(start, vector)
        arrow = Arrow(self.axes.c2p(*start), self.axes.c2p(*end), buff=0, color=color, stroke_width=5)
        label_text = MathTex(label, font_size=25, color=color).next_to(self.axes.c2p(*end), UR, buff=0.08)
        bundle = VGroup(arrow, label_text)
        if self.show_coordinate_labels:
            coordinate = MathTex(
                rf"({vector[0]:g},{vector[1]:g})",
                font_size=20,
                color=color,
            ).next_to(label_text, DOWN, buff=0.06)
            bundle.add(coordinate)
        return bundle

    def _components_bundle(self, vector) -> VGroup:
        x, y = vector
        corner = self.axes.c2p(x, 0)
        return VGroup(
            DashedLine(self.axes.c2p(0, 0), corner, color=BLUE_B),
            DashedLine(corner, self.axes.c2p(x, y), color=GREEN_B),
            MathTex(rf"{x:g}", font_size=23, color=BLUE_B).next_to(corner, DOWN, buff=0.08),
            MathTex(rf"{y:g}", font_size=23, color=GREEN_B).next_to(
                (corner + self.axes.c2p(x, y)) / 2,
                RIGHT,
                buff=0.08,
            ),
        )

    @staticmethod
    def _validate_vector(vector, name: str) -> tuple[float, float]:
        if (
            not isinstance(vector, (list, tuple))
            or len(vector) != 2
            or any(not isinstance(value, (int, float)) for value in vector)
            or all(abs(value) < 1e-9 for value in vector)
        ):
            raise ValueError(f"{name} must be a non-zero numeric 2D vector")
        return tuple(vector)

    @classmethod
    def _validate_optional_vector(cls, vector):
        return None if vector is None else cls._validate_vector(vector, "vector_b")

    @staticmethod
    def _add(first, second):
        return first[0] + second[0], first[1] + second[1]

    @staticmethod
    def _scale(vector, scalar):
        return vector[0] * scalar, vector[1] * scalar

    @staticmethod
    def _dot(first, second):
        return first[0] * second[0] + first[1] * second[1]

    @classmethod
    def _projection(cls, vector, onto):
        factor = cls._dot(vector, onto) / cls._dot(onto, onto)
        return cls._scale(onto, factor)
