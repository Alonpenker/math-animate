import math

from manim import *


class FractionModelTemplate(VisualTemplate):
    VALID_STATES = frozenset({"bar", "grid", "circle"})
    MAX_WHOLES = 3

    def __init__(
        self,
        state: str,
        *,
        numerator: int = 1,
        denominator: int = 2,
        show_label: bool = True,
        label: str | None = None,
        grid_shape: tuple[int, int] | None = None,
        show_part_numbers: bool = False,
    ):
        state = self._validate_state(state)
        self.show_label = show_label
        self.custom_label = label
        self.grid_shape = grid_shape
        self.show_part_numbers = show_part_numbers
        self.numerator, self.denominator = self._validate_fraction(numerator, denominator)
        self.model, self.filled_parts, self.whole_groups = self._build_model(
            state,
            self.numerator,
            self.denominator,
        )
        self.label_group = self._label_group(self.numerator, self.denominator)
        content = VGroup(self.model, self.label_group).arrange(DOWN, buff=0.35)
        boundary = Rectangle(width=9.5, height=5.8).move_to(content).set_opacity(0)
        super().__init__(content, boundary, state=state)

    def set_fraction(self, numerator: int, denominator: int) -> Animation:
        numerator, denominator = self._validate_fraction(numerator, denominator)
        model, filled_parts, whole_groups = self._build_model(
            self.state,
            numerator,
            denominator,
        )
        target_label = self._label_group(numerator, denominator).move_to(self.label_group)
        model.move_to(self.model)
        self.numerator, self.denominator = numerator, denominator
        return AnimationGroup(
            Transform(self.model, model),
            Transform(self.label_group, target_label),
        )

    def show_equivalent_fraction(self, multiplier: int) -> Animation:
        if not isinstance(multiplier, int) or multiplier <= 1:
            raise ValueError("equivalent-fraction multiplier must be an integer greater than one")
        return self.set_fraction(
            self.numerator * multiplier,
            self.denominator * multiplier,
        )

    def highlight_filled_parts(self) -> Animation:
        filled_parts = self._current_filled_parts()
        if not filled_parts:
            raise ValueError("the fraction has no filled parts to highlight")
        return Indicate(filled_parts, color=YELLOW)

    def highlight_wholes(self) -> Animation:
        completed = min(self.numerator // self.denominator, len(self.model))
        if completed < 1:
            raise ValueError("highlight_wholes requires at least one completed whole")
        return AnimationGroup(*[
            Circumscribe(self.model[index], color=YELLOW, buff=0.1, fade_out=True)
            for index in range(completed)
        ])

    def _current_filled_parts(self) -> VGroup:
        parts = VGroup()
        remaining = self.numerator
        for whole in self.model:
            for part in whole:
                if remaining <= 0:
                    return parts
                parts.add(part)
                remaining -= 1
        return parts

    def _build_model(self, state: str, numerator: int, denominator: int):
        if state == "bar":
            return self._bar_model(numerator, denominator)
        if state == "grid":
            return self._grid_model(numerator, denominator)
        return self._circle_model(numerator, denominator)

    def _bar_model(self, numerator: int, denominator: int):
        whole_count = self._whole_count(numerator, denominator)
        groups = VGroup()
        filled = VGroup()
        part_width = 5.5 / denominator
        for whole_index in range(whole_count):
            cells = VGroup()
            for part_index in range(denominator):
                global_index = whole_index * denominator + part_index
                cell = Rectangle(
                    width=part_width,
                    height=0.72,
                    stroke_color=WHITE,
                    fill_color=TEAL_B,
                    fill_opacity=0.72 if global_index < numerator else 0.05,
                )
                if self.show_part_numbers:
                    cell.add(MathTex(str(global_index + 1), font_size=18).move_to(cell))
                cells.add(cell)
                if global_index < numerator:
                    filled.add(cell)
            cells.arrange(RIGHT, buff=0)
            groups.add(cells)
        groups.arrange(DOWN, buff=0.28)
        return groups, filled, groups

    def _grid_model(self, numerator: int, denominator: int):
        rows, columns = self._grid_dimensions(denominator)
        whole_count = self._whole_count(numerator, denominator)
        groups = VGroup()
        filled = VGroup()
        for whole_index in range(whole_count):
            cells = VGroup()
            for part_index in range(denominator):
                global_index = whole_index * denominator + part_index
                cell = Square(
                    side_length=min(0.72, 3.4 / max(rows, columns)),
                    stroke_color=WHITE,
                    fill_color=TEAL_B,
                    fill_opacity=0.72 if global_index < numerator else 0.05,
                )
                if self.show_part_numbers:
                    cell.add(MathTex(str(global_index + 1), font_size=16).move_to(cell))
                cells.add(cell)
                if global_index < numerator:
                    filled.add(cell)
            cells.arrange_in_grid(rows=rows, cols=columns, buff=0)
            groups.add(cells)
        groups.arrange(RIGHT, buff=0.42)
        return groups, filled, groups

    def _circle_model(self, numerator: int, denominator: int):
        if denominator > 12:
            raise ValueError("circle state supports denominators up to twelve")
        whole_count = self._whole_count(numerator, denominator)
        groups = VGroup()
        filled = VGroup()
        for whole_index in range(whole_count):
            sectors = VGroup()
            for part_index in range(denominator):
                global_index = whole_index * denominator + part_index
                sector = Sector(
                    radius=1.05,
                    angle=TAU / denominator,
                    start_angle=part_index * TAU / denominator,
                    stroke_color=WHITE,
                    fill_color=TEAL_B,
                    fill_opacity=0.72 if global_index < numerator else 0.05,
                )
                sectors.add(sector)
                if global_index < numerator:
                    filled.add(sector)
            groups.add(sectors)
        groups.arrange(RIGHT, buff=0.42)
        return groups, filled, groups

    def _label_group(self, numerator: int, denominator: int) -> VGroup:
        if not self.show_label:
            return VGroup(VectorizedPoint())
        text = self.custom_label or rf"\frac{{{numerator}}}{{{denominator}}}"
        return VGroup(MathTex(text, font_size=34, color=YELLOW))

    def _grid_dimensions(self, denominator: int) -> tuple[int, int]:
        if self.grid_shape is not None:
            if (
                not isinstance(self.grid_shape, (list, tuple))
                or len(self.grid_shape) != 2
                or any(not isinstance(value, int) or value <= 0 for value in self.grid_shape)
                or self.grid_shape[0] * self.grid_shape[1] != denominator
            ):
                raise ValueError("grid_shape must contain two positive integers whose product is denominator")
            return tuple(self.grid_shape)
        rows = int(math.sqrt(denominator))
        while rows > 1 and denominator % rows:
            rows -= 1
        return rows, denominator // rows

    @classmethod
    def _validate_fraction(cls, numerator: int, denominator: int) -> tuple[int, int]:
        if not isinstance(numerator, int) or numerator < 0:
            raise ValueError("numerator must be a nonnegative integer")
        if not isinstance(denominator, int) or denominator <= 0:
            raise ValueError("denominator must be a positive integer")
        if cls._whole_count(numerator, denominator) > cls.MAX_WHOLES:
            raise ValueError("fraction model supports at most three wholes")
        return numerator, denominator

    @staticmethod
    def _whole_count(numerator: int, denominator: int) -> int:
        return max(1, math.ceil(numerator / denominator))
