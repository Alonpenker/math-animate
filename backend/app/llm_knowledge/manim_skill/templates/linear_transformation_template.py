from manim import *


class LinearTransformationTemplate(VisualTemplate):
    VALID_STATES = frozenset({"setup", "transformed", "comparison", "eigenvector"})
    VECTOR_COLORS = (TEAL_B, ORANGE, GREEN_B, PURPLE_B, RED_C)

    def __init__(
        self,
        state: str,
        *,
        matrix: list[list[float]],
        vectors: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        vector_labels: list[str] | tuple[str, ...] | None = None,
        active_index: int = 0,
        show_span: bool = False,
        show_unit_square: bool = False,
        show_matrix_label: bool = True,
        x_range: tuple[float, float, float] = (-5, 6, 1),
        y_range: tuple[float, float, float] = (-5, 6, 1),
    ):
        state = self._validate_state(state)
        self.matrix = self._validate_matrix(matrix)
        self.vectors = self._validate_vectors(vectors)
        self.transformed_vectors = [self._transform(vector) for vector in self.vectors]
        self.active_index = self._validate_index(active_index)
        self.show_span = show_span
        self.show_unit_square = show_unit_square

        labels = list(vector_labels) if vector_labels is not None else [
            rf"v_{{{index + 1}}}" for index in range(len(self.vectors))
        ]
        if len(labels) != len(self.vectors):
            raise ValueError("vector_labels must match vectors length")

        self.axes = Axes(
            x_range=list(x_range),
            y_range=list(y_range),
            x_length=7,
            y_length=5.2,
            tips=False,
            axis_config={"color": GREY_B, "stroke_width": 2},
        )
        axes_group = VGroup(
            self.axes,
            self.axes.get_axis_labels(MathTex("x", font_size=24), MathTex("y", font_size=24)),
        )
        active_vectors = self.vectors if state == "setup" else self.transformed_vectors
        active_labels = labels if state == "setup" else [rf"A{label}" for label in labels]
        self.active_vectors = VGroup(*[
            self._vector_bundle(vector, label, color)
            for vector, label, color in zip(active_vectors, active_labels, self._colors())
        ])
        self.reference_vectors = VGroup(*[
            self._vector_bundle(vector, label, color)
            for vector, label, color in zip(self.vectors, labels, self._colors())
        ])
        self.spans = VGroup(*[
            self._span(vector, color)
            for vector, color in zip(self.vectors, self._colors())
        ])
        self.active_square = self._square(transformed=state != "setup")
        self.reference_square = self._square(transformed=False)
        self.matrix_label = self._matrix_label() if show_matrix_label else VGroup(VectorizedPoint())
        self.eigenvalue_label = self._eigenvalue_label()

        self._apply_state_opacity(state)
        boundary = Rectangle(width=9.6, height=6).move_to(self.axes).set_opacity(0)
        super().__init__(
            axes_group,
            self.spans,
            self.reference_square,
            self.active_square,
            self.reference_vectors,
            self.active_vectors,
            self.matrix_label,
            self.eigenvalue_label,
            boundary,
            state=state,
        )

    def highlight_vector(self, index: int) -> Animation:
        index = self._validate_index(index)
        return Circumscribe(self.active_vectors[index], color=YELLOW, buff=0.12, fade_out=True)

    def highlight_span(self, index: int) -> Animation:
        index = self._validate_index(index)
        if not self.show_span:
            raise ValueError("highlight_span requires show_span=True")
        return Circumscribe(self.spans[index], color=YELLOW, buff=0.1, fade_out=True)

    def highlight_unit_square(self) -> Animation:
        if not self.show_unit_square:
            raise ValueError("highlight_unit_square requires show_unit_square=True")
        return Circumscribe(self.active_square, color=YELLOW, buff=0.1, fade_out=True)

    def _apply_state_opacity(self, state: str) -> None:
        self.spans.set_opacity(1 if self.show_span else 0)
        self.active_square.set_opacity(1 if self.show_unit_square else 0)
        self.reference_square.set_opacity(0)
        self.reference_vectors.set_opacity(0)
        self.eigenvalue_label.set_opacity(0)

        if state in {"transformed", "comparison", "eigenvector"}:
            self.reference_vectors.set_opacity(0.3)
            if self.show_unit_square:
                self.reference_square.set_opacity(0.25)

        if state == "eigenvector":
            self.reference_vectors.set_opacity(0.12)
            self.active_vectors.set_opacity(0.12)
            self.spans.set_opacity(0)
            self.reference_vectors[self.active_index].set_opacity(0.4)
            self.active_vectors[self.active_index].set_opacity(1)
            if self.show_span:
                self.spans[self.active_index].set_opacity(1)
            self.eigenvalue_label.set_opacity(1)

    def _vector_bundle(self, vector, label: str, color: ManimColor) -> VGroup:
        endpoint = self.axes.c2p(*vector)
        arrow = Arrow(self.axes.c2p(0, 0), endpoint, buff=0, color=color, stroke_width=5)
        text = MathTex(label, font_size=25, color=color).next_to(endpoint, UR, buff=0.08)
        return VGroup(arrow, text)

    def _span(self, vector, color: ManimColor) -> VGroup:
        factor = 4.5 / max(abs(vector[0]), abs(vector[1]))
        return VGroup(DashedLine(
            self.axes.c2p(-factor * vector[0], -factor * vector[1]),
            self.axes.c2p(factor * vector[0], factor * vector[1]),
            color=color,
            stroke_opacity=0.55,
        ))

    def _square(self, *, transformed: bool) -> VGroup:
        points = [(0, 0), (1, 0), (1, 1), (0, 1)]
        if transformed:
            points = [self._transform(point) for point in points]
        polygon = Polygon(
            *[self.axes.c2p(*point) for point in points],
            color=BLUE_B if transformed else GREY_B,
            fill_opacity=0.16,
            stroke_width=3,
        )
        return VGroup(polygon)

    def _matrix_label(self) -> VGroup:
        a, b = self.matrix[0]
        c, d = self.matrix[1]
        label = MathTex(
            rf"A=\begin{{bmatrix}}{a:g}&{b:g}\\{c:g}&{d:g}\end{{bmatrix}}",
            font_size=27,
        ).move_to(self.axes.get_corner(UR) + LEFT * 0.65 + DOWN * 0.35)
        return VGroup(label)

    def _eigenvalue_label(self) -> VGroup:
        vector = self.vectors[self.active_index]
        transformed = self.transformed_vectors[self.active_index]
        scale = (
            transformed[0] / vector[0]
            if abs(vector[0]) > 1e-9
            else transformed[1] / vector[1]
        )
        if abs(transformed[0] * vector[1] - transformed[1] * vector[0]) > 1e-9:
            return VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        return VGroup(MathTex(
            rf"Av={scale:g}v",
            font_size=28,
            color=YELLOW,
        ).move_to(self.axes.get_corner(UL) + RIGHT * 0.65 + DOWN * 0.35))

    def _transform(self, vector) -> tuple[float, float]:
        x, y = vector
        return (
            self.matrix[0][0] * x + self.matrix[0][1] * y,
            self.matrix[1][0] * x + self.matrix[1][1] * y,
        )

    def _validate_index(self, index: int) -> int:
        if not isinstance(index, int) or not 0 <= index < len(self.vectors):
            raise ValueError("active vector index is outside vectors")
        return index

    @staticmethod
    def _validate_matrix(matrix) -> list[list[float]]:
        if (
            not isinstance(matrix, list)
            or len(matrix) != 2
            or any(not isinstance(row, list) or len(row) != 2 for row in matrix)
            or any(not isinstance(value, (int, float)) for row in matrix for value in row)
        ):
            raise ValueError("matrix must be a numeric 2x2 list")
        return matrix

    @staticmethod
    def _validate_vectors(vectors) -> list[tuple[float, float]]:
        if not isinstance(vectors, (list, tuple)) or not vectors:
            raise ValueError("vectors must be a non-empty list")
        if any(
            not isinstance(vector, (list, tuple))
            or len(vector) != 2
            or any(not isinstance(value, (int, float)) for value in vector)
            or vector == (0, 0)
            or vector == [0, 0]
            for vector in vectors
        ):
            raise ValueError("vectors must contain non-zero numeric 2D vectors")
        return [tuple(vector) for vector in vectors]

    def _colors(self):
        return [
            self.VECTOR_COLORS[index % len(self.VECTOR_COLORS)]
            for index in range(len(self.vectors))
        ]
