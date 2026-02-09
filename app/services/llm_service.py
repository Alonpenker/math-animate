

from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan

CODEGEN_EXAMPLE = """from manim import *

class Scene1(Scene):
    def construct(self):
        example_text = Tex(
            "This is a some text",
            tex_to_color_map={"text": YELLOW},
        )
        example_tex = MathTex(
            "\\\\sum_{k=1}^\\\\infty {1 \\\\over k^2} = {\\\\pi^2 \\\\over 6}",
        )
        group = VGroup(example_text, example_tex)
        group.arrange(DOWN)
        group.width = config["frame_width"] - 2 * LARGE_BUFF

        self.play(Write(example_text))
        self.play(Write(example_tex))
        self.wait()

class Scene2(Scene):
    def construct(self):
        circle = Circle()
        square = Square()
        square.flip(RIGHT)
        square.rotate(-3 * TAU / 8)
        circle.set_fill(PINK, opacity=0.5)

        self.play(Create(square))
        self.play(Transform(square, circle))
        self.play(FadeOut(square))
"""
PLAN_EXAMPLE = """{
  "scenes": [
    {
      "learning_objective": "Understand what a variable represents in a linear equation.",
      "visual_storyboard": "Show a simple linear equation on a whiteboard and highlight the variable.",
      "voice_notes": "Explain that a variable stands for an unknown number in the equation.",
      "scene_number": 1
    },
    {
      "learning_objective": "Solve a one-step linear equation by isolating the variable.",
      "visual_storyboard": "Animate subtracting the same number from both sides of the equation.",
      "voice_notes": "Walk through the steps to isolate the variable and find its value.",
      "scene_number": 2
    }
  ]
}"""

class LLMService:
    
    @staticmethod
    def plan_call(user_request: UserRequest) -> VideoPlan:
        return VideoPlan.model_validate_json(PLAN_EXAMPLE)
    
    @staticmethod
    def codegen_call(plan: VideoPlan) -> str:
        return CODEGEN_EXAMPLE
