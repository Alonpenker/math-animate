from manim import *


A_COLOR = RED_D
B_COLOR = BLUE_D
C_COLOR = GREEN_D
D_COLOR = YELLOW_E


def color_formula_parts(formula: MathTex) -> MathTex:
    formula.set_color_by_tex("a", A_COLOR)
    formula.set_color_by_tex("b", B_COLOR)
    formula.set_color_by_tex("c", C_COLOR)
    formula.set_color_by_tex("-7", B_COLOR)
    formula.set_color_by_tex("2", A_COLOR)
    formula.set_color_by_tex("3", C_COLOR)
    return formula


def color_substitution_parts(formula: MathTex) -> MathTex:
    return color_formula_parts(formula)


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("Set Up the Quadratic Formula", font_size=38, weight=BOLD).to_edge(UP, buff=0.35)

        equation = MathTex("2x^2", "-", "7x", "+", "3", "=", "0", font_size=68).move_to(UP * 1.25)
        a_box = SurroundingRectangle(equation[0], color=A_COLOR, buff=0.14)
        b_box = SurroundingRectangle(VGroup(equation[1], equation[2]), color=B_COLOR, buff=0.14)
        c_box = SurroundingRectangle(equation[4], color=C_COLOR, buff=0.14)

        a_label = MathTex("a", "=", "2", font_size=38, color=A_COLOR)
        b_label = MathTex("b", "=", "-7", font_size=38, color=B_COLOR)
        c_label = MathTex("c", "=", "3", font_size=38, color=C_COLOR)
        labels = VGroup(a_label, b_label, c_label).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        labels.next_to(equation, RIGHT, buff=1.0)
        labels.align_to(equation, UP)

        formula = MathTex(
            r"x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}",
            font_size=56,
            color=WHITE,
        ).next_to(equation, DOWN, buff=0.95)

        substituted = MathTex(
            r"x=\frac{-(-7)\pm\sqrt{(-7)^2-4\cdot2\cdot3}}{2\cdot2}",
            font_size=50,
        ).move_to(formula)
        color_substitution_parts(substituted)

        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.8)
        self.wait(1)

        self.play(Write(equation), run_time=1.0)
        self.wait(1)

        self.play(Create(a_box), FadeIn(labels[0], shift=RIGHT * 0.1), run_time=0.7)
        self.wait(1)
        self.play(ReplacementTransform(a_box, b_box), FadeIn(labels[1], shift=RIGHT * 0.1), run_time=0.7)
        self.wait(1)
        self.play(ReplacementTransform(b_box, c_box), FadeIn(labels[2], shift=RIGHT * 0.1), run_time=0.7)
        self.wait(1)

        self.play(FadeIn(formula, shift=UP * 0.15), run_time=0.9)
        self.wait(1)

        a_targets = formula.get_parts_by_tex("a")
        b_targets = formula.get_parts_by_tex("b")
        c_targets = formula.get_parts_by_tex("c")
        flying_values = VGroup(
            *[a_label[2].copy() for _ in a_targets],
            *[b_label[2].copy() for _ in b_targets],
            *[c_label[2].copy() for _ in c_targets],
        )
        for flyer in flying_values:
            self.add(flyer)

        fly_animations = []
        for flyer, target in zip(flying_values[:len(a_targets)], a_targets):
            flyer.move_to(a_label[2])
            fly_animations.append(flyer.animate.move_to(target.get_center()))
        for flyer, target in zip(
            flying_values[len(a_targets):len(a_targets) + len(b_targets)],
            b_targets,
        ):
            flyer.move_to(b_label[2])
            fly_animations.append(flyer.animate.move_to(target.get_center()))
        for flyer, target in zip(flying_values[-len(c_targets):], c_targets):
            flyer.move_to(c_label[2])
            fly_animations.append(flyer.animate.move_to(target.get_center()))

        self.play(
            *fly_animations,
            Indicate(VGroup(*a_targets), color=A_COLOR, scale_factor=1.08),
            Indicate(VGroup(*b_targets), color=B_COLOR, scale_factor=1.08),
            Indicate(VGroup(*c_targets), color=C_COLOR, scale_factor=1.08),
            run_time=1.1,
        )
        self.wait(1)

        value_note = Text(
            "Be careful with the negative b value",
            font_size=24,
            color=YELLOW_E,
        ).next_to(substituted, DOWN, buff=0.28)
        self.play(
            FadeOut(flying_values, scale=0.8),
            TransformMatchingTex(formula, substituted),
            FadeOut(c_box),
            run_time=1.1,
        )
        self.wait(1)
        self.play(FadeIn(value_note, shift=UP * 0.1), run_time=0.7)
        self.wait(1.5)


class Scene2(Scene):
    def construct(self) -> None:
        title = Text("Compute the Discriminant", font_size=38, weight=BOLD).to_edge(UP, buff=0.35)
        helper = Text("D = b^2 - 4ac", font_size=28, color=D_COLOR).next_to(title, DOWN, buff=0.25)

        discriminant_start = MathTex(
            "D",
            "=",
            "(",
            "-7",
            ")",
            "^2",
            "-",
            "4",
            r"\cdot",
            "2",
            r"\cdot",
            "3",
            font_size=60,
        ).move_to(UP * 0.9)
        discriminant_start[0].set_color(D_COLOR)
        discriminant_start[3].set_color(B_COLOR)
        for index in (7, 8, 9, 10, 11):
            discriminant_start[index].set_color(RED_E)

        left_step = MathTex("(", "-7", ")", "^2", "=", "49", font_size=42).move_to(LEFT * 3.1 + DOWN * 0.8)
        left_step[1].set_color(B_COLOR)
        left_step[5].set_color(B_COLOR)
        right_step = MathTex("4", r"\cdot", "2", r"\cdot", "3", "=", "24", font_size=42).move_to(
            RIGHT * 3.0 + DOWN * 0.8
        )
        right_step.set_color(RED_E)
        step_boxes = VGroup(
            SurroundingRectangle(left_step[5], color=B_COLOR, buff=0.12),
            SurroundingRectangle(right_step[6], color=RED_E, buff=0.12),
        )

        discriminant_mid = MathTex("D", "=", "49", "-", "24", font_size=62).move_to(DOWN * 0.5)
        discriminant_mid[0].set_color(D_COLOR)
        discriminant_mid[2].set_color(B_COLOR)
        discriminant_mid[4].set_color(RED_E)
        discriminant_final = MathTex("D", "=", "25", font_size=66, color=D_COLOR).move_to(DOWN * 0.5)

        sqrt_step = MathTex(r"\sqrt{25}=5", font_size=58, color=GREEN_E).move_to(DOWN * 2.0)
        sqrt_note = Text(
            "Perfect square -> two real rational solutions",
            font_size=24,
            color=GREEN_E,
        ).next_to(sqrt_step, DOWN, buff=0.28)

        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(helper, shift=DOWN * 0.15), run_time=0.8)
        self.wait(1)

        self.play(Write(discriminant_start), run_time=1.0)
        self.wait(1)

        self.play(FadeIn(left_step, shift=UP * 0.1), FadeIn(right_step, shift=UP * 0.1), run_time=0.8)
        self.wait(1)

        self.play(Create(step_boxes[0]), Create(step_boxes[1]), run_time=0.7)
        self.wait(1)

        self.play(
            FadeOut(discriminant_start, shift=UP * 0.1),
            Write(VGroup(discriminant_mid[0], discriminant_mid[1], discriminant_mid[3])),
            TransformFromCopy(left_step[5], discriminant_mid[2]),
            TransformFromCopy(right_step[6], discriminant_mid[4]),
            run_time=1.0,
        )
        self.wait(1)

        self.play(
            FadeOut(step_boxes[0]),
            FadeOut(step_boxes[1]),
            FadeOut(left_step, shift=DOWN * 0.1),
            FadeOut(right_step, shift=DOWN * 0.1),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            TransformMatchingTex(discriminant_mid, discriminant_final),
            run_time=0.9,
        )
        self.wait(1)

        self.play(FadeIn(sqrt_step, shift=UP * 0.1), run_time=0.7)
        self.wait(1)
        self.play(FadeIn(sqrt_note, shift=UP * 0.1), run_time=0.7)
        self.wait(1.5)


class Scene3(Scene):
    def construct(self) -> None:
        title = Text("Use the Plus-Minus for Both Solutions", font_size=36, weight=BOLD).to_edge(UP, buff=0.35)
        helper = Text("One formula, two cases", font_size=26, color=YELLOW_E).next_to(title, DOWN, buff=0.25)

        compact_formula = MathTex(
            "x",
            "=",
            r"\frac{7\pm 5}{4}",
            font_size=66,
        ).move_to(UP * 1.1)

        plus_track = VGroup(
            Text("Plus case", font_size=24, color=BLUE_D),
            MathTex("x_1", "=", r"\frac{7+5}{4}", font_size=50),
            MathTex("x_1", "=", r"\frac{12}{4}", font_size=50),
            MathTex("x_1", "=", "3", font_size=54, color=GREEN_E),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        plus_track.move_to(LEFT * 3.2 + DOWN * 1.25)

        minus_track = VGroup(
            Text("Minus case", font_size=24, color=ORANGE),
            MathTex("x_2", "=", r"\frac{7-5}{4}", font_size=50),
            MathTex("x_2", "=", r"\frac{2}{4}", font_size=50),
            MathTex("x_2", "=", r"\frac{1}{2}", font_size=54, color=GREEN_E),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        minus_track.move_to(RIGHT * 3.0 + DOWN * 1.25)

        plus_arrow = Arrow(
            plus_track.get_top() + UP * 0.75,
            plus_track.get_top() + UP * 0.08,
            buff=0.05,
            color=BLUE_D,
        )
        minus_arrow = Arrow(
            minus_track.get_top() + UP * 0.75,
            minus_track.get_top() + UP * 0.08,
            buff=0.05,
            color=ORANGE,
        )

        solution_set = MathTex("x", r"\in", r"\left\{3,\frac{1}{2}\right\}", font_size=64, color=GREEN_E).move_to(
            DOWN * 2.0
        )
        solution_label = Text("Solution set", font_size=26, color=GREEN_E).next_to(solution_set, UP, buff=0.22)

        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(helper, shift=DOWN * 0.15), run_time=0.8)
        self.wait(1)

        self.play(Write(compact_formula), run_time=1.0)
        self.wait(1)

        self.play(Create(plus_arrow), Create(minus_arrow), run_time=0.8)
        self.wait(1)

        self.play(FadeIn(plus_track[0], shift=UP * 0.1), FadeIn(minus_track[0], shift=UP * 0.1), run_time=0.6)
        self.wait(1)

        self.play(Write(plus_track[1]), Write(minus_track[1]), run_time=0.9)
        self.wait(1)

        self.play(
            TransformMatchingTex(plus_track[1].copy(), plus_track[2]),
            TransformMatchingTex(minus_track[1].copy(), minus_track[2]),
            run_time=0.9,
        )
        self.wait(1)

        self.play(
            TransformMatchingTex(plus_track[2].copy(), plus_track[3]),
            TransformMatchingTex(minus_track[2].copy(), minus_track[3]),
            run_time=0.9,
        )
        self.wait(1)

        self.play(
            FadeOut(VGroup(plus_arrow, minus_arrow), shift=UP * 0.1),
            FadeOut(VGroup(plus_track[0], plus_track[1], plus_track[2]), shift=DOWN * 0.1),
            FadeOut(VGroup(minus_track[0], minus_track[1], minus_track[2]), shift=DOWN * 0.1),
            FadeIn(solution_label, shift=UP * 0.1),
            TransformMatchingTex(VGroup(plus_track[3], minus_track[3]), solution_set),
            run_time=1.0,
        )
        self.wait(1.5)
