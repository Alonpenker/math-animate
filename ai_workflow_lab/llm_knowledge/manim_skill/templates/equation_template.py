from manim import *


class EquationTemplate(VisualTemplate):
    VALID_STATES = frozenset({"display", "derivation", "statements"})
    MAX_STEPS = 3
    MUTED_OPACITY = 0.55

    def __init__(
        self,
        state: str,
        expression: str | None = None,
        expressions: list[str] | tuple[str, ...] | None = None,
    ):
        state = self._validate_state(state)
        self.expression = None
        self.expressions = []

        if state == "display":
            if not isinstance(expression, str) or not expression:
                raise ValueError("display state requires a non-empty expression")
            if expressions is not None:
                raise ValueError("display state does not accept expressions")
            self.expression = expression
            self.equation = MathTex(expression)
            super().__init__(self.equation, state=state)
            return

        if expression is not None:
            raise ValueError("derivation and statements states do not accept expression")
        if not isinstance(expressions, (list, tuple)) or not 1 <= len(expressions) <= self.MAX_STEPS:
            raise ValueError("derivation and statements states require one to three expressions")
        if not all(isinstance(value, str) and value for value in expressions):
            raise ValueError("expressions must be non-empty strings")

        self.expressions = list(expressions)
        self.active_steps = [
            self._step_slot(
                expression,
                newest=state == "statements" or index == len(self.expressions) - 1,
            )
            for index, expression in enumerate(self.expressions)
        ]
        self.step_slots = VGroup(*self.active_steps).arrange(DOWN, buff=0.45)
        super().__init__(self.step_slots, state=state)

    def set_expression(self, expression: str) -> Animation:
        if self.state != "display":
            raise ValueError("set_expression is only available in display state")
        if not isinstance(expression, str) or not expression:
            raise ValueError("expression must be a non-empty string")
        self.expression = expression
        replacement = MathTex(expression).match_height(self.equation).move_to(self.equation)
        return Transform(self.equation, replacement)

    def advance_step(self, expression: str) -> Animation:
        if self.state != "derivation":
            raise ValueError("advance_step is only available in derivation state")
        if not isinstance(expression, str) or not expression:
            raise ValueError("expression must be a non-empty string")

        center = VGroup(*self.active_steps).get_center()
        new_step = self._step_slot(expression, newest=True)

        if len(self.active_steps) < self.MAX_STEPS:
            targets = VGroup(*[
                step.copy() for step in [*self.active_steps, new_step]
            ]).arrange(DOWN, buff=0.45).move_to(center)
            new_step.move_to(targets[-1])
            self.step_slots.add(new_step)
            self.active_steps.append(new_step)
            self.expressions.append(expression)
            return AnimationGroup(
                *[
                    step.animate.move_to(target).set_opacity(self.MUTED_OPACITY)
                    for step, target in zip(self.active_steps[:-1], targets[:-1])
                ],
                FadeIn(new_step),
                lag_ratio=0.08,
            )

        oldest, middle, newest = self.active_steps
        targets = VGroup(middle.copy(), newest.copy(), new_step.copy()).arrange(
            DOWN,
            buff=0.45,
        ).move_to(center)
        new_step.move_to(targets[-1])
        self.step_slots.add(new_step)
        self.active_steps = [middle, newest, new_step]
        self.expressions = [self.expressions[1], self.expressions[2], expression]
        return AnimationGroup(
            FadeOut(oldest, shift=UP * 0.5),
            middle.animate.move_to(targets[0]).set_opacity(self.MUTED_OPACITY),
            newest.animate.move_to(targets[1]).set_opacity(self.MUTED_OPACITY),
            FadeIn(new_step),
            lag_ratio=0.08,
        )

    def highlight_formula(self, index: int | None = None) -> Animation:
        if self.state == "display":
            if index is not None:
                raise ValueError("display state highlight does not accept an index")
            target = self.equation
        else:
            target_index = len(self.expressions) - 1 if index is None else index
            if not isinstance(target_index, int) or not 0 <= target_index < len(self.expressions):
                raise ValueError("highlight index must reference a visible derivation step")
            target = self.active_steps[target_index]
        return Circumscribe(target, color=YELLOW, buff=0.14, fade_out=True)

    def _step_slot(self, expression: str, *, newest: bool) -> VGroup:
        equation = MathTex(expression)
        if not newest:
            equation.set_opacity(self.MUTED_OPACITY)
        return VGroup(equation)
