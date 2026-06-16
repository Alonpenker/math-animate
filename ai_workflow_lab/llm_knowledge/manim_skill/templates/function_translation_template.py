from manim import *


class FunctionTranslationTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "parent",
        "horizontal_shift",
        "vertical_shift",
        "combined_shift",
        "comparison",
    })

    def __init__(
        self,
        state: str,
        parent_function=lambda x: x**2,
        *,
        h: float = 0,
        k: float = 0,
        anchor_point: tuple[float, float] | None = (0, 0),
        x_range: tuple[float, float, float] = (-4, 5, 1),
        y_range: tuple[float, float, float] = (-3, 7, 1),
        graph_x_range: tuple[float, float] = (-2.4, 2.4),
        parent_label: str = r"f(x)",
        transformed_label: str = r"f(x-h)+k",
    ):
        state = self._validate_state(state)
        self.h, self.k = self._active_translation(state, h=h, k=k)
        self.anchor_point = anchor_point
        self.axes = Axes(
            x_range=list(x_range),
            y_range=list(y_range),
            x_length=6.4,
            y_length=4.8,
            tips=False,
            axis_config={"color": GREY_B, "stroke_width": 2},
        )
        axis_labels = self.axes.get_axis_labels(
            MathTex("x", font_size=24),
            MathTex("y", font_size=24),
        )
        axes_group = VGroup(self.axes, axis_labels)

        parent_graph = self.axes.plot(
            parent_function,
            x_range=list(graph_x_range),
            color=TEAL_B,
            stroke_width=4,
        )
        active_graph = self.axes.plot(
            lambda x: parent_function(x - self.h) + self.k,
            x_range=[graph_x_range[0] + self.h, graph_x_range[1] + self.h],
            color=YELLOW,
            stroke_width=5,
        )
        parent_graph_label = self.axes.get_graph_label(
            parent_graph,
            label=MathTex(parent_label, font_size=27, color=TEAL_B),
            x_val=graph_x_range[1] - 0.45,
            direction=UR,
        )
        active_graph_label = self.axes.get_graph_label(
            active_graph,
            label=MathTex(
                parent_label if state == "parent" else transformed_label,
                font_size=27,
                color=YELLOW,
            ),
            x_val=graph_x_range[1] + self.h - 0.45,
            direction=UR,
        )

        self.active_graph_bundle = VGroup(active_graph, active_graph_label)
        reference_graph_bundle = VGroup(parent_graph, parent_graph_label)
        if state != "comparison":
            reference_graph_bundle.set_opacity(0)

        self.active_anchor = self._anchor_marker(
            self.axes,
            anchor_point,
            h=self.h,
            k=self.k,
            color=YELLOW,
        )
        reference_anchor = self._anchor_marker(
            self.axes,
            anchor_point,
            h=0,
            k=0,
            color=TEAL_B,
        )
        if state != "comparison":
            reference_anchor.set_opacity(0)

        annotations = self._annotations(
            self.axes,
            anchor_point,
            state=state,
            h=self.h,
            k=self.k,
        )
        plot_boundary = Rectangle(
            width=self.axes.width + 1.4,
            height=self.axes.height + 0.8,
        ).move_to(self.axes).set_opacity(0)
        super().__init__(
            axes_group,
            self.active_graph_bundle,
            self.active_anchor,
            reference_graph_bundle,
            reference_anchor,
            annotations,
            plot_boundary,
            state=state,
        )

    def shift_horizontal(self, target_h: float) -> Animation:
        delta = self.axes.c2p(target_h, self.k) - self.axes.c2p(self.h, self.k)
        self.h = target_h
        target_anchor = self._anchor_marker(
            self.axes,
            self.anchor_point,
            h=self.h,
            k=self.k,
            color=YELLOW,
        )
        return AnimationGroup(
            self.active_graph_bundle.animate.shift(delta),
            Transform(self.active_anchor, target_anchor),
        )

    def shift_vertical(self, target_k: float) -> Animation:
        delta = self.axes.c2p(self.h, target_k) - self.axes.c2p(self.h, self.k)
        self.k = target_k
        target_anchor = self._anchor_marker(
            self.axes,
            self.anchor_point,
            h=self.h,
            k=self.k,
            color=YELLOW,
        )
        return AnimationGroup(
            self.active_graph_bundle.animate.shift(delta),
            Transform(self.active_anchor, target_anchor),
        )

    @staticmethod
    def _active_translation(state: str, *, h: float, k: float) -> tuple[float, float]:
        if state == "parent":
            return 0, 0
        if state == "horizontal_shift":
            return h, 0
        if state == "vertical_shift":
            return h, k
        return h, k

    @staticmethod
    def _anchor_marker(
        axes: Axes,
        anchor_point: tuple[float, float] | None,
        *,
        h: float,
        k: float,
        color: ManimColor,
    ) -> VGroup:
        if anchor_point is None:
            return VGroup(VectorizedPoint(axes.c2p(0, 0)))
        x, y = anchor_point
        shifted_x, shifted_y = x + h, y + k
        dot = Dot(axes.c2p(shifted_x, shifted_y), radius=0.065, color=color)
        label = MathTex(
            rf"({shifted_x:g},{shifted_y:g})",
            font_size=24,
            color=color,
        ).next_to(dot, UR, buff=0.08)
        return VGroup(dot, label)

    @classmethod
    def _annotations(
        cls,
        axes: Axes,
        anchor_point: tuple[float, float] | None,
        *,
        state: str,
        h: float,
        k: float,
    ) -> VGroup:
        if anchor_point is None:
            return VGroup(
                VectorizedPoint(axes.c2p(0, 0)),
                VectorizedPoint(axes.c2p(0, 0)),
            )

        x, y = anchor_point
        horizontal = cls._arrow_or_placeholder(
            axes.c2p(x, y),
            axes.c2p(x + h, y),
            color=ORANGE,
        )
        vertical = cls._arrow_or_placeholder(
            axes.c2p(x + h, y),
            axes.c2p(x + h, y + k),
            color=GREEN_B,
        )
        if state not in {"horizontal_shift", "combined_shift", "comparison"}:
            horizontal.set_opacity(0)
        if state not in {"vertical_shift", "combined_shift", "comparison"}:
            vertical.set_opacity(0)
        return VGroup(horizontal, vertical)

    @staticmethod
    def _arrow_or_placeholder(start, end, *, color: ManimColor) -> VGroup:
        if all(abs(value) < 1e-9 for value in end - start):
            return VGroup(VectorizedPoint(start))
        return VGroup(
            Arrow(
                start,
                end,
                buff=0,
                color=color,
                stroke_width=4,
            )
        )
