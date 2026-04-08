from manim import *


class Scene1(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()

        title = Text("One-Step Equations")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title, run_time=2))
        self.wait(1.5)

        equation1 = MathTex("x", "+", "7", "=", "12")
        equation1.move_to(UP * 2)
        middle_group.add(equation1)
        self.play(Write(equation1, run_time=0.8))
        self.wait(2)

        operation1 = MathTex("-7", "\\qquad", "-7", color=ORANGE)
        operation1.next_to(equation1, DOWN, buff=0.6)
        middle_group.add(operation1)
        self.play(FadeIn(operation1, run_time=0.8))
        self.wait(2)

        solved1 = MathTex("x", "=", "5")
        solved1.move_to(equation1)
        self.play(ReplacementTransform(VGroup(equation1, operation1), solved1, run_time=0.8))
        middle_group = VGroup(solved1)
        self.wait(1)

        self.play(FadeOut(middle_group, run_time=0.8))
        middle_group = VGroup()
        self.wait(1)

        equation2 = MathTex("3", "x", "=", "15")
        equation2.move_to(UP * 2)
        middle_group.add(equation2)
        self.play(Write(equation2, run_time=0.8))
        self.wait(2)

        equation2_highlight = MathTex("3", "x", "=", "15")
        equation2_highlight.move_to(equation2)
        equation2_highlight.set_color_by_tex("3", BLUE)
        self.play(ReplacementTransform(equation2, equation2_highlight, run_time=0.8))
        middle_group = VGroup(equation2_highlight)
        self.wait(2)

        operation2 = MathTex("\\div 3", "\\qquad", "\\div 3", color=ORANGE)
        operation2.next_to(equation2_highlight, DOWN, buff=0.6)
        middle_group.add(operation2)
        self.play(FadeIn(operation2, run_time=0.8))
        self.wait(2)

        solved2 = MathTex("x", "=", "5", color=GREEN)
        solved2.move_to(equation2_highlight)
        self.play(ReplacementTransform(VGroup(equation2_highlight, operation2), solved2, run_time=0.8))
        middle_group = VGroup(solved2)
        self.wait(1)

        final_result = MathTex("x", "=", "5", color=GREEN)
        final_result.to_edge(DOWN)
        bottom_group.add(final_result)
        self.play(TransformFromCopy(solved2, final_result, run_time=0.8))
        self.wait()

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)
