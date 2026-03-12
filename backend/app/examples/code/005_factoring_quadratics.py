from manim import *


def make_condition_panel(
    product_value: str,
    sum_value: str,
    anchor: np.ndarray,
) -> tuple[VGroup, Text, MathTex, Text, MathTex]:
    panel = RoundedRectangle(
        corner_radius=0.16,
        width=4.6,
        height=2.5,
        color=BLUE_E,
        stroke_width=2,
    )
    panel.set_fill(BLUE_E, opacity=0.06)
    panel.move_to(anchor)

    title = Text("Need two numbers", font_size=28, weight=BOLD).move_to(
        panel.get_top() + DOWN * 0.38
    )
    product_label = Text("Product", font_size=24, color=TEAL_D)
    product_equal = MathTex("=", font_size=30, color=TEAL_D)
    product_value_tex = MathTex(product_value, font_size=34, color=TEAL_D)
    product_row = VGroup(product_label, product_equal, product_value_tex).arrange(RIGHT, buff=0.16)

    sum_label = Text("Sum", font_size=24, color=ORANGE)
    sum_equal = MathTex("=", font_size=30, color=ORANGE)
    sum_value_tex = MathTex(sum_value, font_size=34, color=ORANGE)
    sum_row = VGroup(sum_label, sum_equal, sum_value_tex).arrange(RIGHT, buff=0.16)

    rows = VGroup(product_row, sum_row).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
    rows.move_to(panel.get_center() + DOWN * 0.18)

    group = VGroup(panel, title, rows)
    return group, product_label, product_value_tex, sum_label, sum_value_tex


def make_pair_row(
    left_value: str,
    right_value: str,
    product_text: str,
    sum_text: str,
    color: ManimColor = WHITE,
) -> VGroup:
    pair_tex = MathTex(
        "(",
        left_value,
        ",",
        right_value,
        ")",
        font_size=34,
        color=color,
    )
    product_tex = MathTex(product_text, font_size=34, color=TEAL_D)
    sum_tex = MathTex(sum_text, font_size=34, color=ORANGE)
    row = VGroup(pair_tex, product_tex, sum_tex).arrange(RIGHT, buff=0.35)
    return row


def make_factor_table(rows: list[VGroup], anchor: np.ndarray) -> tuple[VGroup, Text]:
    panel = RoundedRectangle(
        corner_radius=0.16,
        width=5.2,
        height=3.6,
        color=GRAY_B,
        stroke_width=2,
    )
    panel.set_fill(GRAY_E, opacity=0.08)
    panel.move_to(anchor)

    title = Text("Factor Pairs", font_size=28, weight=BOLD).move_to(
        panel.get_top() + DOWN * 0.35
    )
    body = VGroup(*rows).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
    body.move_to(panel.get_center() + DOWN * 0.15)
    group = VGroup(panel, title, body)
    return group, title


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("Factor x^2 + bx + c", font_size=40, weight=BOLD).to_edge(UP, buff=0.35)
        expression = MathTex("x^2", "+", "5", "x", "+", "6", font_size=68).move_to(UP * 1.15)

        panel_group, _, product_value_tex, _, sum_value_tex = make_condition_panel("?", "?", LEFT * 3.3 + DOWN * 1.8)

        row1 = make_pair_row("1", "6", "1\\cdot 6=6", "1+6=7")
        row2 = make_pair_row("2", "3", "2\\cdot 3=6", "2+3=5")
        table_group, _ = make_factor_table([row1, row2], RIGHT * 3.2 + DOWN * 1.7)

        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.8)
        self.wait(1)

        self.play(Write(expression), run_time=1.0)
        self.wait(1)

        self.play(FadeIn(panel_group, shift=UP * 0.2), run_time=0.8)
        self.wait(1)

        product_target = MathTex("6", font_size=34, color=TEAL_D).move_to(product_value_tex)
        sum_target = MathTex("5", font_size=34, color=ORANGE).move_to(sum_value_tex)

        self.play(Indicate(expression[5], color=TEAL_D, scale_factor=1.08), run_time=0.7)
        moving_six = expression[5].copy()
        self.add(moving_six)
        self.play(moving_six.animate.move_to(product_value_tex.get_center()), run_time=0.8)
        self.play(
            FadeOut(moving_six, scale=0.85),
            Transform(product_value_tex, product_target),
            run_time=0.6,
        )
        self.wait(1)

        self.play(Indicate(expression[2], color=ORANGE, scale_factor=1.08), run_time=0.7)
        moving_five = expression[2].copy()
        self.add(moving_five)
        self.play(moving_five.animate.move_to(sum_value_tex.get_center()), run_time=0.8)
        self.play(
            FadeOut(moving_five, scale=0.85),
            Transform(sum_value_tex, sum_target),
            run_time=0.6,
        )
        self.wait(1)

        self.play(FadeIn(table_group, shift=UP * 0.2), run_time=0.8)
        self.wait(1)

        row1_box = SurroundingRectangle(row1, color=GRAY_B, buff=0.12)
        row2_box = SurroundingRectangle(row2, color=GREEN_E, buff=0.12)

        self.play(Create(row1_box), run_time=0.6)
        self.wait(1)
        wrong_note = Text("Sum is 7, not 5", font_size=20, color=RED_E)
        wrong_note.next_to(row2, DOWN, buff=0.18)
        wrong_note.align_to(row2, LEFT)
        self.play(FadeIn(wrong_note, shift=UP * 0.1), run_time=0.6)
        self.wait(1)

        self.play(
            ReplacementTransform(row1_box, row2_box),
            FadeOut(wrong_note, shift=DOWN * 0.1),
            row2[0].animate.set_color(GREEN_E),
            run_time=0.8,
        )
        self.wait(1)

        factored = MathTex("(", "x", "+", "2", ")", "(", "x", "+", "3", ")", font_size=64)
        factored.move_to(DOWN * 0.45)
        pair_copy = row2[0].copy()
        self.add(pair_copy)
        self.play(
            FadeOut(panel_group, shift=DOWN * 0.15),
            FadeOut(table_group, shift=DOWN * 0.15),
            FadeOut(row2_box),
            TransformMatchingTex(pair_copy, factored),
            run_time=1.1,
        )
        self.wait(1.5)
