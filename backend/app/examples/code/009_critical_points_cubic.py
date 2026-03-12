from manim import *


RULE_COLOR = BLUE_D
HIGHLIGHT_COLOR = YELLOW_E
RESULT_COLOR = GREEN_E
ACCENT_COLOR = ORANGE


def make_info_box(text: str, color: str = RULE_COLOR, width: float = 5.8) -> VGroup:
    box = RoundedRectangle(
        width=width,
        height=0.78,
        corner_radius=0.16,
        stroke_color=color,
        fill_color=BLUE_E,
        fill_opacity=0.12,
    )
    label = Text(text, font_size=24, color=color)
    label.move_to(box.get_center())
    return VGroup(box, label)


def make_value_marker(number_line: NumberLine, value: float, label_text: str, color: str) -> VGroup:
    marker = Line(UP * 0.28, DOWN * 0.28, color=color, stroke_width=6)
    marker.move_to(number_line.n2p(value))
    dot = Dot(number_line.n2p(value), color=color, radius=0.06)
    label = Text(label_text, font_size=24, color=color).next_to(marker, UP, buff=0.16)
    return VGroup(marker, dot, label)


class Scene1(Scene):
    def construct(self) -> None:
        title = Text("Find Critical x-Values", font_size=36, weight=BOLD).to_edge(UP, buff=0.28)
        rule_box = make_info_box(
            "Critical points: f'(x) = 0 or f'(x) is undefined",
            width=7.1,
        ).next_to(title, DOWN, buff=0.2)

        function = MathTex(
            "f(x)",
            "=",
            "x^3",
            "-",
            "6x^2",
            "+",
            "9x",
            font_size=60,
        ).move_to(UP * 1.1)

        derivative = MathTex(
            "f'(x)",
            "=",
            "3x^2",
            "-",
            "12x",
            "+",
            "9",
            font_size=58,
        ).move_to(UP * 0.2)

        set_zero = MathTex(
            "3x^2",
            "-",
            "12x",
            "+",
            "9",
            "=",
            "0",
            font_size=58,
        ).move_to(DOWN * 1.05)

        divide_note = Text("Divide every term by 3", font_size=26, color=ACCENT_COLOR).move_to(DOWN * 1.9)
        simplified = MathTex(
            "x^2",
            "-",
            "4x",
            "+",
            "3",
            "=",
            "0",
            font_size=58,
        ).move_to(DOWN * 1.05)

        self.play(FadeIn(title, shift=DOWN * 0.12), FadeIn(rule_box, shift=DOWN * 0.12), run_time=0.8)
        self.wait(1)

        self.play(Write(function), run_time=1.0)
        self.wait(1)

        self.play(TransformFromCopy(function, derivative), run_time=1.0)
        self.wait(1)

        self.play(
            TransformFromCopy(VGroup(derivative[2], derivative[3], derivative[4], derivative[5], derivative[6]), set_zero[:5]),
            FadeIn(set_zero[5], shift=UP * 0.06),
            FadeIn(set_zero[6], shift=UP * 0.06),
            run_time=1.0,
        )
        self.wait(1)

        self.play(FadeIn(divide_note, shift=UP * 0.08), run_time=0.7)
        self.wait(0.8)

        self.play(
            TransformMatchingTex(set_zero, simplified),
            FadeOut(divide_note),
            run_time=1.0,
        )
        self.wait(1.5)


class Scene2(Scene):
    def construct(self) -> None:
        title = Text("Solve for the Critical x-Values", font_size=36, weight=BOLD).to_edge(UP, buff=0.28)
        equation = MathTex(
            "x^2",
            "-",
            "4x",
            "+",
            "3",
            "=",
            "0",
            font_size=62,
        ).move_to(UP * 1.25)

        factored = MathTex(
            "(x-1)",
            "(x-3)",
            "=",
            "0",
            font_size=62,
        ).move_to(equation)

        solutions = VGroup(
            MathTex("x", "=", "1", font_size=52, color=RESULT_COLOR),
            MathTex("x", "=", "3", font_size=52, color=RESULT_COLOR),
        ).arrange(RIGHT, buff=1.1).move_to(DOWN * 0.25)

        number_line = NumberLine(
            x_range=[0, 4, 1],
            length=7.0,
            include_numbers=True,
            include_tip=False,
            font_size=26,
        ).move_to(DOWN * 1.8)

        marker_1 = make_value_marker(number_line, 1, "x = 1", RESULT_COLOR)
        marker_3 = make_value_marker(number_line, 3, "x = 3", RESULT_COLOR)

        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8)
        self.wait(1)

        self.play(Write(equation), run_time=1.0)
        self.wait(1)

        self.play(TransformMatchingTex(equation, factored), run_time=1.0)
        self.wait(1)

        self.play(
            FadeIn(solutions[0], shift=UP * 0.08),
            FadeIn(solutions[1], shift=UP * 0.08),
            run_time=0.8,
        )
        self.wait(1)

        self.play(Create(number_line), run_time=0.8)
        self.wait(0.8)

        self.play(
            TransformFromCopy(solutions[0][2], marker_1[0]),
            FadeIn(marker_1[1], scale=0.8),
            FadeIn(marker_1[2], shift=UP * 0.08),
            run_time=0.8,
        )
        self.wait(0.8)

        self.play(
            TransformFromCopy(solutions[1][2], marker_3[0]),
            FadeIn(marker_3[1], scale=0.8),
            FadeIn(marker_3[2], shift=UP * 0.08),
            run_time=0.8,
        )
        self.wait(1.5)


class Scene3(Scene):
    def construct(self) -> None:
        title = Text("Turn Critical x-Values into Points", font_size=36, weight=BOLD).to_edge(UP, buff=0.28)

        function = MathTex(
            "f(x)",
            "=",
            "x^3",
            "-",
            "6x^2",
            "+",
            "9x",
            font_size=54,
        ).move_to(LEFT * 3.25 + UP * 1.6)
        critical_values = VGroup(
            MathTex("x", "=", "1", font_size=48, color=RESULT_COLOR),
            MathTex("x", "=", "3", font_size=48, color=RESULT_COLOR),
        ).arrange(RIGHT, buff=1.0).move_to(LEFT * 3.25 + UP * 0.75)

        eval_box_1 = RoundedRectangle(
            width=4.6,
            height=1.65,
            corner_radius=0.18,
            stroke_color=HIGHLIGHT_COLOR,
            fill_color=BLACK,
            fill_opacity=0.08,
        ).move_to(LEFT * 3.2 + DOWN * 0.15)
        eval_box_2 = eval_box_1.copy().move_to(LEFT * 3.2 + DOWN * 1.95)

        eval_1_intro = MathTex("f(1)", "=", font_size=42)
        eval_1_intro.move_to(eval_box_1.get_center() + LEFT * 1.45)
        eval_1 = MathTex(
            "f(1)",
            "=",
            "1",
            "-",
            "6",
            "+",
            "9",
            "=",
            "4",
            font_size=42,
        ).move_to(eval_box_1.get_center())
        eval_2_intro = MathTex("f(3)", "=", font_size=42)
        eval_2_intro.move_to(eval_box_2.get_center() + LEFT * 1.45)
        eval_2 = MathTex(
            "f(3)",
            "=",
            "27",
            "-",
            "54",
            "+",
            "27",
            "=",
            "0",
            font_size=42,
        ).move_to(eval_box_2.get_center())
        eval_1[-1].set_color(RESULT_COLOR)
        eval_2[-1].set_color(RESULT_COLOR)

        plane = NumberPlane(
            x_range=[0, 4.5, 1],
            y_range=[-1, 5, 1],
            x_length=5.1,
            y_length=4.6,
            background_line_style={
                "stroke_color": BLUE_E,
                "stroke_opacity": 0.22,
                "stroke_width": 1,
            },
            axis_config={"include_numbers": True, "font_size": 22},
        ).move_to(RIGHT * 3.1 + DOWN * 0.3)
        axis_labels = plane.get_axis_labels(MathTex("x"), MathTex("y"))
        graph = plane.plot(lambda x: x**3 - 6 * x**2 + 9 * x, x_range=[0, 4.1], color=BLUE_D, stroke_width=6)

        point_1 = Dot(plane.c2p(1, 4), color=RESULT_COLOR, radius=0.08)
        point_3 = Dot(plane.c2p(3, 0), color=RESULT_COLOR, radius=0.08)

        point_label_1 = MathTex("(1,4)", font_size=32, color=RESULT_COLOR).next_to(point_1, UP + RIGHT, buff=0.12)
        point_label_3 = MathTex("(3,0)", font_size=32, color=RESULT_COLOR).next_to(point_3, DOWN + RIGHT, buff=0.12)

        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8)
        self.wait(1)

        self.play(Write(function), run_time=1.0)
        self.wait(1)

        self.play(
            FadeIn(critical_values[0], shift=UP * 0.08),
            FadeIn(critical_values[1], shift=UP * 0.08),
            run_time=0.8,
        )
        self.wait(1)

        self.play(Create(eval_box_1), run_time=0.6)
        self.play(
            TransformFromCopy(critical_values[0], eval_1_intro[0]),
            FadeIn(eval_1_intro[1], shift=UP * 0.05),
            run_time=0.8,
        )
        self.play(
            TransformMatchingTex(eval_1_intro, eval_1),
            run_time=0.8,
        )
        self.wait(1)

        self.play(Create(eval_box_2), run_time=0.6)
        self.play(
            TransformFromCopy(critical_values[1], eval_2_intro[0]),
            FadeIn(eval_2_intro[1], shift=UP * 0.05),
            run_time=0.8,
        )
        self.play(
            TransformMatchingTex(eval_2_intro, eval_2),
            run_time=0.8,
        )
        self.wait(1)

        self.play(Create(plane), FadeIn(axis_labels), run_time=1.0)
        self.play(Create(graph), run_time=1.0)
        self.wait(1)

        self.play(
            FadeIn(point_1, scale=0.8),
            FadeIn(point_3, scale=0.8),
            run_time=0.7,
        )
        self.wait(0.8)

        self.play(
            TransformFromCopy(VGroup(eval_1[2], eval_1[-1]), point_label_1),
            TransformFromCopy(VGroup(eval_2[2], eval_2[-1]), point_label_3),
            run_time=0.9,
        )
        self.wait(1)
        self.wait(1.5)
