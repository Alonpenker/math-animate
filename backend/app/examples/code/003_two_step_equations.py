from manim import *


class Scene1(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()

        title = Text("Two-Step Equations")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title), run_time=2)
        self.wait(1.5)

        eq1 = MathTex("2x", "+", "5", "=", "15")
        eq1.move_to(UP * 1.8)
        middle_group.add(eq1)
        self.play(Write(eq1), run_time=0.8)
        self.wait(2)

        cue_sub_5 = MathTex("/", "-", "5")
        cue_sub_5.set_color(ORANGE)
        cue_sub_5.next_to(eq1, RIGHT, buff=0.6)
        self.play(FadeIn(cue_sub_5), run_time=0.8)
        self.wait(1)

        eq1_after_sub = MathTex("2x", "=", "10")
        eq1_after_sub.move_to(eq1)
        middle_group.add(eq1_after_sub)
        self.play(ReplacementTransform(eq1, eq1_after_sub), run_time=0.8)
        middle_group.remove(eq1)
        self.wait(1)

        self.play(FadeOut(cue_sub_5), run_time=0.8)
        self.wait(1)

        cue_div_2 = MathTex("/", r"\div", "2")
        cue_div_2.set_color(ORANGE)
        cue_div_2.next_to(eq1_after_sub, RIGHT, buff=0.6)
        self.play(FadeIn(cue_div_2), run_time=0.8)
        self.wait(1)

        eq1_final = MathTex("x", "=", "5")
        eq1_final.move_to(eq1_after_sub)
        middle_group.add(eq1_final)
        self.play(ReplacementTransform(eq1_after_sub, eq1_final), run_time=0.8)
        middle_group.remove(eq1_after_sub)
        self.wait(1)

        self.play(FadeOut(cue_div_2), run_time=0.8)
        self.wait(1)

        self.play(FadeOut(middle_group), run_time=0.8)
        middle_group = VGroup()
        self.wait(1)

        eq2 = MathTex("3x", "-", "4", "=", "11")
        eq2.move_to(UP * 1.8)
        middle_group.add(eq2)
        self.play(Write(eq2), run_time=0.8)
        self.wait(2)

        cue_add_4 = MathTex("/", "+", "4")
        cue_add_4.set_color(ORANGE)
        cue_add_4.next_to(eq2, RIGHT, buff=0.6)
        self.play(FadeIn(cue_add_4), run_time=0.8)
        self.wait(1)

        eq2_after_add = MathTex("3x", "=", "15")
        eq2_after_add.move_to(eq2)
        middle_group.add(eq2_after_add)
        self.play(ReplacementTransform(eq2, eq2_after_add), run_time=0.8)
        middle_group.remove(eq2)
        self.wait(1)

        self.play(FadeOut(cue_add_4), run_time=0.8)
        self.wait(1)

        cue_div_3 = MathTex("/", r"\div", "3")
        cue_div_3.set_color(ORANGE)
        cue_div_3.next_to(eq2_after_add, RIGHT, buff=0.6)
        self.play(FadeIn(cue_div_3), run_time=0.8)
        self.wait(1)

        eq2_final = MathTex("x", "=", "5")
        eq2_final.move_to(eq2_after_add)
        middle_group.add(eq2_final)
        self.play(ReplacementTransform(eq2_after_add, eq2_final), run_time=0.8)
        middle_group.remove(eq2_after_add)
        self.wait(1)

        self.play(FadeOut(cue_div_3), run_time=0.8)
        self.wait(1)

        final_result = MathTex("x", "=", "5", color=GREEN)
        final_result.to_edge(DOWN)
        bottom_group.add(final_result)
        self.play(TransformFromCopy(eq2_final, final_result), run_time=0.8)
        self.wait(1)

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)


class Scene2(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()

        title = Text("Both Sides Matter")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title), run_time=2)
        self.wait(1.5)

        eq1 = MathTex("2x", "+", "5", "=", "15")
        eq1.move_to(UP * 1.8)
        middle_group.add(eq1)
        self.play(Write(eq1), run_time=0.8)
        self.wait(2)

        wrong_step = MathTex("2x", "=", "15")
        wrong_step.set_color(RED)
        wrong_step.move_to(eq1)
        middle_group.add(wrong_step)
        self.play(ReplacementTransform(eq1, wrong_step), run_time=0.8)
        middle_group.remove(eq1)
        self.wait(2)

        eq1_reset = MathTex("2x", "+", "5", "=", "15")
        eq1_reset.move_to(wrong_step)
        middle_group.add(eq1_reset)
        self.play(ReplacementTransform(wrong_step, eq1_reset), run_time=0.8)
        middle_group.remove(wrong_step)
        self.wait(1)

        cue_sub_5 = MathTex("/", "-", "5")
        cue_sub_5.set_color(ORANGE)
        cue_sub_5.next_to(eq1_reset, RIGHT, buff=0.6)
        self.play(FadeIn(cue_sub_5), run_time=0.8)
        self.wait(1)

        eq1_correct = MathTex("2x", "=", "10")
        eq1_correct.move_to(eq1_reset)
        middle_group.add(eq1_correct)
        self.play(ReplacementTransform(eq1_reset, eq1_correct), run_time=0.8)
        middle_group.remove(eq1_reset)
        self.wait(1)

        self.play(FadeOut(cue_sub_5), run_time=0.8)
        self.wait(1)

        self.play(FadeOut(middle_group), run_time=0.8)
        middle_group = VGroup()
        self.wait(1)

        eq2 = MathTex("x", "-", "7", "=", "-2")
        eq2.move_to(UP * 1.8)
        middle_group.add(eq2)
        self.play(Write(eq2), run_time=0.8)
        self.wait(2)

        cue_add_7 = MathTex("/", "+", "7")
        cue_add_7.set_color(ORANGE)
        cue_add_7.next_to(eq2, RIGHT, buff=0.6)
        self.play(FadeIn(cue_add_7), run_time=0.8)
        self.wait(1)

        eq2_final = MathTex("x", "=", "5")
        eq2_final.move_to(eq2)
        middle_group.add(eq2_final)
        self.play(ReplacementTransform(eq2, eq2_final), run_time=0.8)
        middle_group.remove(eq2)
        self.wait(1)

        self.play(FadeOut(cue_add_7), run_time=0.8)
        self.wait(1)

        final_result = MathTex("x", "=", "5", color=GREEN)
        final_result.to_edge(DOWN)
        bottom_group.add(final_result)
        self.play(TransformFromCopy(eq2_final, final_result), run_time=0.8)
        self.wait(1)

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)
