from manim import *


class Scene1(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()

        color_a = BLUE_B
        color_b = BLUE_D
        color_c = BLUE_E

        # Title section:
        title = Text("Factor ax^2 + bx + c")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title), run_time=2)
        self.wait(1.5)

        # Middle section:
        general_expr = MathTex("a", "x^2", "+", "b", "x", "+", "c")
        general_expr.move_to(UP * 2)
        middle_group.add(general_expr)
        self.play(Write(general_expr), run_time=0.8)
        self.wait(2)

        example_expr = MathTex("x^2", "+", "5", "x", "+", "6")
        example_expr.next_to(general_expr, DOWN, buff=0.6)
        middle_group.add(example_expr)
        self.play(Write(example_expr), run_time=0.8)
        self.wait(2)

        general_colored = MathTex("a", "x^2", "+", "b", "x", "+", "c")
        general_colored.move_to(UP * 2)
        general_colored.set_color_by_tex("a", color_a)
        general_colored.set_color_by_tex("b", color_b)
        general_colored.set_color_by_tex("c", color_c)

        example_colored = MathTex("x^2", "+", "5", "x", "+", "6")
        example_colored.next_to(general_colored, DOWN, buff=0.6)
        example_colored.set_color_by_tex("5", color_b)
        example_colored.set_color_by_tex("6", color_c)

        next_middle_group = VGroup()
        next_middle_group.add(general_colored)
        next_middle_group.add(example_colored)
        self.play(
            ReplacementTransform(general_expr, general_colored),
            ReplacementTransform(example_expr, example_colored),
            run_time=0.8,
        )
        middle_group = next_middle_group
        self.wait(2)

        map_a = MathTex("a", "=", "1")
        map_a.set_color_by_tex("a", color_a)
        map_a.set_color_by_tex("1", color_a)

        map_b = MathTex("b", "=", "5")
        map_b.set_color_by_tex("b", color_b)
        map_b.set_color_by_tex("5", color_b)

        map_c = MathTex("c", "=", "6")
        map_c.set_color_by_tex("c", color_c)
        map_c.set_color_by_tex("6", color_c)

        parameter_map = VGroup(map_a, map_b, map_c)
        parameter_map.arrange(DOWN, buff=0.35)
        parameter_map.next_to(example_colored, DOWN, buff=0.5)
        middle_group.add(parameter_map)
        self.play(Write(parameter_map), run_time=0.8)
        self.wait(2)

        rule_product = MathTex("r_1 r_2", "=", "a", "\\cdot", "c")
        rule_product.set_color_by_tex("a", color_a)
        rule_product.set_color_by_tex("c", color_c)

        rule_sum = MathTex("r_1 + r_2", "=", "b")
        rule_sum.set_color_by_tex("b", color_b)

        rule_group = VGroup(rule_product, rule_sum)
        rule_group.arrange(DOWN, buff=0.35)
        rule_group.next_to(parameter_map, DOWN, buff=0.5)
        middle_group.add(rule_group)
        self.play(Write(rule_group), run_time=0.8)
        self.wait(2)

        value_product = MathTex("r_1 r_2", "=", "1", "\\cdot", "6", "=", "6")
        value_product.set_color_by_tex("1", color_a)
        value_product.set_color_by_tex("6", color_c)

        value_sum = MathTex("r_1 + r_2", "=", "5")
        value_sum.set_color_by_tex("5", color_b)

        value_group = VGroup(value_product, value_sum)
        value_group.arrange(DOWN, buff=0.35)
        value_group.next_to(parameter_map, DOWN, buff=0.5)

        next_middle_group = VGroup()
        next_middle_group.add(general_colored)
        next_middle_group.add(example_colored)
        next_middle_group.add(parameter_map)
        next_middle_group.add(value_group)
        self.play(ReplacementTransform(rule_group, value_group), run_time=0.8)
        middle_group = next_middle_group
        self.wait(1)

        self.play(FadeOut(middle_group), run_time=0.8)
        middle_group = VGroup()
        self.wait(2)

        pair_check_1 = MathTex("(1,6):\\ 1\\cdot 6=6,\\ 1+6=7")
        pair_check_2 = MathTex("(2,3):\\ 2\\cdot 3=6,\\ 2+3=5")
        pair_check_1.set_color(RED)
        pair_check_2.set_color(BLUE)

        pair_group = VGroup(pair_check_1, pair_check_2)
        pair_group.arrange(DOWN, buff=0.4)
        pair_group.move_to(UP * 0.8)
        middle_group.add(pair_group)
        self.play(Write(pair_group), run_time=0.8)
        self.wait(2)

        factored_middle = MathTex("(x+2)(x+3)")
        factored_middle.next_to(pair_group, DOWN, buff=0.6)
        middle_group.add(factored_middle)
        self.play(TransformFromCopy(pair_check_2, factored_middle), run_time=0.8)
        self.wait(1)

        # Bottom section:
        final_result = MathTex("x^2 + 5x + 6 = (x+2)(x+3)")
        final_result.to_edge(DOWN)
        final_result.set_color(GREEN)
        bottom_group.add(final_result)
        self.play(TransformFromCopy(factored_middle, final_result), run_time=0.8)
        self.wait()

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)
