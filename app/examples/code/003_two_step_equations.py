from manim import *


def position_equation(left_side: Mobject, equal_sign: Mobject, right_side: Mobject, center_point: np.ndarray) -> None:
    equal_sign.move_to(center_point)
    left_side.next_to(equal_sign, LEFT, buff=0.35)
    right_side.next_to(equal_sign, RIGHT, buff=0.35)


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("Two-Step Equations", font_size=40, weight=BOLD).to_edge(UP, buff=0.35)
        helper_label = Text("Undo last operation first", font_size=28, color=YELLOW_E).next_to(
            title, DOWN, buff=0.35
        )
        step_one_label = Text("1. Remove the constant", font_size=24, color=ORANGE).next_to(
            helper_label, DOWN, buff=0.25
        )
        step_two_label = Text("2. Remove the coefficient", font_size=24, color=TEAL_D).next_to(
            step_one_label, DOWN, buff=0.16
        )

        equal_sign = MathTex("=", font_size=66).move_to(UP * 0.25)
        left_side = MathTex("2x", "+", "5", font_size=64)
        left_side[1].set_color(ORANGE)
        left_side[2].set_color(ORANGE)
        right_side = MathTex("15", font_size=64)
        position_equation(left_side, equal_sign, right_side, UP * 0.25)

        self.play(
            FadeIn(title, shift=DOWN * 0.2),
            FadeIn(helper_label, shift=DOWN * 0.15),
            FadeIn(step_one_label, shift=DOWN * 0.15),
            FadeIn(step_two_label, shift=DOWN * 0.15),
            run_time=0.8,
        )
        self.wait(1)

        self.play(Write(left_side), Write(equal_sign), Write(right_side), run_time=1.0)
        self.wait(1)

        subtract_left = MathTex("-5", font_size=50, color=ORANGE).next_to(left_side, DOWN, buff=0.7)
        subtract_right = MathTex("-5", font_size=50, color=ORANGE).next_to(right_side, DOWN, buff=0.7)

        self.play(
            FadeIn(subtract_left, shift=UP * 0.1),
            FadeIn(subtract_right, shift=UP * 0.1),
            run_time=0.7,
        )
        self.wait(1)

        next_left = MathTex("2x", font_size=64)
        next_right = MathTex("10", font_size=64)
        position_equation(next_left, equal_sign, next_right, UP * 0.25)
        self.play(
            TransformMatchingTex(left_side, next_left),
            TransformMatchingTex(right_side, next_right),
            FadeOut(subtract_left, shift=DOWN * 0.1),
            FadeOut(subtract_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        left_side = next_left
        right_side = next_right
        self.wait(1)

        highlighted_left = MathTex("2", "x", font_size=64)
        highlighted_left[0].set_color(TEAL_D)
        position_equation(highlighted_left, equal_sign, right_side, UP * 0.25)
        self.play(TransformMatchingTex(left_side, highlighted_left), run_time=0.6)
        left_side = highlighted_left

        divide_left = MathTex("\\div 2", font_size=48, color=TEAL_D).next_to(left_side, DOWN, buff=0.7)
        divide_right = MathTex("\\div 2", font_size=48, color=TEAL_D).next_to(right_side, DOWN, buff=0.7)
        self.play(
            FadeIn(divide_left, shift=UP * 0.1),
            FadeIn(divide_right, shift=UP * 0.1),
            run_time=0.7,
        )
        self.wait(1)

        next_left = MathTex("x", font_size=68, color=GREEN_E)
        next_right = MathTex("5", font_size=68, color=GREEN_E)
        position_equation(next_left, equal_sign, next_right, UP * 0.25)
        self.play(
            TransformMatchingTex(left_side, next_left),
            TransformMatchingTex(right_side, next_right),
            FadeOut(divide_left, shift=DOWN * 0.1),
            FadeOut(divide_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        left_side = next_left
        right_side = next_right
        self.wait(1)

        next_left = MathTex("3x", "-", "4", font_size=64)
        next_left[1].set_color(ORANGE)
        next_left[2].set_color(ORANGE)
        next_right = MathTex("11", font_size=64)
        position_equation(next_left, equal_sign, next_right, UP * 0.25)
        self.play(
            TransformMatchingTex(left_side, next_left),
            TransformMatchingTex(right_side, next_right),
            run_time=0.8,
        )
        left_side = next_left
        right_side = next_right
        self.wait(1)

        add_left = MathTex("+4", font_size=50, color=ORANGE).next_to(left_side, DOWN, buff=0.7)
        add_right = MathTex("+4", font_size=50, color=ORANGE).next_to(right_side, DOWN, buff=0.7)
        self.play(
            FadeIn(add_left, shift=UP * 0.1),
            FadeIn(add_right, shift=UP * 0.1),
            run_time=0.7,
        )
        self.wait(1)

        next_left = MathTex("3x", font_size=64)
        next_right = MathTex("15", font_size=64)
        position_equation(next_left, equal_sign, next_right, UP * 0.25)
        self.play(
            TransformMatchingTex(left_side, next_left),
            TransformMatchingTex(right_side, next_right),
            FadeOut(add_left, shift=DOWN * 0.1),
            FadeOut(add_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        left_side = next_left
        right_side = next_right
        self.wait(1)

        divide_left_two = MathTex("\\div 3", font_size=48, color=TEAL_D).next_to(left_side, DOWN, buff=0.7)
        divide_right_two = MathTex("\\div 3", font_size=48, color=TEAL_D).next_to(right_side, DOWN, buff=0.7)
        self.play(
            FadeIn(divide_left_two, shift=UP * 0.1),
            FadeIn(divide_right_two, shift=UP * 0.1),
            run_time=0.7,
        )
        self.wait(1)

        next_left = MathTex("x", font_size=68, color=GREEN_E)
        next_right = MathTex("5", font_size=68, color=GREEN_E)
        position_equation(next_left, equal_sign, next_right, UP * 0.25)
        self.play(
            TransformMatchingTex(left_side, next_left),
            TransformMatchingTex(right_side, next_right),
            FadeOut(divide_left_two, shift=DOWN * 0.1),
            FadeOut(divide_right_two, shift=DOWN * 0.1),
            run_time=0.9,
        )
        self.wait(1.5)


class Scene2(Scene):
    def construct(self) -> None:
        title = Text("Both Sides Matter", font_size=40, weight=BOLD).to_edge(UP, buff=0.35)
        divider = Line(UP * 1.8, DOWN * 1.3, color=GRAY_C, stroke_width=3)

        wrong_label = Text("Wrong", font_size=28, color=RED_E).move_to(LEFT * 2.2 + UP * 1.9)
        right_label = Text("Right", font_size=28, color=GREEN_E).move_to(RIGHT * 2.2 + UP * 1.9)
        wrong_icon = Text("X", font_size=30, color=RED_E).next_to(wrong_label, RIGHT, buff=0.16)
        right_icon = MathTex("\\checkmark", font_size=34, color=GREEN_E).next_to(right_label, RIGHT, buff=0.16)

        wrong_equal = MathTex("=", font_size=54).move_to(LEFT * 2.2 + UP * 0.8)
        wrong_left = MathTex("2x", "+", "5", font_size=50).next_to(wrong_equal, LEFT, buff=0.3)
        wrong_right = MathTex("15", font_size=50).next_to(wrong_equal, RIGHT, buff=0.3)

        right_equal = MathTex("=", font_size=54).move_to(RIGHT * 2.2 + UP * 0.8)
        right_left = MathTex("2x", "+", "5", font_size=50).next_to(right_equal, LEFT, buff=0.3)
        right_right = MathTex("15", font_size=50).next_to(right_equal, RIGHT, buff=0.3)

        self.play(
            FadeIn(title, shift=DOWN * 0.2),
            FadeIn(divider),
            FadeIn(wrong_label, shift=DOWN * 0.15),
            FadeIn(wrong_icon, shift=DOWN * 0.15),
            FadeIn(right_label, shift=DOWN * 0.15),
            FadeIn(right_icon, shift=DOWN * 0.15),
            run_time=0.8,
        )
        self.wait(1)

        self.play(
            Write(wrong_left),
            Write(wrong_equal),
            Write(wrong_right),
            Write(right_left),
            Write(right_equal),
            Write(right_right),
            run_time=1.0,
        )
        self.wait(1)

        wrong_subtract = MathTex("-5", font_size=42, color=RED_E).next_to(wrong_right, DOWN, buff=0.6)
        right_subtract_left = MathTex("-5", font_size=42, color=GREEN_E).next_to(right_left, DOWN, buff=0.6)
        right_subtract_right = MathTex("-5", font_size=42, color=GREEN_E).next_to(right_right, DOWN, buff=0.6)

        self.play(FadeIn(wrong_subtract, shift=UP * 0.1), run_time=0.6)
        self.play(
            FadeIn(right_subtract_left, shift=UP * 0.1),
            FadeIn(right_subtract_right, shift=UP * 0.1),
            run_time=0.6,
        )
        self.wait(1)

        wrong_left_next = MathTex("2x", "+", "5", font_size=50, color=RED_E)
        wrong_right_next = MathTex("10", font_size=50, color=RED_E)
        position_equation(wrong_left_next, wrong_equal, wrong_right_next, LEFT * 2.2 + UP * 0.8)

        right_left_next = MathTex("2x", font_size=50, color=GREEN_E)
        right_right_next = MathTex("10", font_size=50, color=GREEN_E)
        position_equation(right_left_next, right_equal, right_right_next, RIGHT * 2.2 + UP * 0.8)

        self.play(
            TransformMatchingTex(wrong_left, wrong_left_next),
            TransformMatchingTex(wrong_right, wrong_right_next),
            FadeOut(wrong_subtract, shift=DOWN * 0.1),
            TransformMatchingTex(right_left, right_left_next),
            TransformMatchingTex(right_right, right_right_next),
            FadeOut(right_subtract_left, shift=DOWN * 0.1),
            FadeOut(right_subtract_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        wrong_left = wrong_left_next
        wrong_right = wrong_right_next
        right_left = right_left_next
        right_right = right_right_next
        self.wait(1)

        wrong_note = Text("Only one side changed", font_size=22, color=RED_E).next_to(
            VGroup(wrong_left, wrong_equal, wrong_right), DOWN, buff=0.45
        )
        right_note = Text("Same move on both sides", font_size=22, color=GREEN_E).next_to(
            VGroup(right_left, right_equal, right_right), DOWN, buff=0.45
        )
        self.play(FadeIn(wrong_note, shift=UP * 0.1), FadeIn(right_note, shift=UP * 0.1), run_time=0.6)
        self.wait(1)

        self.play(
            FadeOut(
                VGroup(
                    wrong_label,
                    wrong_icon,
                    right_label,
                    right_icon,
                    divider,
                    wrong_left,
                    wrong_equal,
                    wrong_right,
                    right_left,
                    right_equal,
                    right_right,
                    wrong_note,
                    right_note,
                ),
                shift=UP * 0.15,
            ),
            run_time=0.8,
        )
        self.wait(1)

        negative_title = Text("Negative Example", font_size=30, color=YELLOW_E).move_to(UP * 0.45)
        negative_equal = MathTex("=", font_size=60).move_to(DOWN * 0.2)
        negative_left = MathTex("x", "-", "7", font_size=60).next_to(negative_equal, LEFT, buff=0.3)
        negative_right = MathTex("-2", font_size=60).next_to(negative_equal, RIGHT, buff=0.3)

        self.play(
            FadeIn(negative_title, shift=DOWN * 0.15),
            Write(negative_left),
            Write(negative_equal),
            Write(negative_right),
            run_time=0.9,
        )
        self.wait(1)

        add_left = MathTex("+7", font_size=44, color=YELLOW_E).next_to(negative_left, DOWN, buff=0.65)
        add_right = MathTex("+7", font_size=44, color=YELLOW_E).next_to(negative_right, DOWN, buff=0.65)
        self.play(FadeIn(add_left, shift=UP * 0.1), FadeIn(add_right, shift=UP * 0.1), run_time=0.7)
        self.wait(1)

        negative_left_next = MathTex("x", font_size=64, color=GREEN_E)
        negative_right_next = MathTex("5", font_size=64, color=GREEN_E)
        position_equation(negative_left_next, negative_equal, negative_right_next, DOWN * 0.2)
        self.play(
            TransformMatchingTex(negative_left, negative_left_next),
            TransformMatchingTex(negative_right, negative_right_next),
            FadeOut(add_left, shift=DOWN * 0.1),
            FadeOut(add_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        self.wait(1.5)
