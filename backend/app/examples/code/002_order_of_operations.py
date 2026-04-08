from manim import *


class Scene1(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()

        title = Text("Order of Operations")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title, run_time=2))
        self.wait(1.5)

        pemdas = MathTex("P", r"\to", "E", r"\to", "M/D", r"\to", "A/S")
        pemdas.move_to(UP * 2)
        middle_group.add(pemdas)
        self.play(Write(pemdas, run_time=0.8))
        self.wait(2)

        expr1 = MathTex("4", "+", "2", "(", "5", "-", "x", ")")
        expr1_value = MathTex("x", "=", "3")
        block1 = VGroup()
        block1.add(expr1)
        block1.add(expr1_value)
        block1.arrange(direction=DOWN, buff=0.4)
        block1.next_to(pemdas, DOWN, buff=0.5)
        middle_group.add(block1)
        self.play(Write(block1, run_time=0.8))
        self.wait(2)

        expr1_sub = MathTex("4", "+", "2", "(", "5", "-", "3", ")")
        expr1_sub.move_to(block1)
        middle_group.add(expr1_sub)
        self.play(ReplacementTransform(block1, expr1_sub, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_sub)
        self.wait(1)

        expr1_paren = MathTex("4", "+", "2", "(", "5", "-", "3", ")")
        expr1_paren.move_to(expr1_sub)
        expr1_paren.set_color_by_tex("5", BLUE)
        expr1_paren.set_color_by_tex("3", BLUE)
        middle_group.add(expr1_paren)
        self.play(ReplacementTransform(expr1_sub, expr1_paren, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_paren)
        self.wait(2)

        expr1_after_paren = MathTex("4", "+", "2", "(", "2", ")")
        expr1_after_paren.move_to(expr1_paren)
        middle_group.add(expr1_after_paren)
        self.play(ReplacementTransform(expr1_paren, expr1_after_paren, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_after_paren)
        self.wait(1)

        expr1_mult = MathTex("4", "+", "2", "(", "2", ")")
        expr1_mult.move_to(expr1_after_paren)
        expr1_mult.set_color_by_tex("2", BLUE)
        middle_group.add(expr1_mult)
        self.play(ReplacementTransform(expr1_after_paren, expr1_mult, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_mult)
        self.wait(2)

        expr1_after_mult = MathTex("4", "+", "4")
        expr1_after_mult.move_to(expr1_mult)
        middle_group.add(expr1_after_mult)
        self.play(ReplacementTransform(expr1_mult, expr1_after_mult, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_after_mult)
        self.wait(1)

        expr1_add = MathTex("4", "+", "4")
        expr1_add.move_to(expr1_after_mult)
        expr1_add.set_color_by_tex("4", BLUE)
        middle_group.add(expr1_add)
        self.play(ReplacementTransform(expr1_after_mult, expr1_add, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_add)
        self.wait(2)

        expr1_result = MathTex("8", color=GREEN)
        expr1_result.move_to(expr1_add)
        middle_group.add(expr1_result)
        self.play(ReplacementTransform(expr1_add, expr1_result, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        self.wait(1)

        expr2 = MathTex("3", "(", "2", "+", "x", ")", "^2")
        expr2_value = MathTex("x", "=", "1")
        block2 = VGroup()
        block2.add(expr2)
        block2.add(expr2_value)
        block2.arrange(direction=DOWN, buff=0.4)
        block2.next_to(expr1_result, DOWN, buff=0.7)
        middle_group.add(block2)
        self.play(Write(block2, run_time=0.8))
        self.wait(2)

        expr2_sub = MathTex("3", "(", "2", "+", "1", ")", "^2")
        expr2_sub.move_to(block2)
        middle_group.add(expr2_sub)
        self.play(ReplacementTransform(block2, expr2_sub, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        middle_group.add(expr2_sub)
        self.wait(1)

        expr2_paren = MathTex("3", "(", "2", "+", "1", ")", "^2")
        expr2_paren.move_to(expr2_sub)
        expr2_paren.set_color_by_tex("2", BLUE)
        expr2_paren.set_color_by_tex("1", BLUE)
        middle_group.add(expr2_paren)
        self.play(ReplacementTransform(expr2_sub, expr2_paren, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        middle_group.add(expr2_paren)
        self.wait(2)

        expr2_after_paren = MathTex("3", "(", "3", ")", "^2")
        expr2_after_paren.move_to(expr2_paren)
        middle_group.add(expr2_after_paren)
        self.play(ReplacementTransform(expr2_paren, expr2_after_paren, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        middle_group.add(expr2_after_paren)
        self.wait(1)

        expr2_exp = MathTex("3", "(", "3", ")", "^2")
        expr2_exp.move_to(expr2_after_paren)
        expr2_exp.set_color_by_tex("^2", BLUE)
        middle_group.add(expr2_exp)
        self.play(ReplacementTransform(expr2_after_paren, expr2_exp, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        middle_group.add(expr2_exp)
        self.wait(2)

        expr2_after_exp = MathTex("3", r"\cdot", "9")
        expr2_after_exp.move_to(expr2_exp)
        middle_group.add(expr2_after_exp)
        self.play(ReplacementTransform(expr2_exp, expr2_after_exp, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        middle_group.add(expr2_after_exp)
        self.wait(1)

        expr2_mult = MathTex("3", r"\cdot", "9")
        expr2_mult.move_to(expr2_after_exp)
        expr2_mult.set_color_by_tex("3", BLUE)
        expr2_mult.set_color_by_tex("9", BLUE)
        middle_group.add(expr2_mult)
        self.play(ReplacementTransform(expr2_after_exp, expr2_mult, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        middle_group.add(expr2_mult)
        self.wait(2)

        expr2_result = MathTex("27", color=GREEN)
        expr2_result.move_to(expr2_mult)
        middle_group.add(expr2_result)
        self.play(ReplacementTransform(expr2_mult, expr2_result, run_time=0.8))
        middle_group = VGroup()
        middle_group.add(pemdas)
        middle_group.add(expr1_result)
        middle_group.add(expr2_result)
        self.wait(1)

        final_result = MathTex(
            "4",
            "+",
            "2",
            "(",
            "5",
            "-",
            "3",
            ")",
            "=",
            "8",
            r"\quad",
            "3",
            "(",
            "2",
            "+",
            "1",
            ")",
            "^2",
            "=",
            "27",
        )
        final_result.scale(0.8)
        final_result.to_edge(DOWN)
        final_result.set_color(GREEN)
        bottom_group.add(final_result)
        source_block = VGroup()
        source_block.add(expr1_result)
        source_block.add(expr2_result)
        self.play(TransformFromCopy(source_block, final_result, run_time=0.8))
        self.wait()

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)
