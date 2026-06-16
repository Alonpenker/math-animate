import math

from manim import *


class UnitCircleTemplate(VisualTemplate):
    VALID_STATES = frozenset({"base", "angle", "coordinates", "reference_triangle", "quadrants"})

    def __init__(
        self,
        state: str,
        *,
        angle_degrees: float = 30,
        angle_label: str | None = None,
        coordinate_label: str | None = None,
        cosine_label: str = r"\cos\theta",
        sine_label: str = r"\sin\theta",
        radius_label: str = "1",
        show_axes_labels: bool = True,
    ):
        state = self._validate_state(state)
        self._validate_angle(angle_degrees)
        self.angle_degrees = angle_degrees % 360
        self.angle_label_text = angle_label
        self.coordinate_label_text = coordinate_label
        self.cosine_label = cosine_label
        self.sine_label = sine_label
        self.radius_label = radius_label

        self.axes = Axes(
            x_range=[-1.5, 1.6, 0.5],
            y_range=[-1.5, 1.6, 0.5],
            x_length=5.4,
            y_length=5.4,
            tips=False,
            axis_config={"color": GREY_B, "stroke_width": 2},
        )
        axes_labels = (
            self.axes.get_axis_labels(MathTex("x", font_size=23), MathTex("y", font_size=23))
            if show_axes_labels
            else VGroup(VectorizedPoint())
        )
        self.circle = Circle(radius=self._unit_length(), color=TEAL_B, stroke_width=4).move_to(self.axes.c2p(0, 0))
        self.origin = Dot(self.axes.c2p(0, 0), radius=0.055, color=WHITE)
        self.angle_bundle = self._angle_bundle(self.angle_degrees, angle_label)
        self.coordinates_bundle = self._coordinates_bundle(self.angle_degrees, coordinate_label)
        self.reference_triangle_bundle = self._reference_triangle_bundle(self.angle_degrees)
        self.quadrants_bundle = self._quadrants_bundle()
        self._apply_state(state)
        boundary = Rectangle(width=7, height=6.2).move_to(self.axes).set_opacity(0)
        super().__init__(
            VGroup(self.axes, axes_labels),
            self.circle,
            self.origin,
            self.angle_bundle,
            self.coordinates_bundle,
            self.reference_triangle_bundle,
            self.quadrants_bundle,
            boundary,
            state=state,
        )

    def rotate_to_angle(
        self,
        target_degrees: float,
        angle_label: str | None = None,
        coordinate_label: str | None = None,
    ) -> Animation:
        self._validate_angle(target_degrees)
        self.angle_degrees = target_degrees % 360
        self.angle_label_text = angle_label
        self.coordinate_label_text = coordinate_label
        return AnimationGroup(
            Transform(self.angle_bundle, self._angle_bundle(self.angle_degrees, angle_label)),
            Transform(self.coordinates_bundle, self._coordinates_bundle(self.angle_degrees, coordinate_label)),
            Transform(self.reference_triangle_bundle, self._reference_triangle_bundle(self.angle_degrees)),
        )

    def reveal_coordinates(self) -> Animation:
        return AnimationGroup(self.coordinates_bundle.animate.set_opacity(1))

    def reveal_reference_triangle(self) -> Animation:
        return AnimationGroup(self.reference_triangle_bundle.animate.set_opacity(1))

    def highlight_quadrant(self, quadrant: int | None = None) -> Animation:
        active = self._quadrant(self.angle_degrees) if quadrant is None else quadrant
        if active not in {1, 2, 3, 4}:
            raise ValueError("quadrant must be one of 1, 2, 3, or 4")
        return Circumscribe(self.quadrants_bundle[active - 1], color=YELLOW, buff=0.08, fade_out=True)

    def highlight_projection(self, axis: str) -> Animation:
        if axis not in {"x", "y"}:
            raise ValueError("projection axis must be x or y")
        return Circumscribe(
            self.coordinates_bundle[0 if axis == "x" else 1],
            color=YELLOW,
            buff=0.08,
            fade_out=True,
        )

    def _apply_state(self, state: str) -> None:
        self.angle_bundle.set_opacity(1 if state != "base" else 0)
        self.coordinates_bundle.set_opacity(1 if state == "coordinates" else 0)
        self.reference_triangle_bundle.set_opacity(1 if state == "reference_triangle" else 0)
        self.quadrants_bundle.set_opacity(1 if state == "quadrants" else 0)

    def _angle_bundle(self, angle_degrees: float, label: str | None) -> VGroup:
        point = self._point(angle_degrees)
        radius = Arrow(self.axes.c2p(0, 0), point, buff=0, color=YELLOW, stroke_width=5)
        dot = Dot(point, radius=0.065, color=YELLOW)
        arc = Arc(
            radius=self._unit_length() * 0.32,
            start_angle=0,
            angle=math.radians(angle_degrees),
            arc_center=self.axes.c2p(0, 0),
            color=ORANGE,
        )
        text = MathTex(
            label or rf"{angle_degrees:g}^\circ",
            font_size=25,
            color=ORANGE,
        ).next_to(arc.point_from_proportion(0.55), UR, buff=0.05)
        radius_text = MathTex(self.radius_label, font_size=23, color=YELLOW).move_to(
            (self.axes.c2p(0, 0) + point) / 2 + UP * 0.14
        )
        return VGroup(radius, dot, arc, text, radius_text)

    def _coordinates_bundle(self, angle_degrees: float, label: str | None) -> VGroup:
        x, y = self._coordinates(angle_degrees)
        point = self.axes.c2p(x, y)
        x_point = self.axes.c2p(x, 0)
        x_projection = Line(self.axes.c2p(0, 0), x_point, color=BLUE_B, stroke_width=5)
        y_projection = Line(x_point, point, color=GREEN_B, stroke_width=5)
        text = MathTex(
            label or rf"({x:.2f},{y:.2f})",
            font_size=24,
            color=YELLOW,
        ).next_to(point, UR, buff=0.1)
        return VGroup(x_projection, y_projection, text)

    def _reference_triangle_bundle(self, angle_degrees: float) -> VGroup:
        x, y = self._coordinates(angle_degrees)
        origin, foot, point = self.axes.c2p(0, 0), self.axes.c2p(x, 0), self.axes.c2p(x, y)
        triangle = Polygon(origin, foot, point, color=WHITE, fill_color=BLUE_E, fill_opacity=0.2)
        cosine = MathTex(self.cosine_label, font_size=22, color=BLUE_B).next_to(Line(origin, foot), DOWN, buff=0.08)
        sine = MathTex(self.sine_label, font_size=22, color=GREEN_B).next_to(Line(foot, point), RIGHT, buff=0.08)
        return VGroup(triangle, cosine, sine)

    def _quadrants_bundle(self) -> VGroup:
        center = self.axes.c2p(0, 0)
        groups = VGroup()
        labels = (
            (r"\cos +,\ \sin +", UR),
            (r"\cos -,\ \sin +", UL),
            (r"\cos -,\ \sin -", DL),
            (r"\cos +,\ \sin -", DR),
        )
        for index, (text, direction) in enumerate(labels):
            sector = AnnularSector(
                inner_radius=0,
                outer_radius=self._unit_length(),
                angle=PI / 2,
                start_angle=index * PI / 2,
                fill_color=(TEAL_E, BLUE_E, RED_E, ORANGE)[index],
                fill_opacity=0.2,
                stroke_opacity=0,
            ).move_to(center)
            label = MathTex(text, font_size=18).move_to(center + direction * self._unit_length() * 0.54)
            groups.add(VGroup(sector, label))
        return groups

    def _point(self, angle_degrees: float):
        return self.axes.c2p(*self._coordinates(angle_degrees))

    @staticmethod
    def _coordinates(angle_degrees: float) -> tuple[float, float]:
        angle = math.radians(angle_degrees)
        return math.cos(angle), math.sin(angle)

    def _unit_length(self) -> float:
        return float(abs(self.axes.c2p(1, 0)[0] - self.axes.c2p(0, 0)[0]))

    @staticmethod
    def _quadrant(angle_degrees: float) -> int:
        return int((angle_degrees % 360) // 90) + 1

    @staticmethod
    def _validate_angle(angle_degrees: float) -> None:
        if not isinstance(angle_degrees, (int, float)) or not math.isfinite(angle_degrees):
            raise ValueError("angle_degrees must be a finite number")
