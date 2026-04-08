from manim import *


class Scene1(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()
        a_color = BLUE_C
        b_color = BLUE_D
        c_color = BLUE_E

        title = Text("Set Up the Quadratic Formula")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title), run_time=2)
        self.wait(1.5)

        equation = MathTex("2x^2", "-", "7x", "+", "3", "=", "0")
        equation.move_to(UP * 2)
        middle_group.add(equation)
        self.play(Write(equation), run_time=0.8)
        self.wait(2)

        general_form = MathTex("a", "x^2", "+", "b", "x", "+", "c", "=", "0")
        general_form.set_color_by_tex("a", a_color)
        general_form.set_color_by_tex("b", b_color)
        general_form.set_color_by_tex("c", c_color)
        general_form.next_to(equation, DOWN, buff=0.7)
        middle_group.add(general_form)
        self.play(Write(general_form), run_time=0.8)
        self.wait(2)

        coefficients = MathTex("a", "=", "2", ",", "b", "=", "-7", ",", "c", "=", "3")
        coefficients.set_color_by_tex("a", a_color)
        coefficients.set_color_by_tex("2", a_color)
        coefficients.set_color_by_tex("b", b_color)
        coefficients.set_color_by_tex("-7", b_color)
        coefficients.set_color_by_tex("c", c_color)
        coefficients.set_color_by_tex("3", c_color)
        coefficients.next_to(general_form, DOWN, buff=0.7)
        middle_group.add(coefficients)
        self.play(Write(coefficients), run_time=0.8)
        self.wait(2)

        self.play(FadeOut(middle_group), run_time=0.8)
        self.wait(1)
        middle_group = VGroup()

        formula = MathTex(
            "x",
            "=",
            "{-",
            "b",
            "\\pm\\sqrt{",
            "b",
            "^2-4",
            "a",
            "c",
            "}",
            r"\over",
            "2",
            "a",
            "}",
        )
        formula.set_color_by_tex("a", a_color)
        formula.set_color_by_tex("b", b_color)
        formula.set_color_by_tex("c", c_color)
        formula.move_to(UP * 2)
        middle_group.add(formula)
        self.play(Write(formula), run_time=0.8)
        self.wait(2)

        substituted = MathTex(
            "x",
            "=",
            "{-(",
            "-7",
            ")\\pm\\sqrt{(",
            "-7",
            ")^2-4\\cdot",
            "2",
            "\\cdot",
            "3",
            "}",
            r"\over",
            "2",
            "\\cdot",
            "2",
            "}",
        )
        for part in substituted.get_parts_by_tex("-7", substring=False):
            part.set_color(b_color)
        for part in substituted.get_parts_by_tex("2", substring=False):
            part.set_color(a_color)
        for part in substituted.get_parts_by_tex("3", substring=False):
            part.set_color(c_color)
        substituted.next_to(formula, DOWN, buff=0.8)
        middle_group.add(substituted)
        self.play(TransformFromCopy(formula, substituted), run_time=0.8)
        self.wait(1)

        simplified_b = MathTex(
            "x",
            "=",
            "{",
            "7",
            "\\pm\\sqrt{(",
            "-7",
            ")^2-4\\cdot",
            "2",
            "\\cdot",
            "3",
            "}",
            r"\over",
            "2",
            "\\cdot",
            "2",
            "}",
        )
        for part in simplified_b.get_parts_by_tex("7", substring=False):
            part.set_color(b_color)
        for part in simplified_b.get_parts_by_tex("-7", substring=False):
            part.set_color(b_color)
        for part in simplified_b.get_parts_by_tex("2", substring=False):
            part.set_color(a_color)
        for part in simplified_b.get_parts_by_tex("3", substring=False):
            part.set_color(c_color)
        simplified_b.move_to(substituted)
        middle_group.add(simplified_b)
        self.play(ReplacementTransform(substituted, simplified_b), run_time=0.8)
        self.wait(1)

        final_setup = MathTex("x", "=", "{7\\pm\\sqrt{(-7)^2-4\\cdot2\\cdot3}", r"\over", "2\\cdot2", "}")
        final_setup.to_edge(DOWN)
        final_setup.set_color(GREEN)
        bottom_group.add(final_setup)
        self.play(TransformFromCopy(simplified_b, final_setup), run_time=0.8)
        self.wait()

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)


class Scene2(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()

        title = Text("Compute the Discriminant")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title), run_time=2)
        self.wait(1.5)

        discriminant = MathTex("D", "=", "b^2", "-", "4ac")
        discriminant.move_to(UP * 2)
        middle_group.add(discriminant)
        self.play(Write(discriminant), run_time=0.8)
        self.wait(2)

        substituted_d = MathTex("D", "=", "(-7)^2", "-", "4\\cdot2\\cdot3")
        substituted_d.move_to(discriminant)
        middle_group.add(substituted_d)
        self.play(ReplacementTransform(discriminant, substituted_d), run_time=0.8)
        middle_group = VGroup(substituted_d)
        self.wait(1)

        evaluated_parts = MathTex("D", "=", "49", "-", "24")
        evaluated_parts.move_to(substituted_d)
        middle_group.add(evaluated_parts)
        self.play(ReplacementTransform(substituted_d, evaluated_parts), run_time=0.8)
        middle_group = VGroup(evaluated_parts)
        self.wait(1)

        discriminant_value = MathTex("D", "=", "25")
        discriminant_value.move_to(evaluated_parts)
        middle_group.add(discriminant_value)
        self.play(ReplacementTransform(evaluated_parts, discriminant_value), run_time=0.8)
        middle_group = VGroup(discriminant_value)
        self.wait(1)

        sqrt_value = MathTex("\\sqrt{25}", "=", "5")
        sqrt_value.next_to(discriminant_value, DOWN, buff=0.7)
        middle_group.add(sqrt_value)
        self.play(Write(sqrt_value), run_time=0.8)
        self.wait(2)

        real_rational = MathTex("D", ">", "0", ",", "\\sqrt{D}", "=", "5")
        real_rational.next_to(sqrt_value, DOWN, buff=0.7)
        middle_group.add(real_rational)
        self.play(Write(real_rational), run_time=0.8)
        self.wait(2)

        final_discriminant = MathTex("D", "=", "25")
        final_discriminant.to_edge(DOWN)
        final_discriminant.set_color(GREEN)
        bottom_group.add(final_discriminant)
        self.play(TransformFromCopy(discriminant_value, final_discriminant), run_time=0.8)
        self.wait()

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)


class Scene3(Scene):
    def construct(self):
        title_group = VGroup()
        middle_group = VGroup()
        bottom_group = VGroup()

        title = Text("Use the Plus-Minus for Both Solutions")
        title.to_edge(UP)
        title_group.add(title)
        self.play(Write(title), run_time=2)
        self.wait(1.5)

        simplified_formula = MathTex("x", "=", "\\frac{7\\pm5}{4}")
        simplified_formula.move_to(UP * 2)
        middle_group.add(simplified_formula)
        self.play(Write(simplified_formula), run_time=0.8)
        self.wait(2)

        plus_case = MathTex("x", "=", "\\frac{7+5}{4}", "=", "\\frac{12}{4}", "=", "3")
        plus_case.next_to(simplified_formula, DOWN, buff=0.8)
        middle_group.add(plus_case)
        self.play(TransformFromCopy(simplified_formula, plus_case), run_time=0.8)
        self.wait(1)

        minus_case = MathTex("x", "=", "\\frac{7-5}{4}", "=", "\\frac{2}{4}", "=", "\\frac{1}{2}")
        minus_case.next_to(plus_case, DOWN, buff=0.8)
        middle_group.add(minus_case)
        self.play(TransformFromCopy(simplified_formula, minus_case), run_time=0.8)
        self.wait(1)

        solution_set = MathTex("x", "\\in", "\\left\\{3,\\frac{1}{2}\\right\\}")
        solution_set.next_to(minus_case, DOWN, buff=0.7)
        middle_group.add(solution_set)
        self.play(TransformFromCopy(VGroup(plus_case, minus_case), solution_set), run_time=0.8)
        self.wait(1)

        final_solutions = MathTex("x", "\\in", "\\left\\{3,\\frac{1}{2}\\right\\}")
        final_solutions.to_edge(DOWN)
        final_solutions.set_color(GREEN)
        bottom_group.add(final_solutions)
        self.play(ReplacementTransform(solution_set, final_solutions), run_time=0.8)
        middle_group = VGroup(simplified_formula, plus_case, minus_case)
        self.wait()

        self.play(FadeOut(title_group), FadeOut(middle_group), FadeOut(bottom_group), run_time=0.8)
        self.wait(1)
