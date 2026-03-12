from manim import *


GRAPH_COLOR = BLUE_D
LIMIT_COLOR = YELLOW_E
VALUE_COLOR = RED_D
HIGHLIGHT_COLOR = ORANGE


def make_cancel_mark(target: Mobject, color: str = HIGHLIGHT_COLOR) -> VGroup:
    slash = Line(
        target.get_corner(UL) + RIGHT * 0.04 + DOWN * 0.02,
        target.get_corner(DR) + LEFT * 0.04 + UP * 0.02,
        color=color,
        stroke_width=6,
    )
    accent = slash.copy().shift(UP * 0.08 + RIGHT * 0.05).set_stroke(width=3)
    return VGroup(slash, accent)


def make_warning_badge() -> VGroup:
    zero_over_zero = MathTex(r"\frac{0}{0}", font_size=30, color=HIGHLIGHT_COLOR)
    badge = RoundedRectangle(
        corner_radius=0.16,
        width=1.35,
        height=1.0,
        stroke_color=HIGHLIGHT_COLOR,
        fill_color=BLACK,
        fill_opacity=0.2,
    )
    zero_over_zero.move_to(badge.get_center())
    return VGroup(badge, zero_over_zero)


def build_factored_limit_expression(
    limit_tex: str,
    cancelled_factor: str,
    remaining_factor: str,
    font_size: int,
) -> tuple[VGroup, Mobject, Mobject]:
    prefix = MathTex(limit_tex, font_size=font_size)
    numerator_cancel = MathTex(f"({cancelled_factor})", font_size=font_size, color=HIGHLIGHT_COLOR)
    numerator_keep = MathTex(f"({remaining_factor})", font_size=font_size, color=GRAPH_COLOR)
    numerator = VGroup(numerator_cancel, numerator_keep).arrange(RIGHT, buff=0.08)

    denominator = MathTex(cancelled_factor, font_size=font_size, color=HIGHLIGHT_COLOR)
    fraction_width = max(numerator.width + 0.2, denominator.width + 0.35)
    fraction_bar = Line(
        LEFT * (fraction_width / 2),
        RIGHT * (fraction_width / 2),
        color=WHITE,
        stroke_width=4,
    )
    numerator.next_to(fraction_bar, UP, buff=0.12)
    denominator.next_to(fraction_bar, DOWN, buff=0.18)

    fraction = VGroup(numerator, fraction_bar, denominator)
    expression = VGroup(prefix, fraction).arrange(RIGHT, buff=0.16, aligned_edge=DOWN)
    return expression, numerator_cancel, denominator


def build_fraction_layout(numerator: Mobject, denominator: Mobject) -> VGroup:
    fraction_width = max(numerator.width + 0.2, denominator.width + 0.35)
    fraction_bar = Line(
        LEFT * (fraction_width / 2),
        RIGHT * (fraction_width / 2),
        color=WHITE,
        stroke_width=4,
    )
    numerator.next_to(fraction_bar, UP, buff=0.12)
    denominator.next_to(fraction_bar, DOWN, buff=0.18)
    return VGroup(numerator, fraction_bar, denominator)


def build_limit_with_value(limit_value: str, content: Mobject, font_size: int) -> VGroup:
    prefix = MathTex(rf"\lim_{{x\to {limit_value}}}", font_size=font_size)
    expression = VGroup(prefix, content).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
    return expression


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("What the Limit Approaches", font_size=38, weight=BOLD).to_edge(UP, buff=0.3)

        plane = NumberPlane(
            x_range=[-1, 5, 1],
            y_range=[0, 6, 1],
            x_length=7.2,
            y_length=4.6,
            background_line_style={
                "stroke_color": BLUE_E,
                "stroke_opacity": 0.25,
                "stroke_width": 1,
            },
            axis_config={"include_numbers": True, "font_size": 22},
        ).shift(DOWN * 0.35)
        axis_labels = plane.get_axis_labels(MathTex("x"), MathTex("y"))

        graph_left = plane.plot(lambda x: x + 2, x_range=[-0.5, 1.94], color=GRAPH_COLOR, stroke_width=6)
        graph_right = plane.plot(lambda x: x + 2, x_range=[2.06, 4.3], color=GRAPH_COLOR, stroke_width=6)

        hole = Circle(radius=0.11, color=LIMIT_COLOR, stroke_width=4)
        hole.set_fill(opacity=0)
        hole.move_to(plane.c2p(2, 4))

        hole_coordinate = MathTex("(2,4)", font_size=28, color=LIMIT_COLOR).next_to(hole, UP + RIGHT, buff=0.12)

        limit_label = MathTex(r"\lim_{x\to 2} f(x)=4", font_size=40, color=LIMIT_COLOR)
        limit_label.next_to(title, DOWN, buff=0.28)
        limit_label.to_edge(LEFT, buff=0.55)

        limit_arrow = CurvedArrow(
            limit_label.get_right() + RIGHT * 0.1,
            hole.get_left() + UP * 0.05,
            angle=-0.35 * PI,
            color=LIMIT_COLOR,
            stroke_width=4,
        )

        left_tracker = Dot(plane.c2p(0.3, 2.3), color=WHITE, radius=0.07)
        right_tracker = Dot(plane.c2p(4.0, 6.0), color=WHITE, radius=0.07)

        closing_note = Text(
            "As x gets close to 2, the graph approaches 4.",
            font_size=24,
            color=WHITE,
        ).to_edge(DOWN, buff=0.35)

        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.8)
        self.wait(1)

        self.play(Create(plane), FadeIn(axis_labels), run_time=1.0)
        self.wait(1)

        self.play(Create(graph_left), Create(graph_right), run_time=1.0)
        self.wait(1)

        self.play(
            FadeIn(hole, scale=0.8),
            FadeIn(hole_coordinate, shift=UP * 0.1),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            FadeIn(limit_label, shift=RIGHT * 0.1),
            Create(limit_arrow),
            run_time=0.8,
        )
        self.play(Indicate(hole, color=LIMIT_COLOR, scale_factor=1.2), run_time=0.8)
        self.wait(1)

        self.play(FadeIn(left_tracker), FadeIn(right_tracker), run_time=0.4)
        self.play(
            left_tracker.animate.move_to(plane.c2p(1.85, 3.85)),
            right_tracker.animate.move_to(plane.c2p(2.15, 4.15)),
            run_time=1.3,
        )
        self.wait(0.8)
        self.play(FadeOut(left_tracker), FadeOut(right_tracker), run_time=0.4)

        self.play(FadeIn(closing_note, shift=UP * 0.1), run_time=0.8)
        self.wait(1.5)


class Scene2(Scene):
    def construct(self) -> None:
        title = Text("Simplify a Hole Before Substituting", font_size=36, weight=BOLD).to_edge(UP, buff=0.3)
        top_center = UP * 1.45
        calc_center = DOWN * 0.1

        first_numerator = MathTex("x^2-4", font_size=58)
        first_denominator = MathTex("x-2", font_size=58)
        first_fraction = build_fraction_layout(first_numerator, first_denominator)
        first_start = build_limit_with_value("2", first_fraction, 58)
        first_start.move_to(top_center)

        first_direct_fraction = build_fraction_layout(
            MathTex("2^2-4", font_size=50),
            MathTex("2-2", font_size=50),
        )
        first_direct_fraction.move_to(calc_center)
        first_direct_equal = MathTex("=", font_size=50).next_to(first_direct_fraction, RIGHT, buff=0.25)
        first_indeterminate = MathTex(r"\frac{0}{0}", font_size=50, color=HIGHLIGHT_COLOR).next_to(
            first_direct_equal, RIGHT, buff=0.25
        )
        first_warning_text = Text("Direct substitution gives an indeterminate form.", font_size=24, color=HIGHLIGHT_COLOR)
        first_warning_text.next_to(VGroup(first_direct_fraction, first_direct_equal, first_indeterminate), DOWN, buff=0.22)

        first_factored_cancel = MathTex("(x-2)", font_size=58)
        first_factored_keep = MathTex("(x+2)", font_size=58)
        first_factored_denominator = MathTex("x-2", font_size=58)
        first_factored_fraction = build_fraction_layout(
            VGroup(first_factored_cancel, first_factored_keep).arrange(RIGHT, buff=0.08),
            first_factored_denominator,
        )
        first_factored = build_limit_with_value("2", first_factored_fraction, 58)
        first_factored.move_to(top_center)
        first_cancel_marks = VGroup(
            make_cancel_mark(first_factored_cancel),
            make_cancel_mark(first_factored_denominator),
        )

        first_simple_term = MathTex("(x+2)", font_size=58, color=GRAPH_COLOR)
        first_simple = build_limit_with_value("2", first_simple_term, 58)
        first_simple.move_to(top_center)

        first_substituted = MathTex("(2+2)", font_size=54, color=GRAPH_COLOR).move_to(calc_center)
        first_result = MathTex("=", "4", font_size=54).next_to(first_substituted, RIGHT, buff=0.25)
        first_result[1].set_color(GREEN_E)

        second_numerator = MathTex("x^2-1", font_size=50)
        second_denominator = MathTex("x-1", font_size=50)
        second_fraction = build_fraction_layout(second_numerator, second_denominator)
        second_start = build_limit_with_value("1", second_fraction, 50)
        second_start.move_to(top_center)

        second_direct_fraction = build_fraction_layout(
            MathTex("1^2-1", font_size=46),
            MathTex("1-1", font_size=46),
        )
        second_direct_fraction.move_to(calc_center)
        second_direct_equal = MathTex("=", font_size=46).next_to(second_direct_fraction, RIGHT, buff=0.25)
        second_indeterminate = MathTex(r"\frac{0}{0}", font_size=46, color=HIGHLIGHT_COLOR).next_to(
            second_direct_equal, RIGHT, buff=0.25
        )
        second_warning_text = Text("Direct substitution gives an indeterminate form.", font_size=24, color=HIGHLIGHT_COLOR)
        second_warning_text.next_to(VGroup(second_direct_fraction, second_direct_equal, second_indeterminate), DOWN, buff=0.22)

        second_factored_cancel = MathTex("(x-1)", font_size=50)
        second_factored_keep = MathTex("(x+1)", font_size=50)
        second_factored_denominator = MathTex("x-1", font_size=50)
        second_factored_fraction = build_fraction_layout(
            VGroup(second_factored_cancel, second_factored_keep).arrange(RIGHT, buff=0.08),
            second_factored_denominator,
        )
        second_factored = build_limit_with_value("1", second_factored_fraction, 50)
        second_factored.move_to(top_center)
        second_cancel_marks = VGroup(
            make_cancel_mark(second_factored_cancel),
            make_cancel_mark(second_factored_denominator),
        )

        second_simple_term = MathTex("(x+1)", font_size=50, color=GRAPH_COLOR)
        second_simple = build_limit_with_value("1", second_simple_term, 50)
        second_simple.move_to(top_center)

        second_substituted = MathTex("(1+1)", font_size=50, color=GRAPH_COLOR).move_to(calc_center)
        second_result = MathTex("=", "2", font_size=50).next_to(second_substituted, RIGHT, buff=0.25)
        second_result[1].set_color(GREEN_E)

        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.8)
        self.wait(1)

        self.play(Write(first_start), run_time=1.0)
        self.wait(1)

        self.play(
            TransformFromCopy(first_fraction, first_direct_fraction),
            run_time=0.9,
        )
        self.wait(0.8)

        self.play(
            FadeIn(first_direct_equal, shift=RIGHT * 0.05),
            FadeIn(first_indeterminate, shift=RIGHT * 0.05),
            FadeIn(first_warning_text, shift=UP * 0.05),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            FadeOut(first_direct_fraction),
            FadeOut(first_direct_equal),
            FadeOut(first_indeterminate),
            FadeOut(first_warning_text),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(ReplacementTransform(first_start, first_factored), run_time=1.0)
        self.wait(0.8)

        self.play(
            first_factored_cancel.animate.set_color(HIGHLIGHT_COLOR),
            first_factored_denominator.animate.set_color(HIGHLIGHT_COLOR),
            first_factored_keep.animate.set_color(GRAPH_COLOR),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(Create(first_cancel_marks), run_time=0.8)
        self.wait(0.8)

        self.play(
            ReplacementTransform(first_factored, first_simple),
            FadeOut(first_cancel_marks),
            run_time=1.0,
        )
        self.wait(1)

        self.play(
            TransformFromCopy(first_simple_term, first_substituted),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(FadeIn(first_result, shift=RIGHT * 0.05), run_time=0.6)
        self.wait(1)

        self.play(
            FadeOut(first_simple),
            FadeOut(first_substituted),
            FadeOut(first_result),
            run_time=0.8,
        )
        self.wait(0.6)

        self.play(Write(second_start), run_time=0.9)
        self.wait(0.8)

        self.play(
            TransformFromCopy(second_fraction, second_direct_fraction),
            run_time=0.9,
        )
        self.wait(0.8)

        self.play(
            FadeIn(second_direct_equal, shift=RIGHT * 0.05),
            FadeIn(second_indeterminate, shift=RIGHT * 0.05),
            FadeIn(second_warning_text, shift=UP * 0.05),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            FadeOut(second_direct_fraction),
            FadeOut(second_direct_equal),
            FadeOut(second_indeterminate),
            FadeOut(second_warning_text),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(ReplacementTransform(second_start, second_factored), run_time=1.0)
        self.wait(0.8)

        self.play(
            second_factored_cancel.animate.set_color(HIGHLIGHT_COLOR),
            second_factored_denominator.animate.set_color(HIGHLIGHT_COLOR),
            second_factored_keep.animate.set_color(GRAPH_COLOR),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(Create(second_cancel_marks), run_time=0.8)
        self.wait(0.8)

        self.play(
            ReplacementTransform(second_factored, second_simple),
            FadeOut(second_cancel_marks),
            run_time=1.0,
        )
        self.wait(1)

        self.play(
            TransformFromCopy(second_simple_term, second_substituted),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(FadeIn(second_result, shift=RIGHT * 0.05), run_time=0.6)
        self.wait(1.5)
