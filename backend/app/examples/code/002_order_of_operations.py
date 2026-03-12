from manim import *


def step_row(label: str, top_anchor: Mobject) -> tuple[VGroup, Text]:
    check_box = Square(side_length=0.28, color=GRAY_B, stroke_width=2)
    check_mark = Text("✓", font_size=24, color=GREEN_E).move_to(check_box.get_center())
    check_mark.set_opacity(0)
    step_text = Text(label, font_size=24)
    row = VGroup(check_box, check_mark, step_text).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
    row.next_to(top_anchor, DOWN, aligned_edge=LEFT, buff=0.3)
    return row, check_mark


def build_panel() -> tuple[VGroup, list[Text], list[Text]]:
    panel = RoundedRectangle(corner_radius=0.18, width=4.8, height=5.5, color=BLUE_E, stroke_width=2)
    panel.set_fill(BLUE_E, opacity=0.06)
    panel.to_edge(RIGHT, buff=0.45).shift(DOWN * 0.2)

    panel_title = Text("PEMDAS Steps", font_size=28, weight=BOLD).move_to(
        panel.get_top() + DOWN * 0.4
    )
    row1, check1 = step_row("1. Parentheses", panel_title)
    row2, check2 = step_row("2. Exponents", row1)
    row3, check3 = step_row("3. Multiply", row2)
    row4, check4 = step_row("4. Add/Subtract", row3)

    group = VGroup(panel, panel_title, row1, row2, row3, row4)
    return group, [row1[2], row2[2], row3[2], row4[2]], [check1, check2, check3, check4]


def highlight_box(target: Mobject, color: ManimColor = YELLOW) -> SurroundingRectangle:
    box = SurroundingRectangle(target, color=color, buff=0.12, corner_radius=0.12)
    box.set_stroke(width=4)
    return box


def animate_substitution(
    scene: Scene,
    expression: MathTex,
    value_label: MathTex,
    x_piece: Mobject,
    substituted_expression: MathTex,
) -> MathTex:
    moving_value = value_label[2].copy()
    moving_value.move_to(value_label[2].get_center())
    scene.add(moving_value)
    scene.play(moving_value.animate.move_to(x_piece.get_center()), run_time=0.8)
    scene.play(
        TransformMatchingTex(expression, substituted_expression),
        FadeOut(moving_value, scale=0.8),
        run_time=0.8,
    )
    return substituted_expression


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("Order of Operations", font_size=42, weight=BOLD).to_edge(UP, buff=0.35)
        panel_group, step_labels, check_marks = build_panel()

        self.play(
            FadeIn(title, shift=DOWN * 0.2),
            FadeIn(panel_group, shift=LEFT * 0.2),
            run_time=0.8,
        )
        self.wait(1)

        expression_one = MathTex("4", "+", "2", "(", "5", "-", "x", ")", font_size=58)
        expression_one.move_to(LEFT * 2.35 + UP * 0.7)
        example_one_value = MathTex("x", "=", "3", font_size=42, color=TEAL_D).next_to(
            expression_one, UP, aligned_edge=LEFT, buff=0.55
        )

        self.play(Write(expression_one), run_time=1.0)
        self.wait(1)
        self.play(FadeIn(example_one_value, shift=DOWN * 0.15), run_time=0.6)
        self.wait(1)

        substituted_one = MathTex("4", "+", "2", "(", "5", "-", "3", ")", font_size=58).move_to(expression_one)
        expression_one = animate_substitution(self, expression_one, example_one_value, expression_one[6], substituted_one)
        self.wait(1)

        paren_box = highlight_box(
            VGroup(expression_one[3], expression_one[4], expression_one[5], expression_one[6], expression_one[7])
        )
        self.play(Create(paren_box), step_labels[0].animate.set_color(YELLOW), run_time=0.8)
        self.wait(1)

        simplified_parentheses = MathTex("4", "+", "2", "(", "2", ")", font_size=58).move_to(expression_one)
        self.play(TransformMatchingTex(expression_one, simplified_parentheses), run_time=0.9)
        expression_one = simplified_parentheses
        self.play(FadeIn(check_marks[0], scale=0.6), step_labels[0].animate.set_color(GREEN_E), run_time=0.6)
        self.wait(1)

        multiply_box = highlight_box(
            VGroup(expression_one[2], expression_one[3], expression_one[4], expression_one[5]),
            color=TEAL_D,
        )
        self.play(
            ReplacementTransform(paren_box, multiply_box),
            step_labels[2].animate.set_color(TEAL_D),
            run_time=0.8,
        )
        multiplied = MathTex("4", "+", "4", font_size=58).move_to(expression_one)
        self.play(TransformMatchingTex(expression_one, multiplied), run_time=0.9)
        expression_one = multiplied
        self.play(FadeIn(check_marks[2], scale=0.6), step_labels[2].animate.set_color(GREEN_E), run_time=0.6)
        self.wait(1)

        add_box = highlight_box(expression_one, color=ORANGE)
        self.play(
            ReplacementTransform(multiply_box, add_box),
            step_labels[3].animate.set_color(ORANGE),
            run_time=0.8,
        )
        result_one = MathTex("8", font_size=62, color=GREEN_E).move_to(expression_one)
        self.play(TransformMatchingTex(expression_one, result_one), run_time=0.9)
        expression_one = result_one
        self.play(FadeIn(check_marks[3], scale=0.6), step_labels[3].animate.set_color(GREEN_E), run_time=0.6)
        self.wait(1)

        self.play(
            FadeOut(expression_one, shift=LEFT * 0.2),
            FadeOut(example_one_value, shift=LEFT * 0.2),
            FadeOut(add_box, shift=LEFT * 0.2),
            FadeOut(check_marks[0], scale=0.6),
            FadeOut(check_marks[2], scale=0.6),
            FadeOut(check_marks[3], scale=0.6),
            step_labels[0].animate.set_color(WHITE),
            step_labels[2].animate.set_color(WHITE),
            step_labels[3].animate.set_color(WHITE),
            run_time=0.8,
        )
        self.wait(1)

        expression_two = MathTex("3", "(", "2", "+", "x", ")", "^2", font_size=58)
        expression_two.move_to(LEFT * 2.25 + UP * 0.7)
        example_two_value = MathTex("x", "=", "1", font_size=42, color=TEAL_D).next_to(
            expression_two, UP, aligned_edge=LEFT, buff=0.55
        )

        self.play(Write(expression_two), run_time=1.0)
        self.wait(1)
        self.play(FadeIn(example_two_value, shift=DOWN * 0.15), run_time=0.6)
        self.wait(1)

        substituted_two = MathTex("3", "(", "2", "+", "1", ")", "^2", font_size=58).move_to(expression_two)
        expression_two = animate_substitution(self, expression_two, example_two_value, expression_two[4], substituted_two)
        self.wait(1)

        paren_box_two = highlight_box(
            VGroup(expression_two[1], expression_two[2], expression_two[3], expression_two[4], expression_two[5])
        )
        self.play(Create(paren_box_two), step_labels[0].animate.set_color(YELLOW), run_time=0.8)
        self.wait(1)

        parentheses_done = MathTex("3", "(", "3", ")", "^2", font_size=58).move_to(expression_two)
        self.play(TransformMatchingTex(expression_two, parentheses_done), run_time=0.9)
        expression_two = parentheses_done
        self.play(FadeIn(check_marks[0], scale=0.6), step_labels[0].animate.set_color(GREEN_E), run_time=0.6)
        self.wait(1)

        exponent_box = highlight_box(
            VGroup(expression_two[1], expression_two[2], expression_two[3], expression_two[4]),
            color=PURPLE_B,
        )
        self.play(
            ReplacementTransform(paren_box_two, exponent_box),
            step_labels[1].animate.set_color(PURPLE_B),
            run_time=0.8,
        )
        exponent_done = MathTex("3", "(", "9", ")", font_size=58).move_to(expression_two)
        self.play(TransformMatchingTex(expression_two, exponent_done), run_time=0.9)
        expression_two = exponent_done
        self.play(FadeIn(check_marks[1], scale=0.6), step_labels[1].animate.set_color(GREEN_E), run_time=0.6)
        self.wait(1)

        multiply_box_two = highlight_box(expression_two, color=TEAL_D)
        self.play(
            ReplacementTransform(exponent_box, multiply_box_two),
            step_labels[2].animate.set_color(TEAL_D),
            run_time=0.8,
        )
        result_two = MathTex("27", font_size=62, color=GREEN_E).move_to(expression_two)
        self.play(TransformMatchingTex(expression_two, result_two), run_time=0.9)
        self.play(FadeIn(check_marks[2], scale=0.6), step_labels[2].animate.set_color(GREEN_E), run_time=0.6)
        self.wait(1.5)
