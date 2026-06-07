from manim import *


def make_function_translation_model(
    parent_function,
    state,
    *,
    h: float = 0,
    k: float = 0,
    anchor_point: tuple[float, float] | None = None,
    x_range: tuple[float, float, float] = (-4, 5, 1),
    y_range: tuple[float, float, float] = (-3, 7, 1),
    graph_x_range: tuple[float, float] = (-2.4, 2.4),
    parent_label: str = r"f(x)",
    transformed_label: str = r"f(x-h)+k",
) -> VGroup:
    """Return compatible fixed-axis snapshots for function translations."""
    if state not in {
        "parent",
        "horizontal_shift",
        "vertical_shift",
        "combined_shift",
        "comparison",
    }:
        raise ValueError(f"Unknown function-translation state: {state}")

    active_h, active_k = _function_translation_active_translation(state, h=h, k=k)
    axes = Axes(
        x_range=list(x_range),
        y_range=list(y_range),
        x_length=6.4,
        y_length=4.8,
        tips=False,
        axis_config={"color": GREY_B, "stroke_width": 2},
    )
    axis_labels = axes.get_axis_labels(
        MathTex("x", font_size=24),
        MathTex("y", font_size=24),
    )
    axes_group = VGroup(axes, axis_labels)

    parent_graph = axes.plot(
        parent_function,
        x_range=list(graph_x_range),
        color=TEAL_B,
        stroke_width=4,
    )
    active_graph = axes.plot(
        lambda x: parent_function(x - active_h) + active_k,
        x_range=[graph_x_range[0] + active_h, graph_x_range[1] + active_h],
        color=YELLOW,
        stroke_width=5,
    )
    parent_graph_label = axes.get_graph_label(
        parent_graph,
        label=MathTex(parent_label, font_size=27, color=TEAL_B),
        x_val=graph_x_range[1] - 0.45,
        direction=UR,
    )
    active_graph_label = axes.get_graph_label(
        active_graph,
        label=MathTex(
            parent_label if state == "parent" else transformed_label,
            font_size=27,
            color=YELLOW,
        ),
        x_val=graph_x_range[1] + active_h - 0.45,
        direction=UR,
    )

    active_graph_bundle = VGroup(active_graph, active_graph_label)
    reference_graph_bundle = VGroup(parent_graph, parent_graph_label)
    if state != "comparison":
        reference_graph_bundle.set_opacity(0)

    active_anchor = _function_translation_anchor_marker(
        axes,
        anchor_point,
        h=active_h,
        k=active_k,
        color=YELLOW,
    )
    reference_anchor = _function_translation_anchor_marker(
        axes,
        anchor_point,
        h=0,
        k=0,
        color=TEAL_B,
    )
    if state != "comparison":
        reference_anchor.set_opacity(0)

    annotations = _function_translation_annotations(
        axes,
        anchor_point,
        state=state,
        h=h,
        k=k,
    )
    plot_boundary = Rectangle(
        width=axes.width + 1.4,
        height=axes.height + 0.8,
    ).move_to(axes).set_opacity(0)
    return VGroup(
        axes_group,
        active_graph_bundle,
        active_anchor,
        reference_graph_bundle,
        reference_anchor,
        annotations,
        plot_boundary,
    )


def _function_translation_active_translation(
    state,
    *,
    h: float,
    k: float,
) -> tuple[float, float]:
    if state == "parent":
        return 0, 0
    if state == "horizontal_shift":
        return h, 0
    if state == "vertical_shift":
        return h, k
    return h, k


def _function_translation_anchor_marker(
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


def _function_translation_annotations(
    axes: Axes,
    anchor_point: tuple[float, float] | None,
    *,
    state,
    h: float,
    k: float,
) -> VGroup:
    if anchor_point is None:
        return VGroup(VectorizedPoint(axes.c2p(0, 0)), VectorizedPoint(axes.c2p(0, 0)))

    x, y = anchor_point
    horizontal = _function_translation_arrow_or_placeholder(
        axes.c2p(x, y),
        axes.c2p(x + h, y),
        color=ORANGE,
    )
    vertical_x = x + h
    vertical = _function_translation_arrow_or_placeholder(
        axes.c2p(vertical_x, y),
        axes.c2p(vertical_x, y + k),
        color=GREEN_B,
    )
    if state not in {"horizontal_shift", "combined_shift", "comparison"}:
        horizontal.set_opacity(0)
    if state not in {"vertical_shift", "combined_shift", "comparison"}:
        vertical.set_opacity(0)
    return VGroup(horizontal, vertical)


def _function_translation_arrow_or_placeholder(start, end, *, color: ManimColor) -> VGroup:
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
