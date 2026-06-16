"""
Template playground — rewrite this file to test a template.
See README.md for the LLM prompt and render command.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "llm_knowledge", "manim_skill"))

from visual_kit import SafeScene, Layout
# from templates.equation_template import EquationTemplate   ← swap template here


class PlayScene(SafeScene):
    def construct(self):
        # --- LLM: fill this in ---
        pass
