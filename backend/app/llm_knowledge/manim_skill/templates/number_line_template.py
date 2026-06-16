from manim import *


class NumberLineTemplate(VisualTemplate):
    VALID_STATES = frozenset({"points", "interval", "intervals", "operation", "distance"})

    def __init__(
        self,
        state: str,
        *,
        x_range: tuple[float, float, float] = (-5, 6, 1),
        points: list[float] | tuple[float, ...] = (),
        point_labels: list[str] | tuple[str, ...] | None = None,
        start: float = -2,
        end: float = 2,
        left_closed: bool = True,
        right_closed: bool = True,
        intervals: list[tuple[float, float, bool, bool]] | tuple[tuple[float, float, bool, bool], ...] = (),
        excluded_points: list[float] | tuple[float, ...] = (),
        value: float = 0,
        value_label: str | None = None,
        title: str | None = None,
        center: float | None = None,
        radius: float | None = None,
    ):
        state = self._validate_state(state)
        self.number_line = NumberLine(
            x_range=list(x_range),
            length=9,
            include_numbers=True,
            font_size=25,
            color=GREY_B,
        )
        self.value = value
        self.interval = (start, end, left_closed, right_closed)
        title_bundle = (
            VGroup(MathTex(title, font_size=24, color=GREY_A).next_to(self.number_line, UP, buff=0.42))
            if title
            else VGroup(VectorizedPoint())
        )

        labels = list(point_labels) if point_labels is not None else [f"{point:g}" for point in points]
        if len(labels) != len(points):
            raise ValueError("point_labels must match points length")
        point_bundle = (
            VGroup(*[
                self._point_marker(self.number_line, point, label, color=TEAL_B)
                for point, label in zip(points, labels)
            ])
            if state == "points"
            else VGroup(VectorizedPoint())
        )
        self.interval_bundle = VGroup(VectorizedPoint())
        if state == "interval":
            self.interval_bundle = self._interval_bundle(
                self.number_line,
                start,
                end,
                left_closed=left_closed,
                right_closed=right_closed,
            )
        elif state == "intervals":
            if not intervals:
                raise ValueError("intervals state requires at least one interval")
            self.interval_bundle = VGroup(*[
                self._interval_bundle(
                    self.number_line,
                    interval_start,
                    interval_end,
                    left_closed=interval_left_closed,
                    right_closed=interval_right_closed,
                )
                for interval_start, interval_end, interval_left_closed, interval_right_closed in intervals
            ])
        self.excluded_bundle = (
            VGroup(*[
                self._endpoint(self.number_line.n2p(point), False, color=RED)
                for point in excluded_points
            ])
            if state == "intervals"
            else VGroup(VectorizedPoint())
        )
        self.active_point = (
            self._point_marker(
                self.number_line,
                value,
                value_label or f"{value:g}",
                color=YELLOW,
            )
            if state == "operation"
            else VGroup(VectorizedPoint())
        )
        self.distance_bundle = (
            self._radius_distance_bundle(self.number_line, center, radius)
            if state == "distance" and (center is not None or radius is not None)
            else self._distance_bundle(self.number_line, start, end)
            if state == "distance"
            else VGroup(VectorizedPoint())
        )

        boundary = Rectangle(width=10, height=3.4).set_opacity(0)
        super().__init__(
            self.number_line,
            title_bundle,
            point_bundle,
            self.interval_bundle,
            self.excluded_bundle,
            self.active_point,
            self.distance_bundle,
            boundary,
            state=state,
        )

    def move_point(self, target_value: float) -> Animation:
        if self.state != "operation":
            raise ValueError("move_point is only available in operation state")
        self._validate_value(self.number_line, target_value)
        start_point = self.number_line.n2p(self.value)
        end_point = self.number_line.n2p(target_value)
        direction = UP if target_value >= self.value else DOWN
        jump = CurvedArrow(
            start_point,
            end_point,
            angle=-TAU / 4 if direction is UP else TAU / 4,
            color=ORANGE,
        )
        self.add(jump)
        target = self._point_marker(
            self.number_line,
            target_value,
            f"{target_value:g}",
            color=YELLOW,
        )
        self.value = target_value
        return Succession(
            Create(jump),
            Transform(self.active_point, target),
            FadeOut(jump),
        )

    def set_interval(
        self,
        start: float,
        end: float,
        left_closed: bool,
        right_closed: bool,
    ) -> Animation:
        if self.state != "interval":
            raise ValueError("set_interval is only available in interval state")
        target = self._interval_bundle(
            self.number_line,
            start,
            end,
            left_closed=left_closed,
            right_closed=right_closed,
        )
        self.interval = (start, end, left_closed, right_closed)
        return Transform(self.interval_bundle, target)

    def highlight_distance(self) -> Animation:
        if self.state != "distance":
            raise ValueError("highlight_distance is only available in distance state")
        return Circumscribe(self.distance_bundle, color=YELLOW, buff=0.12, fade_out=True)

    @staticmethod
    def _validate_value(number_line: NumberLine, value: float) -> None:
        minimum, maximum, _ = number_line.x_range
        if not minimum <= value <= maximum:
            raise ValueError("number-line values must be inside x_range")

    @classmethod
    def _point_marker(
        cls,
        number_line: NumberLine,
        value: float,
        label: str,
        *,
        color: ManimColor,
    ) -> VGroup:
        cls._validate_value(number_line, value)
        dot = Dot(number_line.n2p(value), radius=0.075, color=color)
        text = MathTex(label, font_size=27, color=color).next_to(dot, UP, buff=0.12)
        return VGroup(dot, text)

    @classmethod
    def _interval_bundle(
        cls,
        number_line: NumberLine,
        start: float,
        end: float,
        *,
        left_closed: bool,
        right_closed: bool,
    ) -> VGroup:
        cls._validate_value(number_line, start)
        cls._validate_value(number_line, end)
        if start >= end:
            raise ValueError("interval start must be less than end")
        segment = Line(number_line.n2p(start), number_line.n2p(end), color=TEAL_B, stroke_width=8)
        endpoints = VGroup(
            cls._endpoint(number_line.n2p(start), left_closed),
            cls._endpoint(number_line.n2p(end), right_closed),
        )
        return VGroup(segment, endpoints)

    @staticmethod
    def _endpoint(point, closed: bool, color: ManimColor = YELLOW) -> Mobject:
        if closed:
            return Dot(point, radius=0.085, color=color)
        return Circle(radius=0.085, color=color, fill_opacity=0).move_to(point)

    @classmethod
    def _distance_bundle(cls, number_line: NumberLine, start: float, end: float) -> VGroup:
        cls._validate_value(number_line, start)
        cls._validate_value(number_line, end)
        if start == end:
            raise ValueError("distance points must be distinct")
        left, right = sorted((start, end))
        brace = BraceBetweenPoints(
            number_line.n2p(left) + DOWN * 0.35,
            number_line.n2p(right) + DOWN * 0.35,
            direction=DOWN,
        )
        label = MathTex(rf"|{end:g}-{start:g}|={abs(end - start):g}", font_size=30)
        label.next_to(brace, DOWN, buff=0.12)
        markers = VGroup(
            cls._point_marker(number_line, start, f"{start:g}", color=TEAL_B),
            cls._point_marker(number_line, end, f"{end:g}", color=ORANGE),
        )
        return VGroup(markers, brace, label)

    @classmethod
    def _radius_distance_bundle(cls, number_line: NumberLine, center: float | None, radius: float | None) -> VGroup:
        if center is None or radius is None or radius <= 0:
            raise ValueError("center and a positive radius are required together")
        left, right = center - radius, center + radius
        cls._validate_value(number_line, left)
        cls._validate_value(number_line, right)
        braces = VGroup(
            BraceBetweenPoints(number_line.n2p(left) + DOWN * 0.35, number_line.n2p(center) + DOWN * 0.35, direction=DOWN),
            BraceBetweenPoints(number_line.n2p(center) + DOWN * 0.35, number_line.n2p(right) + DOWN * 0.35, direction=DOWN),
        )
        labels = VGroup(*[
            MathTex(f"{radius:g}", font_size=26).next_to(brace, DOWN, buff=0.1)
            for brace in braces
        ])
        markers = VGroup(
            cls._point_marker(number_line, left, f"{left:g}", color=TEAL_B),
            cls._point_marker(number_line, center, f"{center:g}", color=YELLOW),
            cls._point_marker(number_line, right, f"{right:g}", color=ORANGE),
        )
        return VGroup(markers, braces, labels)
