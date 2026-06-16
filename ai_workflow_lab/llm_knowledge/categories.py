"""
Standalone category enums for Manim knowledge documents.

This module has NO app-level imports so it can be safely imported from
both llm_settings.py and skill_documents.py without creating circular
import chains.
"""
from enum import Enum


class RuleCategory(str, Enum):
    LAYOUT_SAFETY = "layout-safety"   # frame safety, labels, arrows, overlap
    GEOMETRY = "geometry"             # shapes, geometry labels, matrices
    VISUAL_LAYOUT = "visual-layout"   # composition, grouping, positioning
    GENERAL = "general"               # animation, styling, axes, text, camera


class ExampleCategory(str, Enum):
    MATHEMATICAL_PROOF = "mathematical-proof"   # Pythagorean, derivatives, theorems
    VISUALIZATION = "visualization"             # function graphs, transformations
    CONSTRUCTION = "construction"               # geometric constructions


class TemplateCategory(str, Enum):
    TEMPLATES = "templates"


class SkillCategory(str, Enum):
    CORE = "core"


DocumentCategory = RuleCategory | ExampleCategory | TemplateCategory | SkillCategory
