from manim import *


class EquationTemplate(VisualTemplate):
    VALID_STATES = frozenset({"display"})

    def __init__(self, state: str, expression: str):
        self.expression = expression
        self.equation = MathTex(expression)
        super().__init__(self.equation, state=state)

    def set_expression(self, expression: str) -> Animation:
        self.expression = expression
        replacement = MathTex(expression).match_height(self.equation).move_to(self.equation)
        return Transform(self.equation, replacement)
