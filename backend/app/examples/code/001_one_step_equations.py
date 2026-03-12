from manim import *


def build_balance_scale() -> VGroup:
    beam = Line(LEFT * 1.8, RIGHT * 1.8, stroke_width=8, color=GRAY_D)
    post = Line(ORIGIN + DOWN * 0.1, DOWN * 0.9, stroke_width=8, color=GRAY_D)
    support = Polygon(
        DOWN * 0.9,
        LEFT * 0.35 + DOWN * 1.55,
        RIGHT * 0.35 + DOWN * 1.55,
        color=GRAY_D,
        fill_color=GRAY_D,
        fill_opacity=1,
        stroke_width=0,
    )

    left_hanger = Line(LEFT * 1.2, LEFT * 1.2 + UP * 0.55, color=GRAY_C)
    right_hanger = Line(RIGHT * 1.2, RIGHT * 1.2 + UP * 0.55, color=GRAY_C)
    left_pan = ArcBetweenPoints(
        left_hanger.get_end() + LEFT * 0.7,
        left_hanger.get_end() + RIGHT * 0.7,
        angle=PI / 3,
        color=BLUE_D,
        stroke_width=5,
    )
    right_pan = ArcBetweenPoints(
        right_hanger.get_end() + LEFT * 0.7,
        right_hanger.get_end() + RIGHT * 0.7,
        angle=PI / 3,
        color=BLUE_D,
        stroke_width=5,
    )

    scale = VGroup(
        beam,
        post,
        support,
        left_hanger,
        right_hanger,
        left_pan,
        right_pan,
    )
    return scale.scale(0.68).to_edge(DOWN, buff=0.35)


def position_equation(left_side: Mobject, equal_sign: Mobject, right_side: Mobject, center_point: np.ndarray) -> None:
    equal_sign.move_to(center_point)
    left_side.next_to(equal_sign, LEFT, buff=0.35)
    right_side.next_to(equal_sign, RIGHT, buff=0.35)


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("One-Step Equations", font_size=42, weight=BOLD).to_edge(UP, buff=0.35)
        balance_scale = build_balance_scale()

        equal_sign = MathTex("=", font_size=68).move_to(UP * 0.65)
        left_side = MathTex("x", "+", "7", font_size=68)
        right_side = MathTex("12", font_size=68)
        position_equation(left_side, equal_sign, right_side, UP * 0.65)

        self.play(
            FadeIn(title, shift=DOWN * 0.2),
            FadeIn(balance_scale, shift=UP * 0.2),
            run_time=0.8,
        )
        self.wait(1)

        self.play(Write(left_side), Write(equal_sign), Write(right_side), run_time=1.0)
        self.wait(1)

        plus_seven_group = VGroup(left_side[1], left_side[2])
        moving_plus_seven = plus_seven_group.copy()
        subtract_left = MathTex("-7", font_size=56, color=ORANGE).next_to(left_side, DOWN, buff=0.7)
        subtract_right = MathTex("-7", font_size=56, color=ORANGE).next_to(right_side, DOWN, buff=0.7)

        self.add(moving_plus_seven)
        self.play(
            moving_plus_seven.animate.set_color(ORANGE).move_to(equal_sign.get_center() + DOWN * 0.95),
            run_time=0.8,
        )
        self.wait(0.5)
        self.play(
            TransformFromCopy(moving_plus_seven, subtract_left),
            TransformFromCopy(moving_plus_seven, subtract_right),
            run_time=0.8,
        )
        self.play(FadeOut(moving_plus_seven), run_time=0.3)
        self.play(Indicate(balance_scale, color=GREEN_E, scale_factor=1.03), run_time=0.8)
        self.wait(1)

        next_left = MathTex("x", font_size=68)
        next_right = MathTex("5", font_size=68)
        position_equation(next_left, equal_sign, next_right, UP * 0.65)
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

        next_left = MathTex("3", "x", font_size=68)
        next_right = MathTex("15", font_size=68)
        position_equation(next_left, equal_sign, next_right, UP * 0.65)
        self.play(
            TransformMatchingTex(left_side, next_left),
            TransformMatchingTex(right_side, next_right),
            run_time=0.8,
        )
        left_side = next_left
        right_side = next_right
        self.wait(1)

        moving_three = left_side[0].copy()
        divide_left = MathTex("\\div 3", font_size=54, color=TEAL_D).next_to(left_side, DOWN, buff=0.7)
        divide_right = MathTex("\\div 3", font_size=54, color=TEAL_D).next_to(right_side, DOWN, buff=0.7)

        self.add(moving_three)
        self.play(
            moving_three.animate.set_color(TEAL_D).move_to(equal_sign.get_center() + DOWN * 0.95),
            run_time=0.8,
        )
        self.wait(0.5)
        self.play(
            TransformFromCopy(moving_three, divide_left),
            TransformFromCopy(moving_three, divide_right),
            run_time=0.8,
        )
        self.play(FadeOut(moving_three), run_time=0.3)
        self.play(Indicate(balance_scale, color=GREEN_E, scale_factor=1.03), run_time=0.8)
        self.wait(1)

        next_left = MathTex("x", font_size=68)
        next_right = MathTex("5", font_size=68)
        position_equation(next_left, equal_sign, next_right, UP * 0.65)
        self.play(
            TransformMatchingTex(left_side, next_left),
            TransformMatchingTex(right_side, next_right),
            FadeOut(divide_left, shift=DOWN * 0.1),
            FadeOut(divide_right, shift=DOWN * 0.1),
            run_time=0.9,
        )
        self.wait(1.5)
