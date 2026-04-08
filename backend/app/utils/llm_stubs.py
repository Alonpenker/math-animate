import os

from app.schemas.scene_plan import ScenePlan
from app.schemas.video_plan import VideoPlan

IS_E2E_MODE: bool = os.environ.get("E2E", "").lower() == "true"

STUB_PLAN = VideoPlan(
    scenes=[
        ScenePlan(
            scene_number=1,
            learning_objective="Understand that the area of a circle is calculated using A = pi * r^2",
            visual_storyboard=(
                "Show a circle with a labeled radius r. "
                "Animate the formula A = pi * r^2 appearing beside the circle. "
                "Highlight the radius and shade the interior to represent the area."
            ),
            voice_notes=(
                "Today we will learn how to find the area of a circle. "
                "The formula is A equals pi times the radius squared. "
                "Watch as we shade the area inside the circle."
            ),
        ),
        ScenePlan(
            scene_number=2,
            learning_objective="Apply the area formula to a circle with radius 5",
            visual_storyboard=(
                "Show a circle with radius labeled as 5. "
                "Step through the substitution: A = pi * 5^2 = 25 * pi. "
                "Display the approximate numeric result 78.54 square units."
            ),
            voice_notes=(
                "Now let us plug in a radius of 5. "
                "A equals pi times 5 squared, which is 25 pi, or about 78.54 square units."
            ),
        ),
    ]
)

STUB_BROKEN_CODE: str = """\
import nonexistent_module_xyz
from manim import *

class Scene1(Scene):
    def construct(self):
        circle = Circle(radius=2, color=BLUE)
        self.play(Create(circle))
        self.wait(1)
"""

STUB_FIXED_CODE: str = """\
from manim import *

class Scene1(Scene):
    def construct(self):
        circle = Circle(radius=2, color=BLUE)
        label = MathTex("A = \\\\pi r^2").next_to(circle, RIGHT)
        self.play(Create(circle), Write(label))
        self.wait(1)

class Scene2(Scene):
    def construct(self):
        circle = Circle(radius=2, color=BLUE)
        formula = MathTex("A = \\\\pi \\\\cdot 5^2 = 25\\\\pi").to_edge(UP)
        self.play(Create(circle))
        self.play(Write(formula))
        self.wait(1)
"""
