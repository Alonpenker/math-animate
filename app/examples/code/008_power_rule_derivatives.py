from manim import *


RULE_COLOR = BLUE_D
TERM_COLOR = YELLOW_E
GOOD_COLOR = GREEN_E
BAD_COLOR = RED_D
ACCENT_COLOR = ORANGE


def make_rule_banner() -> VGroup:
    banner = RoundedRectangle(
        width=5.9,
        height=1.0,
        corner_radius=0.18,
        stroke_color=RULE_COLOR,
        fill_color=BLUE_E,
        fill_opacity=0.15,
    )
    text = MathTex(r"\frac{d}{dx}\left(x^n\right)=n x^{n-1}", font_size=36, color=RULE_COLOR)
    text.move_to(banner.get_center())
    return VGroup(banner, text)


def build_power_term(coefficient: str, exponent: str, color: str = WHITE) -> VGroup:
    coefficient_mob = MathTex(coefficient, font_size=54, color=color)
    x_mob = MathTex("x", font_size=54, color=color)
    exponent_mob = MathTex(exponent, font_size=30, color=color)

    coefficient_mob.move_to(ORIGIN)
    x_mob.next_to(coefficient_mob, RIGHT, buff=0.06, aligned_edge=DOWN)
    exponent_mob.next_to(x_mob, UR, buff=0.02)
    return VGroup(coefficient_mob, x_mob, exponent_mob)


def color_power_term(term: VGroup) -> VGroup:
    term[0].set_color(TERM_COLOR)
    term[2].set_color(ACCENT_COLOR)
    return term


def build_derivative_workspace() -> tuple[VGroup, np.ndarray, np.ndarray]:
    derivative_symbol = MathTex(r"\frac{d}{dx}", font_size=54)
    left_paren = MathTex("(", font_size=64)
    right_paren = MathTex(")", font_size=64)
    equals = MathTex("=", font_size=54)

    derivative_symbol.move_to(LEFT * 3.45 + DOWN * 0.05)
    left_paren.next_to(derivative_symbol, RIGHT, buff=0.12)
    right_paren.move_to(RIGHT * 0.05 + DOWN * 0.05)
    equals.next_to(right_paren, RIGHT, buff=0.18)

    workspace = VGroup(derivative_symbol, left_paren, right_paren, equals)
    slot_center = (left_paren.get_center() + right_paren.get_center()) / 2
    return workspace, slot_center, equals.get_center()


def make_x_mark(target: Mobject, color: str = BAD_COLOR) -> VGroup:
    box = SurroundingRectangle(target, buff=0.12)
    slash_1 = Line(box.get_corner(UL), box.get_corner(DR), color=color, stroke_width=6)
    slash_2 = Line(box.get_corner(UR), box.get_corner(DL), color=color, stroke_width=6)
    return VGroup(slash_1, slash_2)


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("Differentiate with the Power Rule", font_size=36, weight=BOLD).to_edge(UP, buff=0.28)
        rule_banner = make_rule_banner().next_to(title, DOWN, buff=0.2)

        function = MathTex(
            "f(x)",
            "=",
            "3x^{4}",
            "-",
            "2x^{2}",
            "+",
            "5",
            font_size=58,
        ).move_to(UP * 1.45)

        answer_start = MathTex("f'(x)", "=", r"\text{?}", font_size=56).move_to(DOWN * 2.15)
        answer_first = MathTex("f'(x)", "=", "12x^{3}", font_size=56).move_to(answer_start)
        answer_second = MathTex("f'(x)", "=", "12x^{3}", "-", "4x", font_size=56).move_to(answer_start)
        answer_with_zero = MathTex("f'(x)", "=", "12x^{3}", "-", "4x", "+", "0", font_size=56).move_to(answer_start)
        answer_final = MathTex("f'(x)", "=", "12x^{3}", "-", "4x", font_size=56).move_to(answer_start)
        current_answer = answer_start

        term1_box = SurroundingRectangle(function[2], color=TERM_COLOR, buff=0.14)
        term2_box = SurroundingRectangle(VGroup(function[3], function[4]), color=TERM_COLOR, buff=0.14)
        term3_box = SurroundingRectangle(function[6], color=TERM_COLOR, buff=0.14)
        workspace, slot_center, equals_center = build_derivative_workspace()
        rhs_multiplier_center = equals_center + RIGHT * 1.0
        rhs_dot_center = equals_center + RIGHT * 1.55
        rhs_coefficient_center = equals_center + RIGHT * 2.15
        rhs_final_center = equals_center + RIGHT * 2.15

        self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(rule_banner, shift=DOWN * 0.12), run_time=0.8)
        self.wait(1)

        self.play(Write(function), run_time=1.0)
        self.wait(1)

        self.play(FadeIn(answer_start, shift=UP * 0.1), run_time=0.8)
        self.wait(1)

        self.play(FadeIn(workspace, shift=UP * 0.08), run_time=0.8)
        self.wait(0.8)

        term_1 = color_power_term(build_power_term("3", "4").move_to(slot_center))
        term_1_rhs_coeff = term_1[0].copy()
        term_1_rhs_x = term_1[1].copy()
        term_1_rhs_multiplier = term_1[2].copy()
        term_1_rhs_exponent = term_1[2].copy()
        term_1_coeff_target = term_1[0].copy().move_to(rhs_coefficient_center)
        term_1_x_target = term_1[1].copy()
        term_1_x_target.next_to(term_1_coeff_target, RIGHT, buff=0.06, aligned_edge=DOWN)
        term_1_multiplier_target = term_1[2].copy().move_to(rhs_multiplier_center)
        term_1_dot = MathTex(r"\cdot", font_size=52).move_to(rhs_dot_center)
        term_1_exponent_target = MathTex("3", font_size=30, color=GOOD_COLOR)
        term_1_exponent_target.next_to(term_1_x_target, UR, buff=0.02)
        term_1_result = MathTex("12", "x^{3}", font_size=54).move_to(rhs_final_center)
        term_1_result[0].set_color(GOOD_COLOR)
        term_1_result[1].set_color(WHITE)

        self.play(Create(term1_box), run_time=0.7)
        self.play(TransformFromCopy(function[2], term_1), run_time=0.8)
        self.wait(0.8)

        self.add(term_1_rhs_coeff, term_1_rhs_x, term_1_rhs_multiplier, term_1_rhs_exponent)
        self.play(
            term_1_rhs_coeff.animate.move_to(term_1_coeff_target.get_center()),
            term_1_rhs_x.animate.move_to(term_1_x_target.get_center()),
            term_1_rhs_multiplier.animate.move_to(term_1_multiplier_target.get_center()),
            Transform(term_1_rhs_exponent, term_1_exponent_target),
            FadeIn(term_1_dot, shift=RIGHT * 0.05),
            run_time=1.0,
        )
        self.wait(1)

        self.play(
            FadeTransform(
                VGroup(term_1_rhs_multiplier, term_1_dot, term_1_rhs_coeff, term_1_rhs_x, term_1_rhs_exponent),
                term_1_result,
            ),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            TransformMatchingTex(current_answer, answer_first),
            TransformFromCopy(term_1_result, answer_first[2]),
            run_time=0.9,
        )
        self.wait(1)

        self.play(
            FadeOut(term_1),
            FadeOut(term_1_result),
            ReplacementTransform(term1_box, term2_box),
            run_time=0.9,
        )
        self.wait(0.8)

        term_2 = color_power_term(build_power_term("-2", "2").move_to(slot_center))
        term_2_rhs_coeff = term_2[0].copy()
        term_2_rhs_x = term_2[1].copy()
        term_2_rhs_multiplier = term_2[2].copy()
        term_2_rhs_exponent = term_2[2].copy()
        term_2_coeff_target = term_2[0].copy().move_to(rhs_coefficient_center)
        term_2_x_target = term_2[1].copy()
        term_2_x_target.next_to(term_2_coeff_target, RIGHT, buff=0.06, aligned_edge=DOWN)
        term_2_multiplier_target = term_2[2].copy().move_to(rhs_multiplier_center)
        term_2_dot = MathTex(r"\cdot", font_size=52).move_to(rhs_dot_center)
        term_2_exponent_target = MathTex("1", font_size=30, color=GOOD_COLOR)
        term_2_exponent_target.next_to(term_2_x_target, UR, buff=0.02)
        term_2_result = MathTex("-4", "x", font_size=54).move_to(rhs_final_center)
        term_2_result[0].set_color(GOOD_COLOR)
        term_2_result[1].set_color(WHITE)

        self.play(TransformFromCopy(VGroup(function[3], function[4]), term_2), run_time=0.8)
        self.wait(0.8)

        self.add(term_2_rhs_coeff, term_2_rhs_x, term_2_rhs_multiplier, term_2_rhs_exponent)
        self.play(
            term_2_rhs_coeff.animate.move_to(term_2_coeff_target.get_center()),
            term_2_rhs_x.animate.move_to(term_2_x_target.get_center()),
            term_2_rhs_multiplier.animate.move_to(term_2_multiplier_target.get_center()),
            Transform(term_2_rhs_exponent, term_2_exponent_target),
            FadeIn(term_2_dot, shift=RIGHT * 0.05),
            run_time=1.0,
        )
        self.wait(1)

        self.play(
            FadeTransform(
                VGroup(term_2_rhs_multiplier, term_2_dot, term_2_rhs_coeff, term_2_rhs_x, term_2_rhs_exponent),
                term_2_result,
            ),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            TransformMatchingTex(current_answer, answer_second),
            TransformFromCopy(term_2_result, answer_second[4]),
            run_time=0.9,
        )
        self.wait(1)

        self.play(
            FadeOut(term_2),
            FadeOut(term_2_result),
            ReplacementTransform(term2_box, term3_box),
            run_time=0.9,
        )
        self.wait(0.8)

        term_3 = MathTex("5", font_size=54, color=TERM_COLOR).move_to(slot_center)
        term_3_rhs = term_3.copy()
        term_3_target = MathTex("5", font_size=54, color=TERM_COLOR).move_to(rhs_final_center)
        term_3_zero = MathTex("0", font_size=54, color=GOOD_COLOR).move_to(rhs_final_center)
        constant_note = Text("constant term -> 0", font_size=24, color=ACCENT_COLOR).move_to(RIGHT * 2.5 + DOWN * 1.05)

        self.play(TransformFromCopy(function[6], term_3), run_time=0.8)
        self.wait(1)

        self.play(TransformFromCopy(term_3, term_3_rhs), run_time=0.8)
        self.play(
            term_3_rhs.animate.move_to(term_3_target.get_center()),
            FadeIn(constant_note, shift=UP * 0.05),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(Transform(term_3_rhs, term_3_zero), run_time=0.8)
        self.wait(0.8)

        self.play(
            TransformMatchingTex(current_answer, answer_with_zero),
            TransformFromCopy(term_3_rhs, answer_with_zero[6]),
            run_time=0.9,
        )
        self.wait(0.8)

        self.play(
            FadeOut(term_3),
            FadeOut(term_3_rhs),
            FadeOut(constant_note),
            FadeOut(term3_box),
            FadeOut(workspace),
            TransformMatchingTex(current_answer, answer_final),
            run_time=0.9,
        )
        self.wait(1.5)


class Scene2(Scene):
    def construct(self) -> None:
        title = Text("Common Derivative Errors", font_size=36, weight=BOLD).to_edge(UP, buff=0.28)
        rule_banner = make_rule_banner().next_to(title, DOWN, buff=0.18)

        first_example = MathTex("3x^{4}", r"\rightarrow", "2x^{3}", font_size=60)
        first_example.move_to(UP * 0.8)
        first_example[2].set_color(BAD_COLOR)
        first_cross = make_x_mark(first_example[2])

        first_note = Text("Wrong: do not subtract 1 from the coefficient.", font_size=24, color=BAD_COLOR)
        first_note.next_to(first_example, DOWN, buff=0.22)

        first_correct = MathTex("3x^{4}", r"\rightarrow", "12x^{3}", font_size=60)
        first_correct.move_to(first_example)
        first_correct[2].set_color(GOOD_COLOR)

        first_check = Text("Multiply 3 by 4, then lower the exponent to 3.", font_size=24, color=GOOD_COLOR)
        first_check.next_to(first_example, DOWN, buff=0.22)

        second_prompt = MathTex("g(x)", "=", "-5x^{3}", "+", "4x", font_size=58).move_to(DOWN * 0.45)

        wrong_second = MathTex("g'(x)", "=", "15x^{2}", "+", "4", font_size=52, color=BAD_COLOR)
        wrong_second.next_to(second_prompt, DOWN, buff=0.55)
        wrong_cross = make_x_mark(wrong_second[2])

        sign_note = Text("Wrong: the negative sign stays with the term.", font_size=24, color=BAD_COLOR)
        sign_note.next_to(wrong_second, DOWN, buff=0.18)

        correct_second = MathTex("g'(x)", "=", "-15x^{2}", "+", "4", font_size=52)
        correct_second.next_to(second_prompt, DOWN, buff=0.55)
        correct_second[2].set_color(GOOD_COLOR)
        correct_note = Text("Correct: -5 times 3 is -15, and 4x becomes 4.", font_size=24, color=GOOD_COLOR)
        correct_note.next_to(correct_second, DOWN, buff=0.18)

        self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(rule_banner, shift=DOWN * 0.12), run_time=0.8)
        self.wait(1)

        self.play(Write(first_example), run_time=0.8)
        self.play(Create(first_cross), FadeIn(first_note, shift=UP * 0.05), run_time=0.8)
        self.wait(1)

        self.play(
            FadeOut(first_cross),
            FadeOut(first_note),
            TransformMatchingTex(first_example, first_correct),
            FadeIn(first_check, shift=UP * 0.05),
            run_time=0.9,
        )
        self.wait(1)

        self.play(
            FadeOut(first_correct, shift=UP * 0.08),
            FadeOut(first_check, shift=UP * 0.08),
            run_time=0.7,
        )
        self.wait(0.5)

        second_prompt.move_to(UP * 0.75)
        wrong_second.next_to(second_prompt, DOWN, buff=0.55)
        sign_note.next_to(wrong_second, DOWN, buff=0.18)
        correct_second.next_to(second_prompt, DOWN, buff=0.55)
        correct_note.next_to(correct_second, DOWN, buff=0.18)

        self.play(Write(second_prompt), run_time=0.9)
        self.wait(0.8)

        self.play(FadeIn(wrong_second, shift=UP * 0.05), run_time=0.7)
        self.play(Create(wrong_cross), FadeIn(sign_note, shift=UP * 0.05), run_time=0.8)
        self.wait(1)

        negative_source = second_prompt[2][0].copy()
        self.add(negative_source)
        self.play(
            negative_source.animate.move_to(correct_second[2][0]),
            run_time=0.6,
        )
        self.play(
            FadeOut(wrong_cross),
            FadeOut(sign_note),
            TransformMatchingTex(wrong_second, correct_second),
            FadeIn(correct_note, shift=UP * 0.05),
            FadeOut(negative_source),
            run_time=0.9,
        )
        self.wait(1.5)
