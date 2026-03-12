from manim import *


def build_system() -> tuple[MathTex, MathTex]:
    first_equation = MathTex("y", "=", "2x", "+", "1", font_size=60)
    second_equation = MathTex("x", "+", "y", "=", "7", font_size=60)
    system_group = VGroup(first_equation, second_equation).arrange(
        DOWN, aligned_edge=LEFT, buff=0.9
    )
    system_group.move_to(UP * 0.35)
    return first_equation, second_equation


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("Solve by Substitution", font_size=40, weight=BOLD).to_edge(UP, buff=0.35)
        helper_text = Text(
            "Replace y with 2x + 1 in the other equation",
            font_size=26,
            color=YELLOW_E,
        ).next_to(title, DOWN, buff=0.28)

        first_equation, second_equation = build_system()

        self.play(
            FadeIn(title, shift=DOWN * 0.2),
            FadeIn(helper_text, shift=DOWN * 0.15),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            Write(first_equation),
            Write(second_equation),
            run_time=1.1,
        )
        self.wait(1)

        first_highlight = SurroundingRectangle(first_equation, color=BLUE_D, buff=0.18)
        y_slot_highlight = SurroundingRectangle(second_equation[2], color=BLUE_D, buff=0.14)
        self.play(
            Create(first_highlight),
            first_equation.animate.set_color(BLUE_D),
            run_time=0.8,
        )
        self.wait(1)

        expression_copy = VGroup(
            first_equation[2].copy(),
            first_equation[3].copy(),
            first_equation[4].copy(),
        )
        self.add(expression_copy)
        self.play(Create(y_slot_highlight), run_time=0.6)
        self.play(
            expression_copy.animate.set_color(YELLOW_E).move_to(second_equation[2].get_center() + UP * 0.55),
            run_time=1.0,
        )
        self.wait(1)

        substituted_equation = MathTex(
            "x",
            "+",
            "(",
            "2x",
            "+",
            "1",
            ")",
            "=",
            "7",
            font_size=60,
        ).move_to(second_equation)
        self.play(
            TransformMatchingTex(second_equation, substituted_equation),
            FadeOut(expression_copy, scale=0.85),
            FadeOut(y_slot_highlight),
            run_time=1.0,
        )
        second_equation = substituted_equation
        self.wait(1)

        combine_text = Text("Combine like terms", font_size=26, color=TEAL_D).move_to(helper_text)
        x_terms_highlight = SurroundingRectangle(
            VGroup(second_equation[0], second_equation[3]),
            color=TEAL_D,
            buff=0.18,
        )
        self.play(
            FadeOut(first_highlight),
            first_equation.animate.set_color(WHITE),
            Transform(helper_text, combine_text),
            Create(x_terms_highlight),
            run_time=0.8,
        )
        self.wait(1)

        combined_equation = MathTex("3x", "+", "1", "=", "7", font_size=60).move_to(second_equation)
        self.play(
            TransformMatchingTex(second_equation, combined_equation),
            FadeOut(x_terms_highlight),
            run_time=1.0,
        )
        self.wait(1.5)


class Scene2(Scene):
    def construct(self) -> None:
        title = Text("Finish and Check", font_size=40, weight=BOLD).to_edge(UP, buff=0.35)
        helper_text = Text(
            "Solve for x, then substitute back for y",
            font_size=26,
            color=YELLOW_E,
        ).next_to(title, DOWN, buff=0.28)

        equation = MathTex("3x", "+", "1", "=", "7", font_size=60).move_to(UP * 1.0)

        self.play(
            FadeIn(title, shift=DOWN * 0.2),
            FadeIn(helper_text, shift=DOWN * 0.15),
            run_time=0.8,
        )
        self.wait(1)

        self.play(Write(equation), run_time=1.0)
        self.wait(1)

        subtract_left = MathTex("-1", font_size=46, color=ORANGE).next_to(
            VGroup(equation[0], equation[1], equation[2]), DOWN, buff=0.55
        )
        subtract_right = MathTex("-1", font_size=46, color=ORANGE).next_to(
            equation[4], DOWN, buff=0.55
        )
        self.play(
            FadeIn(subtract_left, shift=UP * 0.1),
            FadeIn(subtract_right, shift=UP * 0.1),
            run_time=0.7,
        )
        self.wait(1)

        next_equation = MathTex("3x", "=", "6", font_size=60).move_to(equation)
        self.play(
            TransformMatchingTex(equation, next_equation),
            FadeOut(subtract_left, shift=DOWN * 0.1),
            FadeOut(subtract_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        equation = next_equation
        self.wait(1)

        divide_left = MathTex("\\div 3", font_size=46, color=TEAL_D).next_to(equation[0], DOWN, buff=0.55)
        divide_right = MathTex("\\div 3", font_size=46, color=TEAL_D).next_to(equation[2], DOWN, buff=0.55)
        self.play(
            FadeIn(divide_left, shift=UP * 0.1),
            FadeIn(divide_right, shift=UP * 0.1),
            run_time=0.7,
        )
        self.wait(1)

        solved_x = MathTex("x", "=", "2", font_size=62, color=GREEN_E).move_to(equation)
        self.play(
            TransformMatchingTex(equation, solved_x),
            FadeOut(divide_left, shift=DOWN * 0.1),
            FadeOut(divide_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        equation = solved_x
        self.wait(1)

        reference_equation = MathTex("y", "=", "2", "x", "+", "1", font_size=56).move_to(LEFT * 2.3 + UP * 0.15)
        substitution_text = Text("Substitute x = 2", font_size=24, color=BLUE_D).move_to(helper_text)

        self.play(
            equation.animate.move_to(RIGHT * 3.0 + UP * 0.2).scale(0.8),
            Transform(helper_text, substitution_text),
            FadeIn(reference_equation, shift=DOWN * 0.15),
            run_time=0.9,
        )
        self.wait(1)

        x_highlight = SurroundingRectangle(reference_equation[3], color=BLUE_D, buff=0.12)
        moving_two = equation[2].copy()
        self.add(moving_two)
        self.play(Create(x_highlight), run_time=0.6)
        self.play(
            moving_two.animate.move_to(reference_equation[3].get_center() + UP * 0.45),
            run_time=0.9,
        )
        self.wait(1)

        substituted_y = MathTex("y", "=", "2", "(", "2", ")", "+", "1", font_size=56).move_to(reference_equation)
        self.play(
            TransformMatchingTex(reference_equation, substituted_y),
            FadeOut(moving_two, scale=0.85),
            FadeOut(x_highlight),
            run_time=1.0,
        )
        reference_equation = substituted_y
        self.wait(1)

        y_value = MathTex("y", "=", "5", font_size=58, color=GREEN_E).move_to(reference_equation)
        self.play(TransformMatchingTex(reference_equation, y_value), run_time=0.9)
        self.wait(1)

        solution_label = Text("Solution: (2, 5)", font_size=28, color=GREEN_E).move_to(DOWN * 0.45)
        self.play(FadeIn(solution_label, shift=UP * 0.15), run_time=0.7)
        self.wait(1.5)
